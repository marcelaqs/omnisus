"""Rows in which each field of a `.dbc` is filled, and rows in which it is blank.

A field is filled when its text is neither blank nor zero (`0`, `0.00`, `0000`), and
blank when it is only spaces; the rest of the rows have a zero. Only counts leave the
files.

    python medir_preenchimento.py rdac0909.csv FILE.dbc [FILE.dbc ...]
"""

from __future__ import annotations

import csv
import hashlib
import struct
import sys
from pathlib import Path

from omnisus.sources.datasus_ftp import dbc

rows: list[list[object]] = [
    ["file", "size_bytes", "sha256", "records", "field", "descriptor", "filled", "blank"]
]
for path in map(Path, sys.argv[2:]):
    raw = path.read_bytes()
    dbf = dbc.decompress_bytes(raw)
    records, header_size, record_size = struct.unpack("<IHH", dbf[4:12])
    start = 1
    for at in range(32, header_size - 32, 32):
        if dbf[at] == 0x0D:
            break
        name, kind = dbf[at : at + 11].split(b"\x00")[0].decode("ascii"), chr(dbf[at + 11])
        width, decimals = dbf[at + 16], dbf[at + 17]
        values = [dbf[header_size + n * record_size + start :][:width] for n in range(records)]
        filled = sum(bool(value.strip(b" 0.")) for value in values)
        blank = sum(not value.strip() for value in values)
        rows.append(
            [
                path.name,
                len(raw),
                hashlib.sha256(raw).hexdigest(),
                records,
                name,
                f"{kind}{width}.{decimals}",
                filled,
                blank,
            ]
        )
        start += width
with Path(sys.argv[1]).open("w", encoding="utf-8", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
