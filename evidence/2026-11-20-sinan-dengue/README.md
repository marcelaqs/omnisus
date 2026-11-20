# SINAN dengue: the 27 `DENGBR` files, read on 2026-11-20

Listing of `/dissemin/publicos/SINAN/DADOS/FINAIS` (`DENGBR00` to `DENGBR25`) and
`/dissemin/publicos/SINAN/DADOS/PRELIM` (`DENGBR26`) at `ftp.datasus.gov.br`. Every file
was downloaded whole: 1,076,987,250 bytes and 27,036,454 records. The files are too large
to commit; `tests/fixtures/FIXTURES.md` lists the four excerpts kept.

## What each file holds

`serie.py` hashed each file, read its DBF header, staged it with `dbc_bytes_to_parquet`
under the `sinan_dengue` dictionary and ran `validate_identity`. `serie.json` has one
entry per file: URL, directory, size and time the server listed, SHA-256, records,
layout, the outcome of the identity check, the counts of `nu_ano` and `id_agravo`, and
the staged type of four columns.

- The bytes received equal the listed size in the 27 files, and the staged rows equal the
  header's record count.
- **Identity passes in the 27 files**: the most frequent `nu_ano` is the file year, and
  where `ID_AGRAVO` exists the most frequent code is `A90`.
- `DENGBR00` to `DENGBR06` have no `ID_AGRAVO`. From `DENGBR07` on, every record is `A90`,
  except 11,218 of the 1,405,095 records of `DENGBR22`, which leave it blank.
- 18 files hold records of another `nu_ano`: 9,340 of 1,643,215 in `DENGBR25` (the most),
  3,778 in `DENGBR15`, 1,649 in `DENGBR09`. They stay in the lake as published.

## Four layouts

`leiautes.json` has the field descriptors (name, type, width, decimals) of each distinct
header.

| Layout | Files | Fields | Staged `nu_idade_n` | Staged `plaq_menor` |
| --- | --- | ---: | --- | --- |
| 1 | `DENGBR00` to `DENGBR06` | 107 | absent (`NU_IDADE`, C 4) | string (C 6) |
| 2 | `DENGBR07` to `DENGBR12` | 67 | double (F 4) | string (C 7) |
| 3 | `DENGBR13` | 67 | int64 (N 4) | double (N 18, with decimals) |
| 4 | `DENGBR14` to `DENGBR26` | 121 | int64 (N 4) | string (C 7) |

The dictionary describes layout 4, read from `DENGBR17`.

## One lake table does not hold every layout

`lake_misto.py <empty folder> 2017 2012 2013 2006` imported the four files from the server
into one new lake, in that order:

| File | Outcome |
| --- | --- |
| `DENGBR17` | ok, 239,395 rows |
| `DENGBR12` | `ingest_failed`: `unsafe schema type change: BIGINT versus DOUBLE; explicit migration required` |
| `DENGBR13` | `ingest_failed`: `unsafe schema type change: VARCHAR versus DOUBLE; explicit migration required` |
| `DENGBR06` | ok, 411,022 rows |

Layouts 1 and 4 share a table. Layouts 2 and 3 are refused in a table that holds layout 4,
and no order of import was tried other than this one.

## Codes

- Dictionary: `DIC_DADOS_ONLINE.pdf` (Sinan Online, Dengue/Chikungunya, revised on
  21/10/2015), 339,721 bytes, 27 pages, SHA-256
  `da262c3b9f20f242d01ee235e64c221dd97e6ad9a53d38cc94da9316bf98c4eb`
  (`sinan-da262c3b9f20`). Each page was read as text and as a rendered image.
- `TAB_SINANNET.zip`, 44,001,396 bytes, SHA-256
  `24ac0c62fb84e5458574fef5a9939b4e47f33ba67038549752b787006ca5944e`
  (`sinan-tab-24ac0c62fb84`). It is a republication of `sinan-tab-cad66ee38781`: the seven
  members `vinculos.json` already packaged have the same hash in both; three members are
  dated after 2026-09-22 inside the zip (`EsquisNET.def`, `PfapolioNET.def`,
  `DIAGNOSCOPIA.cnv`). The other members were not compared, because no copy of the older
  edition was kept.
- Values of every field were counted in the complete `DENGBR14`, `DENGBR17` and
  `DENGBR26` (SHA-256 in `serie.json`). `CLASSI_FIN` holds `8` in 87,345, 73,852 and
  72,952 records; the dictionary page lists 5, 10, 11, 12 and 13, and `Classdeng.cnv`
  names 8 "Inconclusivo". `DENGBR26` holds `0` and `9` in fields the page lists as 1 and
  2 (`ALRM_HIPOT`: 20,194 and 40); no page or CNV names them, so they have no label.
- `COMPLICA` has no map: `DengueNET.def` binds it to `CompdengM50mil.cnv` and to
  `CompdengM20mil.cnv`, which label code 4 differently.

## Age rule (`kind: sinan`)

`manifest.json` names the audited file, the complete final `DENGBR17.dbc`
(`ec341731…afce0`), and `acceptance.json` has the states, expressions and queries of
`scripts/metadados/auditar_arquivos.py`.

| Records | Valid | Invalid |
| ---: | ---: | ---: |
| 239,395 | 239,376 | 19 |

Units 1 (hour, 016–084, 6 records), 2 (day, 001–080), 3 (month, 001–082) and 4 (year,
000–407). The 19 invalid values have fewer than four digits. 15 records hold `4401` to
`4407`, which the rule reads as 401 to 407 years; 117 hold `4088` (88 years).

## Not settled

- No official document for layouts 1 to 3 is in the registry; their fields were not
  compared with any page.
- Why `DENGBR22` leaves `ID_AGRAVO` blank in 11,218 records.
