"""Rows per value of the UTI day counters and of REGCT in RD files. Only counts leave the files.

Usage: uv run --locked python medir.py DIR OUT
DIR holds RD*.dbc files of SIHSUS/200801_/Dados/; OUT is the JSON written.

The values are the bytes of the DBF record, decoded as latin-1: REGCT as published, the
numeric fields without the padding spaces. A field a file's header lacks is listed in
`absent` and gets no counts. The REGCT decode map is read from the packaged dictionary
`sih_aih_reduzida.yaml`.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path

import yaml

import omnisus
from omnisus.sources.datasus_ftp import dbc

NUMERIC = ("UTI_MES_IN", "UTI_MES_AN", "UTI_MES_AL", "UTI_MES_TO", "UTI_INT_TO")
DICTIONARY = Path(omnisus.__file__).parent / "data" / "dicionarios" / "sih_aih_reduzida.yaml"


def regct_decode() -> dict[str, str]:
    fields = yaml.safe_load(DICTIONARY.read_text(encoding="utf-8"))["schema"]["fields"]
    return next(f["x-decode"] for f in fields if f["name"] == "regct")


def columns(dbf: bytes) -> tuple[int, int, int, dict[str, tuple[str, int, int]]]:
    """Records, header size, record size and, per field, DBF type, width and offset."""
    records, header_size, record_size = struct.unpack("<IHH", dbf[4:12])
    layout: dict[str, tuple[str, int, int]] = {}
    start = 1
    for at in range(32, header_size - 32, 32):
        name = dbf[at : at + 11].split(b"\x00")[0].decode("ascii")
        width = dbf[at + 16]
        layout[name] = (chr(dbf[at + 11]), width, start)
        start += width
    return records, header_size, record_size, layout


def value_counts(dbf: bytes, records: int, header: int, record: int, start: int, width: int):
    stop = header + records * record
    return Counter(dbf[at : at + width] for at in range(header + start, stop, record))


def numeric(counted: Counter[bytes], kind: str, width: int) -> dict[str, object]:
    values = {raw.decode("latin-1").strip(): rows for raw, rows in counted.items()}
    numbers = {int(text): rows for text, rows in values.items() if text.isdigit()}
    return {
        "dbf_type": f"{kind}{width}",
        "max": max(numbers) if numbers else None,
        "not_a_number": {t: r for t, r in sorted(values.items()) if not t.isdigit()},
        "rows_above_0": sum(r for v, r in numbers.items() if v > 0),
        "rows_above_31": sum(r for v, r in numbers.items() if v > 31),
        "rows_equal_999": numbers.get(999, 0),
        "values_100_or_more": {str(v): r for v, r in sorted(numbers.items()) if v >= 100},
    }


def measure(raw: bytes, decode: dict[str, str]) -> dict[str, object]:
    dbf = dbc.decompress_bytes(raw)
    records, header, record, layout = columns(dbf)
    out: dict[str, object] = {
        "absent": [name for name in (*NUMERIC, "REGCT") if name not in layout],
        "bytes": len(raw),
        "rows": records,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    for name in NUMERIC:
        if name in layout:
            kind, width, start = layout[name]
            counted = value_counts(dbf, records, header, record, start, width)
            out[name.lower()] = numeric(counted, kind, width)
    if "REGCT" in layout:
        kind, width, start = layout["REGCT"]
        counted = value_counts(dbf, records, header, record, start, width)
        values = {raw.decode("latin-1"): rows for raw, rows in sorted(counted.items())}
        out["regct"] = {
            "dbf_type": f"{kind}{width}",
            "rows_equal_7118": values.get("7118", 0),
            "values": values,
            "values_not_in_decode": {v: r for v, r in values.items() if v not in decode},
        }
    return out


def add(total: dict[str, int], part: dict[str, int]) -> None:
    for key, rows in part.items():
        total[key] = total.get(key, 0) + rows


def by_competence(files: dict[str, dict]) -> dict[str, dict]:
    """The same counts summed over the files of each competence (the YYMM of the name)."""
    out: dict[str, dict] = {}
    for name, entry in files.items():
        month = out.setdefault(
            f"20{name[4:6]}-{name[6:8]}",
            {
                "files": 0,
                "regct": {},
                "regct_not_in_decode": {},
                "rows": 0,
                "uti_mes_to_100_or_more": {},
                "uti_mes_to_max": None,
                "uti_mes_to_rows_above_31": 0,
                "uti_mes_to_rows_equal_999": 0,
            },
        )
        month["files"] += 1
        month["rows"] += entry["rows"]
        if "regct" in entry:
            add(month["regct"], entry["regct"]["values"])
            add(month["regct_not_in_decode"], entry["regct"]["values_not_in_decode"])
        if "uti_mes_to" in entry:
            days = entry["uti_mes_to"]
            add(month["uti_mes_to_100_or_more"], days["values_100_or_more"])
            month["uti_mes_to_rows_above_31"] += days["rows_above_31"]
            month["uti_mes_to_rows_equal_999"] += days["rows_equal_999"]
            if days["max"] is not None:
                month["uti_mes_to_max"] = max(month["uti_mes_to_max"] or 0, days["max"])
    return out


def main() -> None:
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    decode = regct_decode()
    files = {p.name: measure(p.read_bytes(), decode) for p in sorted(folder.glob("RD*.dbc"))}
    result = {
        "competences": by_competence(files),
        "files": files,
        "regct_decode": {
            "codes": sorted(decode),
            "dictionary_sha256": hashlib.sha256(DICTIONARY.read_bytes()).hexdigest(),
        },
    }
    text = json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True)
    out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
