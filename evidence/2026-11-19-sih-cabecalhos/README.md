# SIH: the DBF header of every SP and RJ file (#182)

The dictionaries of `sih_servicos_profissionais` and `sih_aih_rejeitada` were written
from one fixture each, of Roraima in 2024-01. This census reads what every file of the
two prefixes declares, to see which layouts those dictionaries have to cover.

A `.dbc` stores the DBF header uncompressed at its start. `censo.py` asks the server
for each file, keeps the header (1,185 to 2,945 bytes) and closes the transfer: no record
is read, so no SP file, which names the professional in `SP_PF_DOC`, was downloaded.

    python evidence/2026-11-19-sih-cabecalhos/censo.py read \
        /dissemin/publicos/SIHSUS/200801_/Dados SP sp.cache.csv
    python evidence/2026-11-19-sih-cabecalhos/censo.py write sp.cache.csv sp

and the same for `RJ`. Run on 2026-11-19 against `ftp.datasus.gov.br`.

- `sp.csv` and `rj.csv`: one row per file the directory listed, with the server's time
  and size, the SHA-256 of the header bytes, the record count the header declares and
  the layout number. The SHA-256 is of the header, not of the file.
- `sp.layouts.csv` and `rj.layouts.csv`: each distinct list of field descriptors
  (`NAME TYPEWIDTH.DECIMALS`, in file order), numbered by the first month that has it.

| Prefix | Files | Months | Records declared | Layouts |
|---|---:|---|---:|---:|
| `SP` | 6,072 | 2008-01 to 2026-09 | 2,608,295,244 | 3 |
| `RJ` | 5,913 | 2008-01 to 2026-09 | 15,594,298 | 5 |

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
  the descriptor has decimals).

## The values of `FONTE_ORC` in RJ

`rj_fonte_orc.csv` has the rows per value of `FONTE_ORC` in the 18 `RJRR` files of
2025-03 to 2026-08, downloaded whole on 2026-11-19 (the server lists no `RJRR2609`),
with each file's size and SHA-256:

    uv run --locked python evidence/2026-11-19-sih-cabecalhos/medir_fonte_orc.py DIR \
        > evidence/2026-11-19-sih-cabecalhos/rj_fonte_orc.csv

The 1,270 records have `00`, a code `fonterem.CNV` does not list. They are 18 files of
one small UF; another UF may publish another value.

**What it is used for.** `tests/unit/transforms/test_sih_headers.py` compares the two
dictionaries with the layouts, and the issue `fonte_orc-sem-def` of the field in each
dictionary quotes these counts.
