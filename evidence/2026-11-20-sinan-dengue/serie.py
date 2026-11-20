"""Read every DENGBR file of a local folder: hash, layout, staging and identity.

    uv run python evidence/2026-11-20-sinan-dengue/serie.py <folder with DENGBR00..26.dbc>

Writes `serie.json` (one entry per file) and `leiautes.json` (the field descriptors of
each distinct DBF header) beside this script. Each file is staged with
`dbc_bytes_to_parquet` under the `sinan_dengue` dictionary and checked with
`validate_identity`, the two steps an import runs; the Parquet is deleted afterwards.
Both files are rewritten after each DBC, and a file already in `serie.json` with the
same SHA-256 is not read again, so a run that stops can be resumed.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.dbc import decompress_bytes
from omnisus.sources.datasus_ftp.identity import validate_identity
from omnisus.sources.datasus_ftp.inventory import _blocking_list
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from omnisus.transforms.dictionaries import load_dicionario

HERE = Path(__file__).resolve().parent
DIRS = {
    "final": "/dissemin/publicos/SINAN/DADOS/FINAIS",
    "prelim": "/dissemin/publicos/SINAN/DADOS/PRELIM",
}


def descriptors(dbf: bytes) -> list[list]:
    fields, offset = [], 32
    while dbf[offset] != 0x0D:
        raw = dbf[offset : offset + 32]
        fields.append([raw[:11].split(b"\0")[0].decode("latin-1"), chr(raw[11]), raw[16], raw[17]])
        offset += 32
    return fields


def counts(frame: pl.LazyFrame, column: str) -> dict[str, int]:
    rows = frame.group_by(pl.col(column).cast(pl.String).alias("v")).len().collect().rows()
    return dict(sorted((value or "", n) for value, n in rows))


def main() -> None:
    folder = Path(sys.argv[1])
    listed = {}
    for release, path in DIRS.items():
        for line in _blocking_list(path, 120.0):
            parts = line.split()
            if parts[-1].upper().startswith("DENGBR"):
                listed[parts[-1]] = (release, int(parts[2]), f"{parts[0]} {parts[1]}")
    dicionario = load_dicionario("sinan_dengue")
    serie_path, layouts_path = HERE / "serie.json", HERE / "leiautes.json"
    serie = json.loads(serie_path.read_text("utf-8")) if serie_path.exists() else []
    layouts = json.loads(layouts_path.read_text("utf-8")) if layouts_path.exists() else []
    done = {entry["file"]: entry["sha256"] for entry in serie}
    for name in sorted(listed):
        release, size, modified = listed[name]
        raw = (folder / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if done.get(name) == digest:
            continue
        year = 2000 + int(name[6:8])
        dbf = decompress_bytes(raw)
        fields = descriptors(dbf)
        records = struct.unpack("<I", dbf[4:8])[0]
        del dbf
        layout = next((item for item in layouts if item["fields"] == fields), None)
        if layout is None:
            layout = {"layout": len(layouts) + 1, "files": [], "fields": fields}
            layouts.append(layout)
        layout["files"].append(name)
        entry = {
            "file": name,
            "url": f"ftp://ftp.datasus.gov.br{DIRS[release]}/{name}",
            "release": release,
            "listed_bytes": size,
            "listed_modified": modified,
            "bytes": len(raw),
            "sha256": digest,
            "records": records,
            "fields": len(fields),
            "layout": layout["layout"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "staged.parquet"
            result = dbc_bytes_to_parquet(
                raw, out, dataset="sinan_dengue", source_ano=year, release=release
            )
            del raw
            schema = pq.read_schema(out)
            try:
                validate_identity(out, dicionario, ScopeKey(uf=None, ano=year))
                identity = "ok"
            except ValueError as exc:
                identity = str(exc)
            frame = pl.scan_parquet(out)
            entry |= {
                "staged_rows": result.rows,
                "identity": identity,
                "nu_ano": counts(frame, "nu_ano"),
                "id_agravo": counts(frame, "id_agravo") if "id_agravo" in schema.names else None,
                "staged_types": {
                    column: str(schema.field(column).type)
                    for column in ("nu_idade_n", "plaq_menor", "flxrecebi", "classi_fin")
                    if column in schema.names
                },
            }
        serie.append(entry)
        serie_path.write_text(json.dumps(serie, indent=1) + "\n", encoding="utf-8")
        layouts_path.write_text(json.dumps(layouts, indent=1) + "\n", encoding="utf-8")
        print(name, entry["records"], entry["fields"], identity, flush=True)


if __name__ == "__main__":
    main()
