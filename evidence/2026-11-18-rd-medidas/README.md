# RD files: counts that bear on decisions of #182

Counts taken on 2026-11-18 from `RD*.dbc` files of
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/`, so that statements about a few
fields rest on more than one fixture. `medir.py` wrote the four CSV files:

    uv run --locked python evidence/2026-11-18-rd-medidas/medir.py \
        sih_aih_reduzida DIR_2008 evidence/2026-11-18-rd-medidas/2008-2026
    uv run --locked python evidence/2026-11-18-rd-medidas/medir.py \
        sih_aih_reduzida_1992_2007 DIR_2006 evidence/2026-11-18-rd-medidas/2006-2007

Each directory has `arquivos.csv` (file, bytes, SHA-256, records) and `medidas.csv`
(file, measure, key, rows). Only counts leave the files. A count of 1 is one
hospitalisation's value of that field in that file (a UF and a month). The decoder
loads every column, but no measure uses `GESTOR_CPF`, and `CPF_AUT` is only counted as
filled or not.

| Directory | Server directory | Files | Records |
|---|---|---:|---:|
| `2008-2026` | `200801_/Dados` | 238 | 1,994,690 |
| `2006-2007` | `199201_200712/Dados` | 24 | 41,547 |

- `2008-2026`: `RDRR` of every month from 2008-01 to 2026-06 (222 files, Roraima),
  `RDAP2607`, and `RDDF`, `RDRJ` and `RDSP` of January 2008, 2012, 2016, 2020 and 2024.
  224 of the files are in `evidence/2026-10-06-rd-2008-layouts/census.csv`; 213 have the
  SHA-256 recorded there on 2026-10-06, and the 11 from 2025-09 on have another. The
  other 14 (`RDDF`, `RDRJ` and four `RDSP`) have their SHA-256 only here.
- `2006-2007`: `RDRR` of every month of 2006 and 2007, each with the SHA-256 recorded in
  `evidence/2026-10-01-rd-1992-2007-layouts/census.csv`: 3 files of layout 18 (2006-01
  to 2006-03, 4,564 records) and 21 of layout 19 (2006-04 to 2007-12, 36,983 records).

The measures (`medida`), with a field counted as filled when it is neither blank nor
zero (text made only of zeros is zero); a field a file does not have gets no row:

- `zerado_preenchido`: rows where each of the 19 fields `IT_SIHSUS_1603` calls "Zerado"
  is filled.
- `homonimo`, `faec_tp`, `cid_notif`: rows per published value.
- `tpdisec1` to `tpdisec9`: rows per value, split by whether the `diagsec` of the same
  number is filled.
- `uf_zi_em_faixa`: rows whose `uf_zi` falls in one of the ranges `br_municgestor.cnv`
  writes (334501-334530, 358001-358058, 530000-530009, 530011-539999).

## What the counts show

- **The 19 "Zerado" fields.** From 2008 none is filled in any of the 1,994,690 records.
  In the 21 files of layout 19, the layout `Layout_REDUZIDA.pdf` describes, 13 are:
  `rubrica` and `tot_pt_sp` in all 36,983 records, `val_sadt` in 36,858, `val_obsang` in
  10,161, `val_ped1ac` in 9,108, `val_rn` in 5,806, `val_acomp` in 4,118, `val_sangue`
  in 3,461, and five in fewer than 500 (`val_sadtsr`, `uti_mes_al`, `cpf_aut`,
  `uti_mes_in`, `uti_mes_an`). Six are filled in none of those records: `uti_int_in`,
  `uti_int_an`, `uti_int_al`, `val_ortp`, `val_transp` and `num_proc`. `num_proc` is
  filled in all 4,564 records of the three files of layout 18, which have no `rubrica`.
- **`homonimo`.** `0` and `2` in the files of every year from 2006 to 2026: 40,242 and
  1,305 records in 2006-2007, 1,922,238 and 72,418 from 2008. `1` appears in one file,
  `RDAP2607` (34 records). Each of the 21 files of layout 19, the layout
  `Layout_REDUZIDA.pdf` describes with "0 = não , 1 = sim", publishes `2` and no `1`.
- **`tpdisec1-9`.** The 12 files of 2014, all of Roraima, publish the nine fields blank,
  with the `diagsec` blank too. The 148 files from 2015-01 never publish them blank: `0`
  in 11,710,387 field values, every one with the `diagsec` of the same number blank, and
  `1` or `2` in 491,462, every one with it filled. `tpdisec8` and `tpdisec9` are `0` in
  every record of those files, and `diagsec8` and `diagsec9` are never filled.
- **`cid_notif`.** Filled in 28,388 of the 1,994,690 records from 2008: `Z302` in
  28,207, a code that begins with `O` in 172, and other values in 9 (`302`, `Z310`,
  `Z3Z0`, `ZZ30`, `Z320`). In 2006-2007: `0000` in 41,081 records, blank in 143, `Z302`
  in 323.
- **`faec_tp`.** 32 distinct codes in 57,820 filled records. All are among the 100
  codes that `CNV/TP_FINAN.CNV` of `TAB_SIH.zip` (`sih-tab-21e42384645a`; member SHA-256
  `f6986095b663c4a22b69e027c582b7094c56c40abaf26a8183206531d9336683`) lists one by one.
  That member is not packaged, so no test repeats the comparison.
- **`uf_zi`.** Every record of the five `RDDF` files (76,276) has `530000`, a code
  `br_municgestor.cnv` reaches only through the range `530000-530009` of the line
  "530000 Distrito Federal". No file read has a code of the other three ranges.

## What they do not show

- 222 of the 238 files from 2008, and all 24 of 2006-2007, are of Roraima, a small UF.
  Three other UFs enter in five Januaries. A code another UF publishes in another month
  is not here; "the 12 files of 2014" are 12 Roraima files.
- Only RD files were read: nothing here is about the files of the rejected AIH (`RJ`).
- The counts say what the files hold, not what a value means: that `0` goes with a
  blank diagnosis does not make a document of the RD call it so.

**What it is used for.** The issues of the fields in `sih_aih_reduzida.yaml`
(`rotulo-do-layout-ate-2007`, `homonimo-sem-fonte`, `tpdisec-0-sem-fonte`,
`cid_notif-laqueadura-no-def`, `uf_zi-faixa-em-codigo-longo`) and the last one in
`sih_aih_rejeitada.yaml` quote these numbers, and
`tests/unit/transforms/test_sih_rd_measures.py` sums the CSV files and compares.
