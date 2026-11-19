# SIH: the DBF header of every SP, RJ and RD file (#182)

The dictionaries of `sih_servicos_profissionais` and `sih_aih_rejeitada` were written
from one fixture each, of Roraima in 2024-01, and the two censuses of RD layouts read one
UF a month. This census reads what every file of the three prefixes declares, to see
which layouts the dictionaries have to cover.

A `.dbc` stores the DBF header uncompressed at its start. `censo.py` asks the server
for each file, keeps the header (1,153 to 3,681 bytes) and closes the transfer. The
script reads no record and keeps nothing past the header; for this census, that is all
that was read of the SP files.

    python evidence/2026-11-19-sih-cabecalhos/censo.py read \
        /dissemin/publicos/SIHSUS/200801_/Dados SP sp.cache.csv
    python evidence/2026-11-19-sih-cabecalhos/censo.py write sp.cache.csv sp

and the same for `RJ` and for `RD`, the latter in that directory (`rd`) and in
`/dissemin/publicos/SIHSUS/199201_200712/Dados` (`rd_1992_2007`). Run on 2026-11-19
against `ftp.datasus.gov.br`.

- `sp.csv`, `rj.csv`, `rd.csv` and `rd_1992_2007.csv`: one row per `.dbc` file of the
  prefix the directory listed, with the server's time
  and size, the SHA-256 of the header bytes, the record count the header declares and
  the layout number. The SHA-256 is of the header, not of the file.
- `*.layouts.csv`: each distinct list of field descriptors
  (`NAME TYPEWIDTH.DECIMALS`, in file order), numbered by the first month that has it.

| Prefix | Files | Months | Records declared | Layouts |
|---|---:|---|---:|---:|
| `SP` | 6,072 | 2008-01 to 2026-09 | 2,608,295,244 | 3 |
| `RJ` | 5,913 | 2008-01 to 2026-09 | 15,594,298 | 5 |
| `RD` | 6,072 | 2008-01 to 2026-09 | 227,938,672 | 7 |
| `RD` | 5,165 | 1992-01 to 2007-12 | 205,572,316 | 19 |

| Prefix | Layout | Months | Files | Fields | Against the layout before |
|---|---:|---|---:|---:|---|
| `SP` | 1 | 2008-01 to 2025-02 | 5,337 | 36 | (first) |
| `SP` | 2 | 2008-03 to 2008-12 | 225 | 36 | `SP_NF` C20 to C8 |
| `SP` | 3 | 2025-03 to 2026-09 | 510 | 37 | adds `FONTE_ORC`; `SP_NF` is C20 |
| `RJ` | 1 | 2008-01 to 2010-12 | 941 | 89 | (first) |
| `RJ` | 2 | 2011-01 to 2011-12 | 312 | 90 | adds `NAT_JUR` |
| `RJ` | 3 | 2012-01 to 2012-12 | 314 | 90 | `INSC_PN` C10 to C12 |
| `RJ` | 4 | 2013-01 to 2025-02 | 3,836 | 90 | `GESTOR_COD` C3 to C5 |
| `RJ` | 5 | 2025-03 to 2026-09 | 510 | 91 | adds `FONTE_ORC` |

The layouts of `SP` 1 and 2 overlap in two months: in 2008-03 and in 2008-12 some files
have `SP_NF` C8 and others C20. No field changes between text and number in either prefix.

## What it settles

- **`FONTE_ORC`.** C(2), the last field of the header, in every `SP` and every `RJ`
  file from 2025-03 on (510 of each) and in none before. The two dictionaries did not
  declare it. They now do, with no label and no map: the packaged `SP2008.DEF` and
  `RJ2008.DEF` do not name the field. `RD2008.DEF`, line 274, binds the RD's
  `FONTE_ORC` to `CNV/fonterem.CNV`; that line is the RD's.
- **Types.** Every other field the two dictionaries declare has, in every layout, the
  type family the dictionary gives it (`C` text; `N` a whole number, or a number when
  the descriptor has decimals). The five fields declared `date` (`sp_dtinter`,
  `sp_dtsaida`, `nasc`, `dt_inter`, `dt_saida`) are `C8.0` in the file.

## The values of `FONTE_ORC` in RJ

`rj_fonte_orc.csv` has the rows per value of `FONTE_ORC` in the 18 `RJRR` files of
2025-03 to 2026-08, downloaded whole on 2026-11-19 (the server lists no `RJRR2609`),
with each file's size and SHA-256:

    uv run --locked python evidence/2026-11-19-sih-cabecalhos/medir_fonte_orc.py DIR \
        evidence/2026-11-19-sih-cabecalhos/rj_fonte_orc.csv

