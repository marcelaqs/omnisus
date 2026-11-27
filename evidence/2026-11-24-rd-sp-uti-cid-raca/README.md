# RD SP: counts for the SIH notes of 2026-11-24

Counts taken on 2026-11-24 from seven `RDSP*.dbc` files of
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/`, downloaded that day,
so that several notes of `docs/sources/sih_aih_reduzida.md` rest on more than the Roraima
fixture. `medir.py` wrote `medidas.json`:

    uv run --locked python evidence/2026-11-24-rd-sp-uti-cid-raca/medir.py \
        DIR evidence/2026-11-24-rd-sp-uti-cid-raca/medidas.json

| File | SHA-256 | Bytes |
| --- | --- | --- |
| RDSP1412.dbc | `c744f524f7a98dc02b30aef346d0efa693dc00d5baeb29a47e378876b808c3ec` | 14214477 |
| RDSP1502.dbc | `8011928ad0cb9119ba6ef1c95df8471a44e52a70855624810b3c30ae79b5e8b6` | 14899189 |
| RDSP1902.dbc | `4653fb8f96fefacfb3a47f8f7fc1b1d1591c56be0c9800fbe0fcddf82dc254a0` | 15690982 |
| RDSP2001.dbc | `ea611bb554aa00062c8aee2c3041d3065b2635938cdd32d6ce6636cb91436478` | 17083017 |
| RDSP2303.dbc | `e6c920afdb0f432f93724893a731b22cb9303c2bed8a3342ed0c161f2e600b6b` | 18077745 |
| RDSP2306.dbc | `e9507c7429b4dc8990639b90b70e2ea38d42547dde7594cf1f327aae8587a95b` | 18001348 |
| RDSP2512.dbc | `976373cd79219b8287dcb3815f5a7b7b85c40ce542dce903e44591bc05159aa5` | 18300555 |

| File | AIH | marca_uti 74 | 77 | uti_int_to > 0 | of which marca_uti 00 | deaths | deaths with a CID in cid_morte | raca_cor 99 | latest dt_inter with 99 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RDSP1412 | 193789 | 423 | 14 | 485 | 223 | 8801 | 8801 | 32488 | 20141231 |
| RDSP1502 | 195822 | 405 | 7 | 472 | 263 | 9135 | 0 | 34296 | 20150228 |
| RDSP1902 | 203599 | 272 | 4 | 1328 | 757 | 9701 | 0 | 27160 | 20190228 |
| RDSP2001 | 215766 | 254 | 2 | 1770 | 1068 | 11045 | 0 | 27436 | 20200131 |
| RDSP2303 | 233649 | 130 | 0 | 2147 | 1281 | 11363 | 0 | 4778 | 20230331 |
| RDSP2306 | 232263 | 121 | 7 | 2015 | 1170 | 12420 | 0 | 282 | 20230331 |
| RDSP2512 | 230747 | 29 | 0 | 1926 | 1103 | 11597 | 0 | 97 | 20221125 |

From RDSP1502 on, `cid_morte` and `cid_asso` are `0000` in every row; in RDSP1412,
`cid_morte` is blank outside the deaths. No file has `uti_mes_to` 999.

The same files, for the other notes of the page:

- `sexo` is only `1` or `3` in all seven.
- `cobranca` 65, 66 and 67 always come with `morte` 1, and 61 to 64 with `morte` 0
  (`cobranca_61_67_by_morte`; for example RDSP2303: 65/1 3, 66/1 2, 67/1 1).
- The fifth digit of `n_aih` does not give the type of AIH: every AIH with `ident` 5 has
  the digit 1, and AIH with `ident` 1 have 1, 3 or 5 (`n_aih_digit5_by_ident`; RDSP2512:
  1/1 221408, 1/5 4488, 3/1 14, 5/1 4837).
- With `diag_princ` of chapter XIX (S or T), `diagsec1` holds a code of V to Y in 18320 of
  18321 AIH in RDSP1502 and 25556 of 25840 in RDSP2512; in RDSP1412, before the
  `diagsec` fields were filled, in none.
- `etnia` is `0000` in every AIH whose `raca_cor` is not 05; of the AIH with 05, a few
  carry `0000` (3 of 24 in RDSP1902, 6 of 35 in RDSP2001, none in RDSP1412 and RDSP2512).
- Of the AIH with `cobranca` 61 to 67 (parto), `diar_acom` is above zero in 9499 of 26207
  in RDSP1412 and 13909 of 20855 in RDSP2512 (`cobranca_61_67_diar_acom_gt0`).
- Every AIH with `uti_int_to` above zero is of a patient under one year (`cod_idade` 2
  or 3) and has `marca_uci` 01, 02 or 03 (1926 of 1926 in RDSP2512).
- `car_int` 03 to 06 come only with a `diag_princ` of S or T (2588 of 2588 in RDSP2512),
  but most AIH with S or T have `car_int` 01 or 02 (23252 of 25840 in RDSP2512).
- `dias_perm` equals `dt_saida` minus `dt_inter` in 226276 of 230747 AIH in RDSP2512.
  `qt_diarias` is `dias_perm` plus one in most AIH with `cobranca` 3x (transfer, 8659 of
  9869) and 4x (death, 6877 of 11595), and equals `dias_perm` in most with 1x (discharge,
  131170 of 170082) and 6x (parto, 20569 of 20855)
  (`qt_diarias_vs_dias_perm_by_cobranca_first_digit`).
