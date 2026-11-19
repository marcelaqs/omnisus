"""Writes files.csv and values.csv from the JSON lines census.py wrote.

python tables.py census.jsonl <output directory>
"""

import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

rows = sorted(
    (json.loads(line) for line in Path(sys.argv[1]).read_text("utf-8").splitlines()),
    key=lambda row: row["file"],
)
out = Path(sys.argv[2])
assert not [row for row in rows if "error" in row]


def prefix(name: str) -> str:
    return re.match(r"A[A-Z]{1,2}?(?=[A-Z]{2}\d{4})", name).group(0)


with (out / "files.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(
        [
            "file",
            "bytes",
            "sha256",
            "listed",
            "fields",
            "header_sha256",
            "natjur_names",
            "position",
            "width",
            "records",
        ]
    )
    for row in rows:
        listed = datetime.strptime(" ".join(row["listed"].split()), "%m-%d-%y %I:%M%p")
        writer.writerow(
            [
                row["file"],
                row["bytes"],
                row["sha256"],
                listed.strftime("%Y-%m-%dT%H:%M"),
                row["fields"],
                row["header_sha256"],
                " ".join(row["natjur_names"]),
                row["position"] or "",
                row.get("width", ""),
                row["records"],
            ]
        )

records: dict[tuple[str, str], int] = Counter()
in_files: dict[tuple[str, str], int] = Counter()
for row in rows:
    for value, count in (row.get("values") or {}).items():
        records[prefix(row["file"]), value] += count
        in_files[prefix(row["file"]), value] += 1
with (out / "values.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["prefix", "value", "records", "files"])
    for key in sorted(records):
        writer.writerow([*key, records[key], in_files[key]])
