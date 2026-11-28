"""Rows with ESPEC 17 in RD and RJ files, and what those rows hold. Only counts leave the files.

Usage: uv run --locked python -I evidence/2026-11-28-sih-espec-17/medir.py DIR OUT
DIR holds RD*.dbc and RJ*.dbc files of SIHSUS/200801_/Dados/; OUT is the JSON written.

The values are the bytes of the DBF record, decoded as latin-1, as published. For each
file: the rows per value of ESPEC that `CNV/LEITOS.CNV` (the packaged member of TAB_SIH)
does not list and, among the rows with ESPEC 17, the rows per value of PROC_REA and of
MARCA_UTI and the number of distinct CNES. The distinct CNES are also counted over all
the RD files and over all the RJ files.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path

import omnisus
from omnisus.sources.datasus_ftp import dbc
from omnisus.transforms.cnv import cnv_map, parse_cnv

FIELDS = ("ESPEC", "PROC_REA", "MARCA_UTI", "CNES")
LEITOS = Path(omnisus.__file__).parent / "data/dicionarios/sources/cnv/sih/CNV/LEITOS.CNV"


def columns(dbf: bytes) -> tuple[int, int, int, dict[str, tuple[int, int]]]:
    """Records, header size, record size and, per field, offset and width."""
    records, header_size, record_size = struct.unpack("<IHH", dbf[4:12])
    layout: dict[str, tuple[int, int]] = {}
    start = 1
    for at in range(32, header_size - 32, 32):
        name = dbf[at : at + 11].split(b"\x00")[0].decode("ascii")
        width = dbf[at + 16]
        layout[name] = (start, width)
        start += width
    return records, header_size, record_size, layout


def measure(raw: bytes, listed: set[str]) -> tuple[dict[str, object], set[str]]:
    """The counts of one file and the CNES of its rows with ESPEC 17."""
    dbf = dbc.decompress_bytes(raw)
    records, header, record, layout = columns(dbf)
    espec: Counter[str] = Counter()
    proc_rea: Counter[str] = Counter()
    marca_uti: Counter[str] = Counter()
    cnes: set[str] = set()
    for at in range(header, header + records * record, record):
        row = {
            name: dbf[at + layout[name][0] : at + sum(layout[name])].decode("latin-1")
            for name in FIELDS
        }
        espec[row["ESPEC"]] += 1
        if row["ESPEC"] == "17":
            proc_rea[row["PROC_REA"]] += 1
            marca_uti[row["MARCA_UTI"]] += 1
            cnes.add(row["CNES"])
    counts = {
        "bytes": len(raw),
        "espec_17": {
            "cnes_distinct": len(cnes),
            "marca_uti": dict(sorted(marca_uti.items())),
            "proc_rea": dict(sorted(proc_rea.items())),
            "rows": espec.get("17", 0),
        },
        "espec_not_in_leitos_cnv": {v: r for v, r in sorted(espec.items()) if v not in listed},
        "rows": records,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    return counts, cnes


def main() -> None:
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    leitos = LEITOS.read_bytes()
    listed = set(cnv_map(parse_cnv(leitos.decode("latin-1"))))
    files: dict[str, dict[str, object]] = {}
    cnes: dict[str, set[str]] = {"RD": set(), "RJ": set()}
    for path in sorted([*folder.glob("RD*.dbc"), *folder.glob("RJ*.dbc")]):
        files[path.name], found = measure(path.read_bytes(), listed)
        cnes[path.name[:2]] |= found
    result = {
        "espec_17_cnes_distinct": {prefix: len(found) for prefix, found in cnes.items()},
        "files": files,
        "leitos_cnv": {"codes": sorted(listed), "sha256": hashlib.sha256(leitos).hexdigest()},
    }
    text = json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True)
    out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
