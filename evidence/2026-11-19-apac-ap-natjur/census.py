"""Other APAC files: header and AP_NATJUR only, sliced from the DBF bytes. No other column is decoded."""

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from omnisus.sources.datasus_ftp.dbc import decompress_bytes
from omnisus.sources.datasus_ftp.dbf_contract import _read_field_descriptors

listing, workdir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
BASE = "ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/"
FULL = {"AB", "ABO", "ACF", "AMP"}
SAMPLE = {"AD", "AM", "AQ", "AR", "ATD"}
UFS = {"RR", "AC", "AP"}


def measure(name, listed):
    path = workdir / name
    for _ in range(3):
        r = subprocess.run(["curl", "-s", "--max-time", "600", "-o", str(path), BASE + name])
        if r.returncode == 0 and path.exists() and path.stat().st_size == listed["bytes"]:
            break
    else:
        path.unlink(missing_ok=True)
        return {"file": name, "error": f"download rc={r.returncode}"}
    raw = path.read_bytes()
    path.unlink()
    row = {
        "file": name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "listed": listed["when"],
    }
    try:
        dbf = decompress_bytes(raw)
        desc = list(_read_field_descriptors(dbf))
        names = [d.name.strip() for d in desc]
        n = int.from_bytes(dbf[4:8], "little")
        hl = int.from_bytes(dbf[8:10], "little")
        rl = int.from_bytes(dbf[10:12], "little")
        row.update(
            fields=len(names),
            records=n,
            header_sha256=hashlib.sha256(",".join(names).encode()).hexdigest(),
            natjur_names=[x for x in names if "NAT" in x and "JUR" in x],
            position=None,
        )
        if "AP_NATJUR" in names:
            i = names.index("AP_NATJUR")
            off = 1 + sum(d.width for d in desc[:i])
            w = desc[i].width
            row["position"] = i + 1
            row["width"] = w
            row["values"] = dict(
                Counter(
                    dbf[hl + k * rl + off : hl + k * rl + off + w].decode("latin-1").strip(" \x00")
                    for k in range(n)
                )
            )
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"[:300]
    return row


files = {}
for line in listing.read_text(encoding="latin-1").splitlines():
    m = re.match(
        r"(\S+\s+\S+)\s+(\d+)\s+((A[A-Z]{1,2})([A-Z]{2})\d{4}[a-z]?\.dbc)\s*$", line, re.I
    )
    if not m:
        continue
    prefix, uf = m.group(4).upper(), m.group(5).upper()
    if prefix in FULL or (prefix in SAMPLE and uf in UFS):
        files[m.group(3)] = {"when": m.group(1), "bytes": int(m.group(2))}
done = set()
if out.exists():
    keep = [line for line in out.read_text().splitlines() if '"error"' not in line]
    done = {json.loads(line)["file"] for line in keep}
    out.write_text("".join(line + "\n" for line in keep))
todo = [f for f in sorted(files) if f not in done]
print(len(files), "selected;", len(todo), "to do", flush=True)
with ThreadPoolExecutor(6) as pool, out.open("a") as fh:
    for i, row in enumerate(pool.map(lambda f: measure(f, files[f]), todo), 1):
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        if i % 500 == 0:
            print(i, flush=True)
print("done", flush=True)
