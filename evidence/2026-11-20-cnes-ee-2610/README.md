# CNES EE: one file of 2026-10 after six years without one

Read on 2026-11-20 from `ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/EE/`.

The listing has 3,202 files, `EE<UF><AAMM>.dbc` from 2007-03 to 2026-10. From 2020 on it has
two, each the only file of its month:

| File | Server time | Bytes | SHA-256 | Records |
| --- | --- | ---: | --- | ---: |
| `EEMG2107.dbc` | 2021-08-18 11:10 | 1,035 | `e897ac372c8b353886f99bd23d0da42a0da97d1c564ed4caf5b62fa086b5d927` | 0 |
| `EESP2610.dbc` | 2026-11-17 14:57 | 1,140 | `9d402301e56a4e4cacb8b88fcfec4b532a2cf02a11643f54cdff8ec45f12dc5a` | 1 |

Both have the 31 fields of `EESP1912.dbc` (2020-08-24 09:48, 2,699 bytes, SHA-256
`33fe4d06e88e877c07accea486a35127294320a7b83a5637dca8805a399f4890`, 50 records), the last
month with files for many UFs. The record of `EESP2610` has `COMPETEN` 202610, `CODUFMUN`
355710, `PF_PJ` 3, `CMPT_INI` 202605 and `CMPT_FIM` 999999; no other field was read.

So the registry row `cnes_estabelecimentos_ensino` ends its coverage at 2026-10
(`src/omnisus/sources/datasus_ftp/datasets.py`). The weekly probe
(`tests/integration/test_registry_probe.py::test_coverage_end_is_not_a_stale_claim`) had
failed against 2021-07. Whether DATASUS resumes the monthly series is not known; a file
listed later fails the same probe again.

The downloaded files are not committed.