The 1,270 records have `00`. It is the value the RD publishes in its own `FONTE_ORC`,
which the RD's map leaves without a label (issue `fonte_orc-00-sem-fonte` of the RD).
They are 18 files of one small UF; another UF may publish another value. The files
carry `GESTOR_CPF`, and only counts left them. The fixture `sih_rj_rr_2026_08_mini` is
`RJRR2608.dbc`, its four records, with that column blanked.

## The RD files

The two censuses of RD layouts downloaded one UF a month:
`evidence/2026-10-01-rd-1992-2007-layouts` (260 files) and
`evidence/2026-10-06-rd-2008-layouts` (243 files). Every file both read has, here, the
layout the census recorded. The server has since replaced 11 of the 243 files of the
second census (`RDRR2509` to `RDRR2606`, and `RDAP2607`): their size, time and record
count are no longer the ones in its rows. The directory of 2008 on also lists
`RDAC2017.zip` (2,875,093 bytes) and `RDSP2017.zip` (178,091,353 bytes), both dated
2018-06-04; they are not `.dbc` files and were not read. The headers add this:

- **1992-2007.** The 5,165 files have the 19 layouts of the census and no other; the
  layout numbers here are the census's. `NUM_PROC` is `N4.0` in every file of 1996-01 to
  1996-07 (188 files), and `INSC_PN` and `SEQ_AIH5` are `N` in every file of 2004-07 to
  2006-03 (567 files); they are `C` in every other file that has them, and no other field changes
  between text and number (#40). The files are those of the listing of 2026-10-02
  (`tests/fixtures/listings/sihsus_199201_200712_dados_rd.txt.gz`), same size and time.
- **From 2008.** 6,071 of the 6,072 files have one of the 6 layouts of the census. The
  numbers differ: layout 1 here is the census's 1, layouts 3 to 7 are its 2 to 6, and
  layout 2 is one file, `RDAC0909.dbc`.

## `RDAC0909.dbc` (#219)

The server dates it 2024-05-22; the other eleven `RDAC` files of 2009 are of 2013-11-01.
That is the directory's time, not proof of when the content was written: the three
bytes of the DBF header that hold the date of last update are `11, 1, 13` in this file
and `111, 11, 10` in `RDAC0908.dbc`.
Against the 86 fields of every other file of 2008-01 to 2010-12, its header has 82:
`QT_DIARIAS`, `ETNIA`, `SEQUENCIA` and `REMESSA` are missing, and 33 descriptors differ.
In 17 the type family changes, all to `N1.0`: eleven value fields that are `N` with two
decimals elsewhere (`VAL_SH`, `VAL_SP`, `VAL_SADT`, `VAL_RN`, `VAL_ACOMP`, `VAL_ORTP`,
`VAL_SANGUE`, `VAL_SADTSR`, `VAL_TRANSP`, `VAL_OBSANG`, `VAL_PED1AC`) and six text fields
(`NUM_PROC`, `CPF_AUT`, `GESTOR_COD`, `GESTOR_DT`, `INFEHOSP`, `FAEC_TP`). `VAL_TOT`,
`VAL_UTI` and `US_TOT` are `F8.2`, a field type no other header of the four censuses
has and the Rust DBF reader does not read; the library reads this file with the Python
reader.

`rdac0909.csv` has, for that file and for `RDAC0908.dbc`, both downloaded whole on
2026-11-19, the size, the SHA-256 and the rows in which each field is neither blank nor
zero:

    uv run --locked python evidence/2026-11-19-sih-cabecalhos/medir_preenchimento.py \
        evidence/2026-11-19-sih-cabecalhos/rdac0909.csv RDAC0908.dbc RDAC0909.dbc

`VAL_SH` and `VAL_SP` are zero in the 4,540 records of `RDAC0909` and filled in the 4,379
of `RDAC0908`; `VAL_TOT` and `US_TOT` are filled in all records of both. The other 15
fields that change family are blank or zero in both files. The fixture
`sih_rd_ac_2009_09_excerpt` keeps records 5 to 9 (counted from 0) byte for byte: in them
`INSC_PN`, the pre-natal number 617 records of the file carry, is zeros, and so is
`GESTOR_CPF`.

The file and any other RD file from 2008 cannot share a table of the lake: in every
other layout the eleven value fields have decimals and the six others are text, and the
lake does not convert between them. Whichever is imported second is refused
(`UnsafeSchemaError`); imported first, `RDAC0909` stays and the other is refused.

**What it is used for.** `tests/unit/transforms/test_sih_headers.py` compares the SP and
RJ dictionaries with the layouts, and the issue `fonte_orc-sem-def` of the field in each
dictionary quotes these counts. `tests/unit/transforms/test_sih_rd_headers.py` compares
the RD headers with the two censuses and with the fixture of `RDAC0909`.
