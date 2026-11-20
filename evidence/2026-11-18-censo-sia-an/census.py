"""Census of the AN files: download one, hash it, measure chosen columns, delete it.

    python census.py <listing.txt> <empty work directory> <output.jsonl>

AP_CNSPCN is never selected, counted or written. The library parser decodes every column
of the file before the selection, so the column is read in memory and discarded.
"""

import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from omnisus.sources.datasus_ftp.dbc import decompress_bytes
from omnisus.sources.datasus_ftp.dbf_contract import _read_field_descriptors
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

listing, workdir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
BASE = "ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/"
COUNTS = [
    "ap_ufdif",
    "ap_mndif",
    "ap_natjur",
    "ap_coidade",
    "ap_tippre",
    "ap_ufnacio",
    "an_albumi",
    "an_hb",
    "an_tru",
    "an_intfis",
    "ap_mvm",
    "ap_cmp",
]
DATES = ["ap_dtinic", "ap_dtfim", "ap_dtsolic", "ap_dtaut", "ap_dtocor", "an_dtpdr"]


def valid(v, fmt):
    try:
        datetime.strptime(v, fmt)
        return True
    except ValueError:
        return False


def measure(name, listed):
    path = workdir / name
    for _ in range(3):
        r = subprocess.run(["curl", "-s", "--max-time", "300", "-o", str(path), BASE + name])
        if r.returncode == 0 and path.exists() and path.stat().st_size == listed["bytes"]:
            break
    else:
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
        header = [d.name.strip() for d in _read_field_descriptors(decompress_bytes(raw))]
        row["fields"] = len(header)
        row["header_sha256"] = hashlib.sha256(",".join(header).encode()).hexdigest()
        row["has_ap_natjur"] = "AP_NATJUR" in header
        row["other_names"] = [h for h in header if h in ("AP_NAT_JUR",)]
        lf = dbc_bytes_to_lazyframe(raw, dataset="sia_apac_nefrologia")
        cols = [c for c in COUNTS + DATES if c.upper() in header]
        df = lf.select(cols).collect()
        row["records"] = df.height
        row["counts"] = {c: dict(df[c].value_counts().rows()) for c in COUNTS if c in df.columns}
        row["dates"] = {}
        for c in DATES:
            if c not in df.columns:
                continue
            vals = [v.strip() for v in df[c] if v and v.strip()]
            ok = [v for v in vals if re.fullmatch(r"\d{8}", v) and valid(v, "%Y%m%d")]
            row["dates"][c] = {
                "filled": len(vals),
                "yyyymmdd": len(ok),
                "ddmmyyyy_1900_2100": sum(
                    1
                    for v in vals
                    if re.fullmatch(r"\d{8}", v)
                    and valid(v, "%d%m%Y")
                    and "1900" <= v[4:] <= "2100"
                ),
                "yyyymmdd_outside_1900_2100": sorted(
                    {v for v in ok if not "1900" <= v[:4] <= "2100"}
                )[:5],
                "after_2015": sorted({v for v in ok if v[:4] > "2015"})[:5],
                "min": min(ok, default=None),
                "max": max(ok, default=None),
                "not_valid_sample": sorted({v for v in vals if v not in set(ok)})[:5],
            }
    except Exception as e:  # recorded, not hidden
        row["error"] = f"{type(e).__name__}: {e}"[:300]
    return row


files = {}
for line in listing.read_text(encoding="latin-1").splitlines():
    m = re.match(r"(\S+\s+\S+)\s+(\d+)\s+(AN[A-Z]{2}\d{4}\.dbc)\s*$", line, re.I)
    if m:
        files[m.group(3)] = {"when": m.group(1), "bytes": int(m.group(2))}
done = set()
if out.exists():
    done = {
        json.loads(line)["file"] for line in out.read_text().splitlines() if '"error"' not in line
    }
    out.write_text(
        "".join(line + "\n" for line in out.read_text().splitlines() if '"error"' not in line)
    )
todo = [f for f in sorted(files) if f not in done]
print(len(files), "listed;", len(todo), "to do", flush=True)
with ThreadPoolExecutor(4) as pool, out.open("a") as fh:
    for i, row in enumerate(pool.map(lambda f: measure(f, files[f]), todo), 1):
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        if i % 200 == 0:
            print(i, flush=True)
print("done", flush=True)
