"""Census of DBF headers: what every file of a prefix declares, with no record read.

A `.dbc` stores the DBF header uncompressed at its start: bytes 8-9 give the header's
size, and the field descriptors follow byte 32. For each file the server lists, this
asks for the file, keeps that many bytes and closes the transfer.

    python censo.py read SERVER_DIR PREFIX CACHE.csv
    python censo.py write CACHE.csv NAME

`read` appends one row per file to CACHE.csv and skips the files already there, so a
dropped connection costs one file. `write` numbers the descriptor lists by the first
month that has them and writes NAME.csv and NAME.layouts.csv next to this script.
"""

from __future__ import annotations

import contextlib
import csv
import ftplib
import hashlib
import re
import struct
import sys
import time
from datetime import datetime
from pathlib import Path

HOST = "ftp.datasus.gov.br"
HERE = Path(__file__).parent
CACHE_COLUMNS = ["file", "server_modified", "size_bytes", "header_sha256", "records", "fields"]


def connect() -> ftplib.FTP:
    conn = ftplib.FTP(HOST, timeout=90)
    conn.login()
    conn.voidcmd("TYPE I")
    return conn


def read_header(conn: ftplib.FTP, path: str) -> bytes:
    sock = conn.transfercmd(f"RETR {path}")
    header, size = b"", 10
    try:
        while len(header) < size:
            chunk = sock.recv(size - len(header))
            if not chunk:
                break
            header += chunk
            if size == 10 and len(header) == 10:
                size = struct.unpack("<H", header[8:10])[0]
    finally:
        sock.close()
    with contextlib.suppress(ftplib.Error):
        conn.voidresp()  # the server reports the transfer it was not allowed to finish
    if len(header) < 10 or len(header) != struct.unpack("<H", header[8:10])[0]:
        raise OSError(f"short header for {path}: {len(header)} bytes")
    return header


def descriptors(header: bytes) -> list[str]:
    """`NAME TYPEWIDTH.DECIMALS` per field, in file order."""
    out = []
    for start in range(32, len(header) - 32, 32):
        field = header[start : start + 32]
        if field[0] == 0x0D:
            break
        name = field[:11].split(b"\x00")[0].decode("ascii")
        out.append(f"{name} {chr(field[11])}{field[16]}.{field[17]}")
    return out


def read(server_dir: str, prefix: str, cache: Path) -> None:
    conn = connect()
    lines: list[str] = []
    conn.retrlines(f"LIST {server_dir}", lines.append)
    listed = re.compile(
        rf"(\d\d-\d\d-\d\d\s+\d\d:\d\d[AP]M)\s+(\d+)\s+({prefix}[A-Z]{{2}}\d{{4}}\.dbc)", re.I
    )
    done = set()
    if cache.exists():
        with cache.open(encoding="utf-8", newline="") as f:
            done = {row["file"] for row in csv.DictReader(f)}
    with cache.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        if not done:
            writer.writerow(CACHE_COLUMNS)
        for line in lines:
            match = listed.fullmatch(line.strip())
            if not match or match[3] in done:
                continue
            modified = datetime.strptime(" ".join(match[1].split()), "%m-%d-%y %I:%M%p")
            for attempt in range(8):
                try:
                    header = read_header(conn, f"{server_dir}/{match[3]}")
                    break
                except (OSError, EOFError, ftplib.Error):
                    conn.close()
                    time.sleep(3 + 3 * attempt)
                    conn = connect()
            else:
                raise SystemExit(f"cannot read {match[3]}")
            records = struct.unpack("<I", header[4:8])[0]
            writer.writerow(
                [
                    match[3],
                    f"{modified:%Y-%m-%dT%H:%M}",
                    match[2],
                    hashlib.sha256(header).hexdigest(),
                    records,
                    " ".join(descriptors(header)),
                ]
            )
            f.flush()


def month(file: str) -> str:
    """`RDAC0909.dbc` is 2009-09; the two digits from 92 on are of the 1900s."""
    year = int(file[4:6])
    return f"{(1900 if year >= 92 else 2000) + year}-{file[6:8]}"


def write(cache: Path, name: str) -> None:
    with cache.open(encoding="utf-8", newline="") as f:
        rows = sorted(csv.DictReader(f), key=lambda row: row["file"])
    first: dict[str, tuple[str, str]] = {}
    for row in rows:
        key = (month(row["file"]), row["file"])
        first[row["fields"]] = min(first.get(row["fields"], key), key)
    numbered = {fields: n for n, fields in enumerate(sorted(first, key=first.__getitem__), 1)}
    with (HERE / f"{name}.layouts.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["layout", "fields"])
        writer.writerows((n, fields) for fields, n in numbered.items())
    with (HERE / f"{name}.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            ["file", "server_modified", "size_bytes", "header_sha256", "records", "layout"]
        )
        for row in rows:
            writer.writerow([row[c] for c in CACHE_COLUMNS[:5]] + [numbered[row["fields"]]])


if __name__ == "__main__":
    if sys.argv[1] == "read":
        read(sys.argv[2], sys.argv[3], Path(sys.argv[4]))
    else:
        write(Path(sys.argv[2]), sys.argv[3])
