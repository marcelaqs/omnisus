# RD files: counts that bear on decisions of #182

Counts taken on 2026-11-18 from `RD*.dbc` files of
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/`, so that statements about a few
fields rest on more than one fixture. `medir.py` wrote the four CSV files:

    uv run --locked python evidence/2026-11-18-rd-medidas/medir.py \
        sih_aih_reduzida DIR_2008 evidence/2026-11-18-rd-medidas/2008-2026
    uv run --locked python evidence/2026-11-18-rd-medidas/medir.py \
        sih_aih_reduzida_1992_2007 DIR_2006 evidence/2026-11-18-rd-medidas/2006-2007

Each directory has `arquivos.csv` (file, bytes, SHA-256, records) and `medidas.csv`
(file, measure, key, rows). Only counts leave the files: no row is copied. `CPF_AUT` is
read only as filled or not, and `GESTOR_CPF` is not read.

| Directory | Server directory | Files | Records |
|---|---|---:|---:|
| `2008-2026` | `200801_/Dados` | 238 | 1,994,690 |
| `2006-2007` | `199201_200712/Dados` | 24 | 41,547 |

- `2008-2026`: `RDRR` of every month from 2008-01 to 2026-06, `RDAP2607`, and `RDDF`,
  `RDRJ` and `RDSP` of January 2008, 2012, 2016, 2020 and 2024. 224 of the files are in
  `evidence/2026-10-06-rd-2008-layouts/census.csv`; 213 have the SHA-256 recorded there,
  and the 11 from 2025-09 on were published again since.
- `2006-2007`: `RDRR` of every month of 2006 and 2007, each with the SHA-256 recorded in
  `evidence/2026-10-01-rd-1992-2007-layouts/census.csv` (3 files of layout 18, 21 of
  layout 19).

The measures (`medida`), with a field counted as filled when it is neither blank nor
zero (text made only of zeros is zero):

- `zerado_preenchido`: rows where each of the 19 fields `IT_SIHSUS_1603` calls "Zerado"
  is filled.
- `homonimo`, `gestor_tp`, `faec_tp`, `cid_notif`: rows per published value.
- `cid_notif|proc_rea`, `cid_notif|sexo`: rows with `cid_notif` filled, by value and by
  `proc_rea` or `sexo`.
- `tpdisec1` to `tpdisec9`: rows per value, split by whether the `diagsec` of the same
  number is filled.
- `uf_zi_em_faixa`: rows whose `uf_zi` falls in one of the ranges `br_municgestor.cnv`
  writes (334501-334530, 358001-358058, 530000-530009, 530011-539999).

## What the counts show

- **The 19 "Zerado" fields.** From 2008 none is filled in any of the 1,994,690 records.
  In 2006 and 2007 most are: `val_sadt` in 41,405 of the 41,547 records, `tot_pt_sp` in
  40,968, `rubrica` in 36,983, `val_obsang` in 11,513, `val_ped1ac` in 10,456. Five are
  filled in fewer than 500 records (`uti_mes_in`, `uti_mes_an`, `uti_mes_al`,
  `val_sadtsr`, `cpf_aut`) and five in none (`uti_int_in`, `uti_int_an`, `uti_int_al`,
  `val_ortp`, `val_transp`) in these Roraima files.
- **`homonimo`.** `0` and `2` in every year from 2006 to 2026: 40,242 and 1,305 records
  in 2006-2007, 1,922,238 and 72,418 from 2008. `1` appears in one file, `RDAP2607` (34
  records). The files of 2006-04 to 2007-12, which have the layout `Layout_REDUZIDA.pdf`
  describes ("0 = não , 1 = sim"), publish `2` and no `1`.
- **`tpdisec1-9`.** The 12 files of 2014 publish the nine fields blank, with the
  `diagsec` blank too. The 148 files from 2015-01 publish `0`, `1` or `2`, never blank:
  `0` in 11,710,387 field values, every one with the `diagsec` of the same number blank,
  and `1` or `2` in 491,462, every one with it filled.
- **`cid_notif`.** Filled in 28,388 of the 1,994,690 records from 2008: `Z302` in
  28,207, a code that begins with `O` in 172, and other values in 9 (`302`, `Z310`, `Z3Z0`, `ZZ30`,
  `Z320`). Of the `Z302` records, 22,157 have `sexo` 3 and 6,050 have `sexo` 1.
- **`faec_tp`.** 32 distinct codes in 57,820 filled records, all among the 100 codes
  `TP_FINAN.CNV` lists one by one.
- **`uf_zi`.** Every record of the five `RDDF` files (76,276) has `530000`, a code
  `br_municgestor.cnv` reaches only through the range `530000-530009` of the line
  "530000 Distrito Federal". No file has a code of the other three ranges.

## What they do not show

One UF a month (Roraima, a small one), plus three UFs in five Januaries: a code that
another UF publishes in another month is not here. The counts say what the files hold,
not what a value means: that `0` goes with a blank diagnosis does not make a document
call it so.
