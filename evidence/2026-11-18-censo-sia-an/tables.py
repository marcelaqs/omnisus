"""Writes files.csv, values.csv and dates.csv from the JSON lines census.py wrote.

values.csv keeps the ten fields the dictionary cites; census.py also counted an_tru and
an_intfis.

python tables.py census.jsonl <output directory>
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

rows = sorted(
    (json.loads(line) for line in Path(sys.argv[1]).read_text("utf-8").splitlines()),
    key=lambda row: row["file"],
)
out = Path(sys.argv[2])
assert not [row for row in rows if "error" in row]
FIELDS = [
    "ap_ufdif",
    "ap_mndif",
    "ap_natjur",
    "ap_coidade",
    "ap_tippre",
    "ap_ufnacio",
    "an_albumi",
    "an_hb",
    "ap_mvm",
    "ap_cmp",
]

with (out / "files.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(
        ["file", "bytes", "sha256", "listed", "fields", "header_sha256", "ap_natjur", "records"]
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
                int(row["has_ap_natjur"]),
                row["records"],
            ]
        )

records: dict[tuple[str, str], int] = Counter()
in_files: dict[tuple[str, str], int] = Counter()
for row in rows:
    for field in FIELDS:
        counts = row["counts"].get(field, {})
        for value, count in counts.items():
            records[field, value] += count
            in_files[field, value] += 1
with (out / "values.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["field", "value", "records", "files"])
    for field, value in sorted(records):
        writer.writerow([field, value, records[field, value], in_files[field, value]])

dates: dict[str, dict] = defaultdict(
    lambda: {"filled": 0, "yyyymmdd": 0, "min": None, "max": None, "outside": 0, "after": 0}
)
for row in rows:
    for field, seen in row["dates"].items():
        total = dates[field]
        total["filled"] += seen["filled"]
        total["yyyymmdd"] += seen["yyyymmdd"]
        total["outside"] += bool(seen["yyyymmdd_outside_1900_2100"])
        total["after"] += bool(seen["after_2015"])
        if seen["min"]:
            total["min"] = min(filter(None, [total["min"], seen["min"]]))
            total["max"] = max(filter(None, [total["max"], seen["max"]]))
with (out / "dates.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(
        [
            "field",
            "filled",
            "yyyymmdd",
            "not_yyyymmdd",
            "min",
            "max",
            "files_with_year_outside_1900_2100",
            "files_with_year_after_2015",
        ]
    )
    for field, total in dates.items():
        writer.writerow(
            [
                field,
                total["filled"],
                total["yyyymmdd"],
                total["filled"] - total["yyyymmdd"],
                total["min"],
                total["max"],
                total["outside"],
                total["after"],
            ]
        )
