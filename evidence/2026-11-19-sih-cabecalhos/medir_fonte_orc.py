"""Rows per value of FONTE_ORC in each `.dbc` of a directory. Only counts leave the files.

python medir_fonte_orc.py DIR rj_fonte_orc.csv
"""

from __future__ import annotations

import csv
import hashlib
import struct
import sys
from collections import Counter
from pathlib import Path

from omnisus.sources.datasus_ftp import dbc

rows: list[list[object]] = [["file", "size_bytes", "sha256", "records", "fonte_orc", "rows"]]
for path in sorted(Path(sys.argv[1]).glob("*.dbc")):
    raw = path.read_bytes()
    dbf = dbc.decompress_bytes(raw)
    records, header_size, record_size = struct.unpack("<IHH", dbf[4:12])
    start, width = 1, 0
    for at in range(32, header_size - 32, 32):
        name, width = dbf[at : at + 11].split(b"\x00")[0], dbf[at + 16]
        if name == b"FONTE_ORC":
            break
        start += width
    else:
        raise SystemExit(f"{path.name} has no FONTE_ORC")
    values = Counter(
        dbf[header_size + n * record_size + start :][:width].decode("latin-1")
        for n in range(records)
    )
    digest = hashlib.sha256(raw).hexdigest()
    rows += [
        [path.name, len(raw), digest, records, value, n] for value, n in sorted(values.items())
    ]
with Path(sys.argv[2]).open("w", encoding="utf-8", newline="") as f:
    csv.writer(f, lineterminator="\n").writerows(rows)
