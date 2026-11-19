# Layout_REDUZIDA.pdf: the layout of the reduced file before 2008, row by row (#182)

`Layout_REDUZIDA.pdf` at `ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/`
was read on 2026-11-18: 26,945 bytes, SHA-256
`f6084d22de3011fd9d2f490736e6d0469c45ac3ccc45be56f4e5c0ad564cb13d`, registered as
`sihsus-f6084d22de30` in `registry.json`. `manuais-listing.txt` is the listing of that
directory as the server returned it that day (81 files).

The directory is where the DATASUS page of manuals of the SIHD
(`http://www2.datasus.gov.br/SIHD/manuais`) points. The page served on 2026-11-18
(23,329 bytes, SHA-256 `8bc0a869e307c485ed586e0858fad7e44c8f4fc4b61dd62db895135cafd15397`)
links the file as "Layout do arquivo de REDUZIDA gerado pelo SIHD" under the heading
"SIHD (uso até 12/2007)"; `pagina-de-manuais-trecho.html` holds those six lines of the
page, converted from ISO-8859-1 to UTF-8.

`layout.csv` has one row per line of the document's table, "ARQUIVO REDUZIDA - SIHD"
(2 pages): the page and the printed NOME and DESCRIÇÃO; a line break or a run of spaces
inside the description is one space. `extrair.py` wrote it from the PDF's text layer
with pypdf 7.1.0, and stops when the file it is given has another SHA-256:

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-layout-reduzida-sihd/extrair.py Layout_REDUZIDA.pdf \
        > evidence/2026-11-18-layout-reduzida-sihd/layout.csv

- 75 rows. The 75 names are, in the same order, 75 of the 86 fields of layout 1 of the
  census of the RD files from 2008 (`evidence/2026-10-06-rd-2008-layouts`, 2008-01 to
  2010-12). The 11 that layout 1 has and this document lacks are `QT_DIARIAS`,
  `GESTOR_TP`, `CNPJ_MANT`, `COMPLEX`, `FINANC`, `FAEC_TP`, `REGCT`, `RACA_COR`,
  `ETNIA`, `SEQUENCIA` and `REMESSA`.
- The descriptions are printed in capitals, most of them without accents
  ("QTD DE DIAS DE UTI NO MES INICIAL DA INTERNACAO").

**What it is used for.** `IT_SIHSUS_1603.pdf`, the layout of the RD files from 2008,
says only "Zerado" of 19 fields. In `sih_aih_reduzida.yaml` each of the 19 takes as
label the description this document prints for the same field name, in sentence case
and with the accents restored, with a `/field/label` claim that names the page and
quotes the row, and an open issue `rotulo-do-layout-ate-2007`.
`tests/unit/transforms/test_sih_rd_fields.py` compares label and document without case
and diacritics, and the names with layout 1 of the census. No test reads the PDF, which
is not in the repository: what ties the CSV to the document is running `extrair.py`
again.

**What it does not settle.** The document describes the file the SIHD wrote until
2007-12. It says what a field was called then, not what the RD files publish today: in
RDRR2401 the 17 numeric "Zerado" fields are 0 in every record and the two text ones are
blank. It was not compared with RD files of 2007 or earlier, which belong to another
dataset (`sih_aih_reduzida_1992_2007`). Its code lists (`SEXO`, `HOMONIMO`, `GESTRISCO`
and others) are not used.
