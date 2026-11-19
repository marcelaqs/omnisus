# IT_SIHSUS_1603.pdf, Table 1: the layout of the RD files, row by row (#182)

`IT_SIHSUS_1603.pdf` at `ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Doc/`
was read on 2026-11-18: 57,465 bytes, SHA-256
`1e89d5f2cc41420385d7e30ba5541a387912ab3a0efb167d39def74502076220`, the hash of
`sihsus-1e89d5f2cc41` in `registry.json`. The directory listed that day holds this file
and no other: `doc-listing.txt` is the listing as the server returned it.

`tabela1.csv` has one row per line of Table 1, "Layout dos arquivos RD*.dbf para janeiro
de 2008 em diante" (pages 1 to 4): the page, the sequence number, the field name and the
type as printed, and the text of the "Descrição/Observações" column; a line break or a
run of spaces inside the type or the text is one space. `extrair.py` wrote
it from the PDF's text layer with pypdf 7.1.0, and stops when the file it is given has
another SHA-256:

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-it-sihsus-1603-layout-rd/extrair.py IT_SIHSUS_1603.pdf \
        > evidence/2026-11-18-it-sihsus-1603-layout-rd/tabela1.csv

- 113 rows, numbered 1 to 114; the table has no row 106.
- The 113 names are the 113 fields of layout 5 of the census
  (`evidence/2026-10-06-rd-2008-layouts`, 2014-01 to 2025-02), once three printed names
  are read as the DBF spells them: `MÊS_CMPT` (`MES_CMPT`), `DI_INTER` (`DT_INTER`) and
  `DESTAO` (`GESTAO`). The column `campo` holds the dictionary's name, and
  `nome_no_documento` what is printed.
- 19 rows describe the field with the single word "Zerado".
- `FONTE_ORC`, which the files publish from 2025-03 (layout 6), is not in the table.

**What it is used for.** `sih_aih_reduzida.yaml` takes the `description` of 110 fields
from the column `descricao`, each with a `/field/description` claim that names the page
and quotes the row; `tests/unit/transforms/test_sih_rd_fields.py` compares the two, and
the order of the rows with the DBF header of layout 5. The `label` of 24 fields is the
same text up to its first full stop, each with a `/field/label` claim. No test reads the PDF, which is
not in the repository: what ties the CSV to the document is running `extrair.py` again.
`uf_zi`, `cnes` and `natureza` keep the description they had.

**What it does not settle.** The sentences are the document's, typos included
(`aaammdd` for the date of `DI_INTER`, `diagnostico`). A description says what the
report of 2016-03 says about a field, not what the files publish: in RDRR2401 the
17 numeric "Zerado" fields are 0 in every record, and the two text ones (`NUM_PROC`,
`CPF_AUT`) are blank.
