# Census of every AN file the server lists (#183)

On 2026-11-18 the listing of `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/`
had 2,145 files `AN<UF><YYMM>.dbc`, from 2008-01 to 2014-10 (82 months, 458,824,790
bytes). All of them were read: 6,534,272 records, no file failed to download or to parse.

`census.py` downloaded each file, checked its size against the listing, took its
SHA-256, read the DBF header and the columns below with the library's parser, and
deleted the file. It never selects, counts or writes `AP_CNSPCN`; the parser decodes
every column of a file before the selection, so the column was read in memory and
discarded. `tables.py` wrote the three tables from the JSON lines `census.py` wrote,
which are not committed, like the listing. No downloaded file was kept. The two AN files
the repository already commits as fixtures (`ANPA1410`, whole, and `ANRR1401`, with
`AP_CNSPCN` blanked) have in `files.csv` the SHA-256 and the listing time
`tests/fixtures/FIXTURES.md` records.

- `files.csv`: one row per file. Bytes, SHA-256, the time the server lists (as listed,
  no time zone), number of fields, SHA-256 of the field names joined by commas, whether
  `AP_NATJUR` is one of them, records.
- `values.csv`: records and files per published value of `ap_ufdif`, `ap_mndif`,
  `ap_natjur`, `ap_coidade`, `ap_tippre`, `ap_ufnacio`, `an_albumi`, `an_hb`, `ap_mvm`
  and `ap_cmp`. Values are as the parser returns them: leading spaces kept, trailing
  spaces and NULs removed, so an empty value is a field of spaces or NULs. The table
  adds the files up; it has no count of a value in one file.
- `dates.csv`: for each of the six dates, the filled values; how many "read as
  `yyyyMMdd`", meaning eight digits with a calendar month and day in any year from 0001
  to 9999; the smallest and largest of those; and the number of files with at least one
  such value whose year is outside 1900-2100, and with at least one whose year is after
  2015. The two last columns count files, not values.

`census.py` also counted `an_tru` and `an_intfis` and recorded, per file, a sample of the
values that do not read as dates; the tables do not carry them, because nothing cites
them.

## What it counts

- **Two headers.** 2,117 files have one list of 60 field names and 28 have one list of
  61 (`header_sha256`). They are the headers of the two fixtures: `ANRR1401`, 60 fields
  ending in `AN_HB`, and `ANPA1410`, 61 ending in `AP_NATJUR`; neither has a field named
  `AP_NAT_JUR`. The 28 are the 27 files of 2011-12 and `ANPA1410`, the only file of
  2014-10. `AP_NATJUR` is empty in 87,203 records and filled in 2 (`3999`, in `ANPA1410`).
- **`ap_mndif`** is `1` in every record. **`ap_ufdif`** is `0` (6,467,051) or `1`
  (67,221). Neither field has `S` or `N` in any AN file.
- **`ap_coidade`**: `4` (6,529,357), `3` (3,408), `2` (970), `5` (519) and `0` (18
  records in 17 files).
- **`ap_tippre`**: seven of the eight codes of `TIPOPRES.CNV`; `80` does not occur, and
  no other value does.
- **`ap_ufnacio`**: 169 distinct values, counting ` 01` and ` 04`, which have a leading
  space in the file. 202 records hold a value `UFNACIO.CNV` does not label (`000`,
  ` 01`, `39`, `24`, `050`, empty, `41`, `95`, `43`, ` 04`, `001`).
- **`ap_mvm`**: each of its 82 values is in exactly the files named after that month,
  with exactly their records. **`ap_cmp`** has 79 values from `200801` to `201407`, each
  a year and a month from 01 to 12.
- **Dates.** Every filled `ap_dtinic`, `ap_dtfim` and `ap_dtocor` reads as `yyyyMMdd`,
  from `20071201` to `20140731`. `ap_dtsolic`, `ap_dtaut` and `an_dtpdr` have 2,712,
  2,669 and 103 filled values that do not, and values that read with years from 0008 to
  9827: 548, 845 and 1,068 files have one outside 1900-2100, and 344, 569 and 602 have
  one after 2015.
- **`an_albumi` and `an_hb`** (CHAR 2, "em g%" in the Informe): integer zero in
  1,638,719 and 1,159,730 records, integers from 1 to 9 in 3,440,835 and 1,246,883,
  integers from 10 to 99 in 1,409,033 and 4,104,933, and text that is not an integer
  (`3,`, `3.`, `NN`, `##`) in 45,685 and 22,726. Spellings such as `4`, `04` and ` 4`
  are added to the same integer here; `values.csv` keeps them apart.

## What it does not show

- What a value means or why it is there: the census counts published values and reads
  no label. It does not say which scale a number of `an_albumi` or `an_hb` is in, or
  whether zero is a measurement.
- How many values, rather than files, have a year outside the two ranges.
- Other APAC datasets: only `AN*.dbc` was read.
- Whether the server changed a file after the listing: sizes matched for all 2,145.

A reviewer who did not write the census downloaded 12 of the files again and recomputed,
with a reader of its own, the SHA-256, the header, the records and every count above
for them: all equal to these tables.
