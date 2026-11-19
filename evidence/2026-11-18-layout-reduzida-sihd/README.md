# Layout_REDUZIDA.pdf: the layout of the reduced file before 2008, row by row (#182)

`Layout_REDUZIDA.pdf` at `ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/`
was read on 2026-11-18: 26,945 bytes, SHA-256
`f6084d22de3011fd9d2f490736e6d0469c45ac3ccc45be56f4e5c0ad564cb13d`, registered as
`sihsus-f6084d22de30` in `registry.json`. `manuais-listing.txt` is the listing of that
directory as the server returned it that day (81 files).

The directory is where the DATASUS page of manuals of the SIHD
(`http://www2.datasus.gov.br/SIHD/manuais`) points. The page links the file as "Layout
do arquivo de REDUZIDA gerado pelo SIHD" under the heading "SIHD (uso até 12/2007)";
`pagina-de-manuais-trecho.html` holds those six lines (181 to 186) of the page, with
CRLF line ends turned into LF. The whole page cannot be pinned by a hash: it was 23,329
bytes in two requests on 2026-11-18, with SHA-256
`8bc0a869e307c485ed586e0858fad7e44c8f4fc4b61dd62db895135cafd15397` in the first and
another in the second, because its last lines print the time of the request
("Atualização da página em: 18-11-2026 00:40:20"). The six lines were the same in both.

`layout.csv` has one row per line of the document's table, "ARQUIVO REDUZIDA - SIHD"
(2 pages): the page and the five printed columns (NOME, TIPO, TAM, DEC, DESCRIÇÃO); a
line break or a run of spaces inside the description is one space. `extrair.py` wrote
it from the PDF's text layer with pypdf 7.1.0, and stops when the file it is given has
another SHA-256:

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-layout-reduzida-sihd/extrair.py Layout_REDUZIDA.pdf \
        > evidence/2026-11-18-layout-reduzida-sihd/layout.csv

- 75 rows. Name, type, width and decimals are, row by row, those of layout 19 of the
  census of the RD files until 2007 (`evidence/2026-10-01-rd-1992-2007-layouts`): the 23
  files read from 2006-04 to 2007-12. The 18 earlier layouts of that census differ, so
  the document is the layout of the RD of those 21 months, whatever the page's heading
  says of the system.
- The 75 names are, in the same order, 75 of the 86 fields of layout 1 of the census of
  the RD files from 2008 (`evidence/2026-10-06-rd-2008-layouts`, 38 files from 2008-01
  to 2010-12). The 11 that layout 1 has and this document lacks are `QT_DIARIAS`,
  `GESTOR_TP`, `CNPJ_MANT`, `COMPLEX`, `FINANC`, `FAEC_TP`, `REGCT`, `RACA_COR`,
  `ETNIA`, `SEQUENCIA` and `REMESSA`.
- The descriptions are printed in capitals, most of them without accents
  ("QTD DE DIAS DE UTI NO MES INICIAL DA INTERNACAO").

**What it is used for.** `IT_SIHSUS_1603.pdf`, the layout of the RD files from 2008,
says only "Zerado" of 19 fields. In `sih_aih_reduzida.yaml` each of the 19 takes as
label the description this document prints for the same field name, in sentence case
and with the accents restored, with a `/field/label` claim that names the page and
quotes the row, and an open issue `rotulo-do-layout-ate-2007`. Where `IT_SIHSUS_1603`
describes a field, its text is used and this document is not, even where the two
differ (`ANO_CMPT` is "ANO COMPETÊNCIA" here and "Ano de processamento da AIH" there).
`tests/unit/transforms/test_sih_rd_fields.py` reads `layout.csv`,
`manuais-listing.txt` and `pagina-de-manuais-trecho.html`: it compares the labels with
the document, the rows with the two censuses, and checks the listing line and the
heading. No test reads the PDF, which is not in the repository: what ties the CSV to
the document is running `extrair.py` again.

**What it does not settle.** The document says what a field was called in 2006 and
2007, not what the RD files publish today: in RDRR2401 the 17 numeric "Zerado" fields
are 0 in every record and the two text ones are blank. No RD file from 2008 to 2021 was
read for those fields. The two documents do not always agree on a family of fields:
this one calls `UTI_INT_IN`, `UTI_INT_AN` and `UTI_INT_AL` days "EM UTI ... (tipo ato =
34 ou 56)", and `IT_SIHSUS_1603` calls their total, `UTI_INT_TO`, "Quantidade de diárias
em unidade intermediaria."; the issue of those three fields says so. The document's
code lists (`SEXO`, `HOMONIMO`, `GESTRISCO` and others) are not used as code maps.
