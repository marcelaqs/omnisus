"""Quote, from two DATASUS documents, the passages that give codes to fields the RD has
without a code list: the classification of a secondary diagnosis and the homonym mark.

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-sih-codigos-em-outros-documentos/extrair.py \
        "layout sisaih01-sihd - para cmpt 09-2015.pdf" dicionario_de_dados_AIH.pdf \
        > evidence/2026-11-18-sih-codigos-em-outros-documentos/trechos.csv

The script stops when a file has another SHA-256. One row per field (the nine classes of
a secondary diagnosis and the homonym mark): the document's id
in `registry.json`, the pages, the name the document gives the field, and the passage,
from the row of that field to the next row of the table, with a line break or a run of
spaces as one space and the page footer (`9/13`) left out.
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

from pypdf import PdfReader

SISAIH01 = "6c7f1298ed25fbd3efb40a140e93cd6978ba23d62f8af9eaaa86fe049e2f89b1"
SIHD2 = "f70974716de829b97b341b2f05ba76eb382c09d867abcf1a0ffbdb95a1c57854"
PASSAGES = [
    # (argument, SHA-256 of the PDF, registry id, pages, field, first line, line after)
    (
        1,
        SISAIH01,
        "sihsus-af543b2b2c9b",
        (7,),
        f"DIAG_SEC_{n}_CLASS",
        rf"^{99 + 2 * n} DIAG_SEC_{n}_CLASS ",
        rf"^{100 + 2 * n} ",
    )
    for n in range(1, 10)
] + [
    (
        2,
        SIHD2,
        "sihsus-f70974716de8",
        (8, 9),
        "AH_ST_DUPLICIDADE",
        r"^AH_ST_DUPLICIDADE ",
        r"^AH_ST_INTO ",
    )
]
FOOTER = re.compile(r"^\d+/\d+$")


def passage(pdf: Path, pages: tuple[int, ...], first: str, after: str) -> str:
    reader = PdfReader(pdf)
    lines = [
        " ".join(line.split())
        for number in pages
        for line in reader.pages[number - 1].extract_text().splitlines()
    ]
    lines = [line for line in lines if line and not FOOTER.match(line)]
    (start,) = (i for i, line in enumerate(lines) if re.match(first, line))
    end = next(i for i in range(start + 1, len(lines)) if re.match(after, lines[i]))
    return " ".join(lines[start:end])


def main() -> None:
    writer = csv.DictWriter(
        sys.stdout, ["source_id", "paginas", "campo", "trecho"], lineterminator="\n"
    )
    writer.writeheader()
    for argument, sha256, source_id, pages, field, first, after in PASSAGES:
        pdf = Path(sys.argv[argument])
        found = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if found != sha256:
            raise SystemExit(f"{pdf.name}: SHA-256 {found}, expected {sha256}")
        writer.writerow(
            {
                "source_id": source_id,
                "paginas": "-".join(map(str, pages)),
                "campo": field,
                "trecho": passage(pdf, pages, first, after),
            }
        )


if __name__ == "__main__":
    main()
