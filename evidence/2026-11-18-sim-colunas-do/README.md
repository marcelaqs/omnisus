# Columns of every DO file on the server

`colunas.csv` has one row per `DO<UF><year>` file of `SIM/CID10/DORES` (1996 to 2024, 812
files: 27 UF and `DOBR` for each year) and of `SIM/PRELIM/DORES` (2025 and 2026, 56 files),
as the DATASUS server listed them on 2026-11-18. Each row gives the size the server lists,
the SHA-256 of the DBF header and the column names in file order. A `.dbc` starts with the
DBF header, uncompressed, so `colunas.py` reads only those bytes of each file; the SHA-256
is of the header, not of the file.

- No file carries `NUMERODO`, `OPOR_DO`, `TP_ALTERA`, `CB_ALT`, `COVID_CLAS` or `MAT_CLAS`.
- `UFINFORM` is in the 28 files of each year from 2002 to 2010 and in one file of 2001.
- `CONTADOR` is in 27 files of 2006, in all of 2007 and 2008, in one of 2009 and in all
  from 2011 on, including the preliminary ones.
- 2001, 2006, 2009 and 2012 have two layouts among the 28 files of the year.

`tests/unit/test_sim_colunas_publicadas.py` reads the table. Not covered: the national
subsets (`SIM/CID10/DOFET`) and the CID-9 files (`SIM/CID9/DORES`).
