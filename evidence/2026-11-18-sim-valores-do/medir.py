"""Values of the coded fields of `sim_obitos` in DO files downloaded from the server.

    uv run --locked python evidence/2026-11-18-sim-valores-do/medir.py DOWNLOAD_DIR

`DOWNLOAD_DIR` holds `DO<UF><year>.dbc` files of `SIM/CID10/DORES`. The script writes,
next to itself, `arquivos.csv` (file, SHA-256, bytes, records, columns) and `valores.csv`:
for each year and each field of `sim_obitos` that has a code map, how many records hold
each value; for the fields in `SHAPES`, how many hold each shape (`9` for a digit, `A`
for a letter, the character itself otherwise).
"""

from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path

from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario

SHAPES = ("horaobito", "codestab", "ocup", "ocupmae", "natural", "versaosist", "causamat")
HERE = Path(__file__).parent


def _shape(value: str) -> str:
    return "".join("9" if c.isdigit() else "A" if c.isalpha() else c for c in value)


def main() -> int:
    coded = [f["name"] for f in load_dicionario("sim_obitos").fields if f.get("x-decode")]
    files, counts = [], Counter()
    for path in sorted(Path(sys.argv[1]).glob("*.[dD][bB][cC]"), key=lambda p: p.name.upper()):
        data = path.read_bytes()
        frame = dbc_bytes_to_lazyframe(data, dataset="sim_obitos").collect()
        year = path.name[4:8]
        files.append(
            [path.name, hashlib.sha256(data).hexdigest(), len(data), frame.height, frame.width]
        )
        for field in coded:
            if field in frame.columns:
                for value, n in Counter(frame[field].cast(str).fill_null("").to_list()).items():
                    counts[year, field, "value", value] += n
        for field in SHAPES:
            if field in frame.columns:
                for value, n in Counter(frame[field].cast(str).fill_null("").to_list()).items():
                    counts[year, field, "shape", _shape(value)] += n
    for name, header, rows in (
        ("arquivos.csv", ["file", "sha256", "bytes", "records", "columns"], files),
        (
            "valores.csv",
            ["year", "field", "kind", "value", "records"],
            [[*key, n] for key, n in sorted(counts.items())],
        ),
    ):
        with (HERE / name).open("w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
    print(f"{len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
