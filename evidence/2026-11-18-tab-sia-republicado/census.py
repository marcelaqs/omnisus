"""List every member of a TAB_SIA.zip and compare it with what the repository recorded.

    uv run --locked python evidence/2026-11-18-tab-sia-republicado/census.py ZIP > members.csv

One CSV row per member: path, size, SHA-256, the date stored in the zip, and the SHA-256
``vinculos.json`` holds for it (the packaged members of ``sia-tab-e5812b51d802``), empty
when it holds none. The summary goes to stderr.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VINCULOS = ROOT / "src/omnisus/data/dicionarios/sources/cnv/vinculos.json"
SOURCE = "sia-tab-e5812b51d802"


def recorded() -> dict[str, str]:
    """``{member path: SHA-256}`` of the members ``vinculos.json`` holds from ``SOURCE``."""
    membros = json.loads(VINCULOS.read_text(encoding="utf-8"))["membros"].values()
    return {entry["membro"]: entry["sha256"] for entry in membros if entry["fonte"] == SOURCE}


def main(zip_path: Path) -> None:
    known = recorded()
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(
        ["member", "bytes", "sha256", "zip_date", "recorded_source", "recorded_sha256"]
    )
    compared = equal = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in sorted(zf.infolist(), key=lambda i: i.filename):
            if info.is_dir():
                continue
            digest = hashlib.sha256(zf.read(info)).hexdigest()
            date = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*info.date_time)
            sha = known.pop(info.filename, "")
            writer.writerow(
                [info.filename, info.file_size, digest, date, SOURCE if sha else "", sha]
            )
            if sha:
                compared += 1
                equal += sha == digest
    print(f"{compared} recorded members compared, {equal} equal", file=sys.stderr)
    print(f"{len(known)} recorded members absent from the zip: {sorted(known)}", file=sys.stderr)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
