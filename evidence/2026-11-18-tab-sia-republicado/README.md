# TAB_SIA.zip republished on 2026-10-15: no packaged member changed (#183)

`TAB_SIA.zip` at `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Auxiliar/`
was read on 2026-11-18: 73,814,622 bytes, server time `Fri, 16 Oct 2026 01:09:17 GMT`
(2026-10-15 22:09 in Brasília), SHA-256
`1ce232b217c6e9bfd53ad5ceb7a42b6c01f7cd8686a29b3e8b828e88e944e119`. It is
`sia-tab-1ce232b217c6` in `registry.json`, the second edition of this URL the registry
holds, after `sia-tab-e5812b51d802` (retrieved on 2026-09-21, 73,356,937 bytes). It was republished the same day as
`TAB_SIH.zip` (`evidence/2026-11-15-tab-sih-republicado/`).

`members.csv` has one row per member (`census.py` wrote it from the zip: path, size,
SHA-256, the date stored in the zip) and, for each member `vinculos.json` holds a hash
of, that hash and its source.

- 877 members: 791 `CNV/`, 72 `DBF/`, 1 `Docs/` and 13 `.DEF`/`.def` at the root.
- 876 of the 877 carry the date 2026-10-15 inside the zip, the day of the server time
  above; `CNV/ap_regsaud.cnv.bak` is dated 2026-04-20.
- **49 recorded hashes compared, 49 equal.** They are every member `vinculos.json` lists
  from `sia-tab-e5812b51d802`: 12 DEF files and 37 CNV, 5 of which have no file of their
  own (`mesmo_que`). None is absent from the new zip.
- The root has a 13th DEF, `APAC_Dados_Comuns.DEF`, which the repository does not package.

**What this settles.** Nothing `vinculos.json` packaged on 2026-11-18 changed in the
republication, so those 49 members stay on `sia-tab-e5812b51d802`. The new edition is registered so a later pull request can cite it.

**What it does not settle.** The 828 members the repository held no hash of on
2026-11-18 were not compared: the repository has no copy of `sia-tab-e5812b51d802`, and
the server now returns the new edition. A CNV or DBF that nothing packaged then may
differ from the edition retrieved on 2026-09-21. Whoever packages one of them cites it from the new edition and reads it again.
