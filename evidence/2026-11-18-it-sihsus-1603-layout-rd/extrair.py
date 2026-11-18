"""Transcribe Table 1 of IT_SIHSUS_1603.pdf, the layout of the RD files, to CSV.

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-it-sihsus-1603-layout-rd/extrair.py IT_SIHSUS_1603.pdf \
        > evidence/2026-11-18-it-sihsus-1603-layout-rd/tabela1.csv

The PDF is `sihsus-1e89d5f2cc41` in `registry.json`; the script stops when the file given
has another SHA-256. One row per line of the table: the page, the sequence number, the
field name and the type as printed, and the text of "Descrição/Observações" with its
line breaks and runs of spaces turned into one space. `campo` is the dictionary's name
for the row: the printed name in lowercase, except the three names the document
misspells (`CORRECTED`).
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

from pypdf import PdfReader

SHA256 = "1e89d5f2cc41420385d7e30ba5541a387912ab3a0efb167d39def74502076220"
CORRECTED = {"MÊS_CMPT": "mes_cmpt", "DI_INTER": "dt_inter", "DESTAO": "gestao"}
"""Printed name -> DBF field. The DBF headers of the census
(evidence/2026-10-06-rd-2008-layouts) have MES_CMPT, DT_INTER and GESTAO, in the
positions where the table prints these three."""
ROW = re.compile(r"^\s*(\d+)\s+(\S+)\s+((?:char|numeric)\s*\([\d, ]+\))\s+(\S.*)$")
END = "3. Layout dos arquivos SP*.dbf"


def rows(pdf: Path) -> list[dict[str, str | int]]:
    out: list[dict[str, str | int]] = []
    for number, page in enumerate(PdfReader(pdf).pages, start=1):
        for line in page.extract_text(extraction_mode="layout").splitlines():
            if END in line and out:
                return out
            match = ROW.match(line)
            if match:
                seq, name, kind, text = match.groups()
                out.append(
                    {
                        "pagina": number,
                        "seq": int(seq),
                        "nome_no_documento": name,
                        "campo": CORRECTED.get(name, name.lower()),
                        "tipo": re.sub(r"\s+", "", kind),
                        "descricao": " ".join(text.split()),
                    }
                )
            elif out and line.strip() and not _is_furniture(line):
                out[-1]["descricao"] = f"{out[-1]['descricao']} {' '.join(line.split())}"
    raise ValueError("the end of Table 1 was not found")


def _is_furniture(line: str) -> bool:
    """Page header, column header or section title: not a continuation of a row."""
    text = line.strip()
    return (
        text.startswith(("Ministério da Saúde", "DIDIS", "SEQ"))
        or text.startswith("Tabela ")
        or bool(re.match(r"^\d\.?\s", text))
    )


def main(pdf: Path) -> None:
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"{pdf.name} has SHA-256 {digest}, not {SHA256}")
    table = rows(pdf)
    writer = csv.DictWriter(sys.stdout, fieldnames=list(table[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(table)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
