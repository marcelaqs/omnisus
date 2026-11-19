"""Transcribe Layout_REDUZIDA.pdf, the layout of the SIHD reduced file, to CSV.

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-layout-reduzida-sihd/extrair.py Layout_REDUZIDA.pdf \
        > evidence/2026-11-18-layout-reduzida-sihd/layout.csv

The PDF is `sihsus-f6084d22de30` in `registry.json`; the script stops when the file given
has another SHA-256. One row per line of the table: the page and the printed NOME and
DESCRIÇÃO (TIPO, TAM and DEC are read to find the row and left out). In the description,
a line break or a run of spaces becomes one space.
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

from pypdf import PdfReader

SHA256 = "f6084d22de3011fd9d2f490736e6d0469c45ac3ccc45be56f4e5c0ad564cb13d"
ROW = re.compile(r"^(\w+)\s+[CN]\s+\d+\s+\d+(?:\s+(\S.*))?$")
FURNITURE = ("ARQUIVO REDUZIDA - SIHD", "NOME TIPO TAM DEC DESCRIÇÃO")


def rows(pdf: Path) -> list[dict[str, str | int]]:
    out: list[dict[str, str | int]] = []
    for number, page in enumerate(PdfReader(pdf).pages, start=1):
        for raw in page.extract_text().splitlines():
            line = " ".join(raw.split())
            match = ROW.match(line)
            if match:
                name, text = match.groups()
                out.append({"pagina": number, "nome": name, "descricao": text or ""})
            elif line and line not in FURNITURE:
                out[-1]["descricao"] = f"{out[-1]['descricao']} {line}".strip()
    return out


def main() -> None:
    pdf = Path(sys.argv[1])
    found = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if found != SHA256:
        raise SystemExit(f"{pdf.name}: SHA-256 {found}, expected {SHA256}")
    writer = csv.DictWriter(sys.stdout, ["pagina", "nome", "descricao"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows(pdf))


if __name__ == "__main__":
    main()
