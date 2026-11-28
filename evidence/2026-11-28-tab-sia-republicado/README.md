# TAB_SIA.zip republished on 2026-11-24: no packaged member changed

`TAB_SIA.zip` at `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Auxiliar/`
was downloaded on 2026-11-28: 74,143,727 bytes, server time
`Wed, 25 Nov 2026 00:06:56 GMT` (2026-11-24 21:06 in Brasília; the directory listing
shows `11-24-26  09:06PM`), SHA-256
`5e145464db62dc80b6727ea0569780444fdafeb395ef1eae7f70f3d1b90b710e`. It is
`sia-tab-5e145464db62` in `registry.json`, the third edition of this URL after
`sia-tab-e5812b51d802` (2026-09-21) and `sia-tab-1ce232b217c6` (2026-11-18). It was
republished the same day as `TAB_SIH.zip` (`evidence/2026-11-28-tab-sih-republicado/`).

`members.csv` has one row per member (`census.py` wrote it from the zip: path, size,
SHA-256, the date stored in the zip) and, for each hash the repository already holds of
that member, the hash and its source:
`evidence/2026-11-18-tab-sia-republicado/members.csv` for every member of
`sia-tab-1ce232b217c6`, and `vinculos.json` for the members packaged from
`sia-tab-e5812b51d802`. A member held under both has two rows.

- 877 members, the same paths as in `sia-tab-1ce232b217c6` (none added, none removed):
  791 `CNV/`, 72 `DBF/`, 1 `Docs/` and 13 `.DEF`/`.def` at the root.
- 876 of the 877 carry the date 2026-11-24 inside the zip, so the whole archive was
  rewritten that day; `CNV/ap_regsaud.cnv.bak` is dated 2026-04-20, as in the previous
  edition.
- **926 recorded hashes compared, 896 equal.** Against `sia-tab-1ce232b217c6`, 847 of the
  877 members are equal and 30 differ. The 49 hashes `vinculos.json` holds from
  `sia-tab-e5812b51d802` (12 DEF files and 37 CNV) are all equal.
- **The 30 members that differ are all in `DBF/`:** `CBO.dbf`, `TB_SIGTAW.dbf` and the 28
  `CADGER??.dbf` (the 27 UFs and `BR`). 29 of them changed size; `CBO.dbf` kept it. The
  other 42 `DBF/` members, the 791 `CNV/`, the `Docs/` member and the 13 DEF files are
  byte-identical.
- **None of the 30 is packaged.** `vinculos.json` lists 53 members of this URL: the 49
  above and `APAC_Dados_Comuns.DEF`, `CNV/TIPOPRES.CNV`, `CNV/UFNACIO.CNV` and
  `CNV/natjurc.cnv` from `sia-tab-1ce232b217c6`. All 53 are identical in the new zip.
- `DBF/CBO.dbf` and `DBF/TB_SIGTAW.dbf` have the same SHA-256 here and in the
  `TAB_SIH.zip` of the same day (`evidence/2026-11-28-tab-sih-republicado/members.csv`),
  as they had in the editions of 2026-10-15.

**What this settles.** Nothing `vinculos.json` packages changed in the republication: no
CNV and no DEF changed at all. So `vinculos.json` stays on `sia-tab-e5812b51d802` and
`sia-tab-1ce232b217c6`, no decode map is regenerated and no dictionary moves to the new
edition. The new edition is registered so a later pull request can cite it.

**What it does not settle.** What changed inside the 30 DBF files: the repository keeps
no copy of `sia-tab-1ce232b217c6`, only its member hashes and sizes, and the server now
returns the new edition, so the rows could not be compared. `Producao_Ambulatorial.DEF`
links `DBF/TB_SIGTAW.DBF` to `PA_PROC_ID`, `DBF/CBO.DBF` to `PA_CBOCOD` and the
`DBF/CADGER??.DBF` files to `PA_CODUNI`; `vinculos.json` packages none of them. Whoever
packages one of the 30 cites it from the new edition and reads it again.
