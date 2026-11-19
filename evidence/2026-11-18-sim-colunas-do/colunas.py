"""Column names of every DO file the DATASUS server publishes, read from the DBF header.

    uv run --locked python evidence/2026-11-18-sim-colunas-do/colunas.py CACHE_DIR

A `.dbc` starts with the DBF header, uncompressed, so the script stops each download
once it holds the header. It writes `colunas.csv` next to itself: directory, file, the
size the server lists, the SHA-256 of the header bytes and the column names in file
order. `CACHE_DIR` keeps one JSON per file, so a run cut by a timeout resumes.
"""

from __future__ import annotations

import contextlib
import csv
import ftplib
import hashlib
import json
import struct
import sys
from pathlib import Path

HOST = "ftp.datasus.gov.br"
DIRS = ("/dissemin/publicos/SIM/CID10/DORES", "/dissemin/publicos/SIM/PRELIM/DORES")


class _HeaderReadError(Exception):
    """Raised by the download callback to stop a transfer once the header is in."""


def _connect(directory: str) -> ftplib.FTP:
    ftp = ftplib.FTP(HOST, timeout=60)
    ftp.login()
    ftp.cwd(directory)
    return ftp


def _header(ftp: ftplib.FTP, name: str) -> bytes:
    buffer = bytearray()

    def take(chunk: bytes) -> None:
        buffer.extend(chunk)
        if len(buffer) >= 10 and len(buffer) >= struct.unpack("<H", bytes(buffer[8:10]))[0]:
            raise _HeaderReadError

    with contextlib.suppress(_HeaderReadError):
        ftp.retrbinary(f"RETR {name}", take, blocksize=4096)
    return bytes(buffer[: struct.unpack("<H", bytes(buffer[8:10]))[0]])


def _columns(header: bytes) -> list[str]:
    names, offset = [], 32
    while offset < len(header) and header[offset] != 0x0D:
        names.append(header[offset : offset + 11].split(b"\0")[0].decode("ascii"))
        offset += 32
    return names


def main() -> int:
    cache = Path(sys.argv[1])
    rows = []
    for directory in DIRS:
        ftp = _connect(directory)
        listing: list[str] = []
        ftp.retrlines("LIST", listing.append)
        sizes = {line.split()[-1]: line.split()[-2] for line in listing}
        for name in sorted((n for n in sizes if n.upper().startswith("DO")), key=str.upper):
            kept = cache / f"{directory.split('/')[-2]}_{name}.json"
            if not kept.exists():
                header = _header(ftp, name)
                ftp.close()  # the transfer was cut; a new connection is the clean way on
                ftp = _connect(directory)
                kept.write_text(
                    json.dumps(
                        {
                            "directory": directory,
                            "file": name,
                            "bytes_listed": sizes[name],
                            "header_sha256": hashlib.sha256(header).hexdigest(),
                            "columns": _columns(header),
                        }
                    )
                )
            rows.append(json.loads(kept.read_text()))
        ftp.close()
    with (Path(__file__).parent / "colunas.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["directory", "file", "bytes_listed", "header_sha256", "columns"])
        for row in rows:
            writer.writerow([*list(row.values())[:4], " ".join(row["columns"])])
    print(f"{len(rows)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
