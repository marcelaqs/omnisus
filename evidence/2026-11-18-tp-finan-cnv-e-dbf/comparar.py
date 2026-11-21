"""Compare the two TP_FINAN tables of TAB_SIH.zip, code by code.

    uv run --locked python evidence/2026-11-18-tp-finan-cnv-e-dbf/comparar.py TAB_SIH.zip \
        > evidence/2026-11-18-tp-finan-cnv-e-dbf/comparacao.csv

The zip is `sih-tab-21e42384645a` in `registry.json`; the script stops when the file given
has another SHA-256. One row per code of either table: the code, its label in
`CNV/TP_FINAN.CNV` as the library reads it (`parse_cnv`, `cnv_map`) and its description
in `DBF/TP_FINAN.dbf` (`dbf_lookup_map`, key `CO_TPFIN`, column `DS_TPFIN`). A code a
table does not have gets an empty cell in that table's column.
"""

from __future__ import annotations

import csv
import hashlib
import sys
import zipfile
from pathlib import Path

from omnisus.transforms.cnv import cnv_map, dbf_lookup_map, parse_cnv

SHA256 = "21e42384645a9386add9f3644264145f39fc00bbb602f305d87bd0793b7e476b"


def main() -> None:
    raw = Path(sys.argv[1]).read_bytes()
    found = hashlib.sha256(raw).hexdigest()
    if found != SHA256:
        raise SystemExit(f"SHA-256 {found}, expected {SHA256}")
    with zipfile.ZipFile(sys.argv[1]) as package:
        table = cnv_map(parse_cnv(package.read("CNV/TP_FINAN.CNV").decode("latin-1")))
        related = dbf_lookup_map(package.read("DBF/TP_FINAN.dbf"), "FAEC_TP", "DS_TPFIN")
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["codigo", "rotulo_no_cnv", "descricao_no_dbf"])
    for code in sorted(table.keys() | related.keys()):
        writer.writerow([code, table.get(code, ""), related.get(code, "")])


if __name__ == "__main__":
    main()
