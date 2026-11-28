"""List every member of a TAB_SIA.zip and compare it with what the repository recorded.

    uv run --locked python evidence/2026-11-28-tab-sia-republicado/census.py ZIP > members.csv

One CSV row per member: path, size, SHA-256, the date stored in the zip, and the SHA-256
the repository holds for it, empty when it holds none. Two places hold one:
``evidence/2026-11-18-tab-sia-republicado/members.csv`` for every member of
``sia-tab-1ce232b217c6``, and ``vinculos.json`` for the packaged members of
``sia-tab-e5812b51d802``. A member held under both has two rows. The summary goes to stderr.
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
PREVIOUS = ROOT / "evidence/2026-11-18-tab-sia-republicado/members.csv"
PREVIOUS_ID = "sia-tab-1ce232b217c6"
PACKAGED_IDS = (PREVIOUS_ID, "sia-tab-e5812b51d802")


def recorded() -> dict[str, dict[str, str]]:
    """``{member path: {source id: SHA-256}}`` from the two places that hold them."""
    out: dict[str, dict[str, str]] = {}
    with PREVIOUS.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            out.setdefault(row["member"], {})[PREVIOUS_ID] = row["sha256"]
    for entry in json.loads(VINCULOS.read_text(encoding="utf-8"))["membros"].values():
        if entry["fonte"] in PACKAGED_IDS:
            held = out.setdefault(entry["membro"], {}).setdefault(entry["fonte"], entry["sha256"])
            if held != entry["sha256"]:
                raise SystemExit(f"{entry['membro']}: vinculos.json and {PREVIOUS.name} differ")
    return out


def main(zip_path: Path) -> None:
    known = recorded()
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(
        ["member", "bytes", "sha256", "zip_date", "recorded_source", "recorded_sha256"]
    )
    compared = equal = 0
    changed: list[str] = []
    added: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in sorted(zf.infolist(), key=lambda i: i.filename):
            if info.is_dir():
                continue
            digest = hashlib.sha256(zf.read(info)).hexdigest()
            date = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*info.date_time)
            held = known.pop(info.filename, {})
            if not held:
                added.append(info.filename)
            for source, sha in held.items() or [("", "")]:
                writer.writerow([info.filename, info.file_size, digest, date, source, sha])
                if source:
                    compared += 1
                    equal += sha == digest
                    if sha != digest:
                        changed.append(f"{info.filename} ({source})")
    print(f"{compared} recorded hashes compared, {equal} equal", file=sys.stderr)
    print(f"{len(changed)} changed: {changed}", file=sys.stderr)
    print(f"{len(added)} without a recorded hash: {added}", file=sys.stderr)
    print(f"{len(known)} recorded members absent from the zip: {sorted(known)}", file=sys.stderr)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
