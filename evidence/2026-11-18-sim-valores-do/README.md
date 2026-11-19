# Values of the coded fields in 186 DO files

`arquivos.csv` lists 186 files of `SIM/CID10/DORES`, downloaded from the DATASUS server on
2026-11-18, each with its SHA-256, size, records and number of columns: `DOAC`, `DOAP`,
`DODF`, `DORR`, `DOSE` and `DOTO` of every year from 1996 to 2024, and `DOBA`, `DOPA`,
`DORS` and `DOSP` of 2006, 2015 and 2023. They hold 2,557,540 records. `valores.csv` gives,
by year, how many records hold each value of every `sim_obitos` field with a code map
(`kind` `value`), and each shape of `horaobito`, `codestab`, `ocup`, `ocupmae`, `natural`,
`versaosist` and `causamat` (`kind` `shape`: `9` is a digit, `A` a letter). `medir.py` is
the script.

- `tppos` is `S`, `N` or blank in every record; never the `1` or `2` of the Estrutura do SIM.
- `seriescfal` and `seriescmae` are blank or `1` to `8`; never the `0` or `9` of `SERIEFAL.CNV`.
- `esc2010` and `escmae2010` hold only `0` to `5`, `9` and blank.
- `origem` is `1`, `2`, `3` or blank; never `01`, and never `9`.
- `horaobito` has 4 digits in 2,185,721 records and 5 digits in 8; none is `00:00`.
- `codestab` has 7 digits in every filled record but one.
- `ocup` and `ocupmae` have 5 characters until 2005 and 6 from 2007; 2006 has both.
- `causamat` is blank in all but 35 records, which have the shape of a CID-10 code.
- 17 fields hold values their map does not label, mostly `0` in 2002 and `8` or `A` until
  2001; `tests/unit/test_sim_valores_medidos.py` lists every one.

Not covered: the other 17 UF in the years outside 2006, 2015 and 2023, the preliminary
files and the national subsets.
