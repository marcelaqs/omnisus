# TAB_SIH.zip republished on 2026-11-24: no packaged member changed (#255)

`TAB_SIH.zip` at `ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Auxiliar/`
was read on 2026-11-27 and downloaded again on 2026-11-28, with the same bytes both
days: 6,085,117 bytes, server time `Wed, 25 Nov 2026 00:11:46 GMT` (2026-11-24 21:11 in
Brasília), SHA-256
`2491e8d4f2db2cc2963006a589157cd55015ad26c2d8eaf8666320f98fcd9bef`. It is
`sih-tab-2491e8d4f2db` in `registry.json`, the fourth edition of this URL after
`sih-tab-714ed980d483` (2026-09-14), `sih-tab-f05b32f32908` (2026-09-21) and
`sih-tab-21e42384645a` (2026-11-15). The first read is the one
`evidence/2026-11-28-rd-uti-mes-to-regct/README.md` cites.

`members.csv` has one row per member (`census.py` wrote it from the zip downloaded on
2026-11-28: path, size, SHA-256, the date stored in the zip) and, for each hash the
repository already holds of that member, the hash and its source:
`evidence/2026-11-15-tab-sih-republicado/members.csv` for every member of
`sih-tab-21e42384645a`, and `vinculos.json` for the members packaged from
`sih-tab-f05b32f32908`. A member held under both has two rows.

- 885 members, the same paths as in `sih-tab-21e42384645a` (none added, none removed):
  797 `CNV/`, 81 `DBF/`, 3 `Docs/` and 4 at the root (`RD2008.DEF`, `RJ2008.DEF`,
  `SP2008.DEF`, `Motivo_de_Erro.DEF`).
- 882 of the 885 carry the date 2026-11-24 inside the zip, so the whole archive was
  rewritten that day; two are dated 2026-06-16 and one 2026-02-19, as in the previous
  edition.
- **916 recorded hashes compared, 858 equal.** Against `sih-tab-21e42384645a`, 827 of the
  885 members are equal and 58 differ. The 31 hashes `vinculos.json` holds from
  `sih-tab-f05b32f32908` (the four DEF files, 26 CNV and `DBF/MOTERRO.dbf`) are all equal.
- **The 58 members that differ are all in `DBF/`:** `CBO.dbf`, `TB_SIGTAW.dbf`, the 28
  `TCH??.dbf` and the 28 `TCNES??.dbf` (the 27 UFs and `BR` of each). 23 of them changed
  size and 35 kept it. The other 23 `DBF/` members, the 797 `CNV/`, the 3 `Docs/` and the
  4 DEF files are byte-identical.
- **None of the 58 is packaged.** `vinculos.json` lists 33 members of this URL: the 31
  above and `CNV/TP_FINAN.CNV` and `CNV/br_municgestor.cnv` from `sih-tab-21e42384645a`.
  All 33 are identical in the new zip.

**What this settles.** Nothing `vinculos.json` packages changed in the republication: no
CNV and no DEF changed at all. So `vinculos.json` stays on `sih-tab-f05b32f32908` and
`sih-tab-21e42384645a`, no decode map is regenerated and no dictionary moves to the new
edition. The new edition is registered so a later pull request can cite it.

**What it does not settle.**

- What changed inside the 58 DBF files: the repository keeps no copy of
  `sih-tab-21e42384645a`, only its member hashes and sizes, and the server now returns
  the new edition, so the rows could not be compared. `RD2008.DEF` links
  `DBF\TB_SIGTAW.DBF` to the procedure fields and `DBF\TCHBR.DBF` to `CGC_HOSP` (the
  lines quoted in `sih_aih_reduzida.yaml`); `vinculos.json` packages neither. Whoever
  packages one of the 58 cites it from the new edition and reads it again.
- `TAB_SIA.zip`. In the edition of 2026-10-15, `DBF/CBO.dbf` and `DBF/TB_SIGTAW.dbf` had
  the same SHA-256 in both zips (`evidence/2026-11-18-tab-sia-republicado/members.csv`).
  On 2026-11-28 the server lists `SIASUS/200801_/Auxiliar/TAB_SIA.zip` with 74,143,727
  bytes and the date `11-24-26 09:06PM`, while `sia-tab-1ce232b217c6` has 73,814,622. That
  zip was not read here.
