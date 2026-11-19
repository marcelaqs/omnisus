# AP_NATJUR in the other APAC files: the name and the values (#183)

`APAC_Dados_Comuns.DEF` of `TAB_SIA.zip` (files `A?*.DBC`; SHA-256 in
`evidence/2026-11-18-tab-sia-republicado/members.csv`) binds `AP_NATJUR` to
`CNV/NATJUR.CNV` (line 203) and `CNV/NATJURC.CNV` (lines 204-205), and `AP_NAT_JUR` to
`CNV/ESFERAJUR.CNV` and `CNV/ESFERAJURC.CNV` (lines 206-208). The DEF of seven APAC
datasets writes `AP_NAT_JUR` on all six lines, and those of ACF and ATD have no such
line. This folder records what the files publish. The listing of
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/` was read on
2026-11-18 and the files were downloaded in the hours after it, into 2026-11-19 (time of
São Paulo); the dictionaries call it the census of 2026-11-19.

- **What was read.** 9,527 files, 194,950,493 bytes, 3,364,586 records, none failed:
  every file of AB (635), ABO (1,621), ACF (3,795) and AMP (903), and the files of RR, AC
  and AP of AD (670), AM (659), AQ (632), AR (181; the listing has no AR file of RR) and
  ATD (431). The AN files are in
  `evidence/2026-11-18-censo-sia-an/`.
- **How.** `census.py` downloaded each file, checked its size against the listing, took
  its SHA-256, read the DBF header and sliced the bytes of `AP_NATJUR` out of each
  record, with spaces and NULs removed at both ends. No other column is decoded. The
  file was then deleted. `tables.py` wrote the
  two tables from the JSON lines `census.py` wrote, which are not committed, like the
  listing.
- `files.csv`: one row per file. Bytes, SHA-256, the time the server lists, number of
  fields, SHA-256 of the field names joined by commas, the field names that contain
  both `NAT` and `JUR`, the position and the width of `AP_NATJUR` in the header,
  records. Nine of the
  files are fixtures of the repository, with the SHA-256 `tests/fixtures/FIXTURES.md`
  records.
- `values.csv`: records and files per value of `AP_NATJUR`, by file prefix. A value is
  the field with spaces and NULs removed at both ends; empty is a field of only those.

## What it counts

- **The name.** No file has a field named `AP_NAT_JUR`. 7,211 files have `AP_NATJUR`,
  always the last field and 4 characters wide; 2,316 have neither.
- **The months.** Counting every prefix read: no file of 2008-01 to 2011-11, of 2012-01
  to 2014-09 or of 2014-11 to 2016-06 has the field; every file of 2011-12 and of
  2016-07 to 2026-08 has it; 2014-10 has files with it and files without.
- **The values.** 2,276,452 records have the field filled, with 28 distinct values;
  211,649 have it empty. Each of the 28 is a code of `CNV/natjurc.cnv` (the member the
  DEF files write `CNV/NATJURC.CNV`) of the `TAB_SIA.zip` republished on 2026-10-15
  (`sia-tab-1ce232b217c6`, SHA-256 of the member in
  `evidence/2026-11-18-tab-sia-republicado/members.csv`), which lists 97 codes of four
  digits and the line `-zzzz,` ("Não especificado ou ignorado").
- **AMP** has the field empty in all its 204,038 records that have it.

## What it does not show

- AD, AM, AQ, AR and ATD outside RR, AC and AP. By the listing, which is not committed,
  the files read are 670 of 6,046 (AD),
  659 of 5,986 (AM), 632 of 6,006 (AQ), 181 of 5,491 (AR) and 431 of 3,911 (ATD) the
  listing has, under 1% of the bytes of each. A code only another UF publishes is not
  here.
- Whether a label describes the establishment: the census checks that a published
  value is a code of the table, not what the code means.
- Why seven DEF files write another name.
- Records marked as deleted: the census counts every record of the file.
