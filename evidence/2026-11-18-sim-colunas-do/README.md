# Columns of every DO file on the server

`colunas.csv` has one row per file whose name starts with `DO` in four directories of the
DATASUS server, as listed on 2026-11-18: `SIM/CID10/DORES` (812 files: 27 UF and `DOBR` for
each year from 1996 to 2024), `SIM/PRELIM/DORES` (56: 2025 and 2026), `SIM/CID10/DOFET`
(133: `DOEXT`, `DOFET`, `DOINF`, `DOMAT` and 15 `DOREXT`) and `SIM/PRELIM/DOFET` (10). Each
row gives the size the server lists, the SHA-256 of the DBF header and the column names in
file order. A `.dbc` starts with the DBF header, uncompressed, so `colunas.py` reads only
those bytes of each file; the SHA-256 is of the header, not of the file.

- None of the 868 `DO<UF><year>` files carries `NUMERODO`, `OPOR_DO`, `TP_ALTERA`, `CB_ALT`,
  `COVID_CLAS` or `MAT_CLAS`.
- One file of the 1,011 carries `NUMERODO`, `TP_ALTERA` and `CB_ALT`: `DOREXT21.dbc`, in
  `SIM/CID10/DOFET`, which omnisus does not import. No file carries the other three.
- `UFINFORM` is in the header of the 28 files of each year from 2002 to 2010 and of one file
  of 2001.
- `CONTADOR` is in all 868 `DO<UF><year>` files, spelled `contador` in 336 of them.
- 2001, 2006, 2009 and 2012 have two layouts among the 28 files of the year.

`tests/unit/test_sim_colunas_publicadas.py` reads the table. Not covered: the CID-9 files
(`SIM/CID9/DORES`) and the values of any column.
