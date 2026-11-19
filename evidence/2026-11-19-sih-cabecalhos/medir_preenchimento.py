"""Rows in which each field of a `.dbc` is filled. Only counts leave the files.

A field is filled when its text is neither blank nor zero (`0`, `0.00`, `0000`).

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
    ["file", "size_bytes", "sha256", "records", "field", "descriptor", "filled"]
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
        filled = sum(
            bool(dbf[header_size + n * record_size + start :][:width].strip(b" 0."))
            for n in range(records)
        )
        rows.append(
            [
                path.name,
                len(raw),
                hashlib.sha256(raw).hexdigest(),
                records,
                name,
                f"{kind}{width}.{decimals}",
                filled,
            ]
        )
        start += width
with Path(sys.argv[1]).open("w", encoding="utf-8", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
