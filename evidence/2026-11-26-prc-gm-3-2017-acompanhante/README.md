# Where the rule behind `diar_acom` lives today (Portaria de Consolidação GM/MS nº 3/2017, art. 92)

`docs/sources/sih_aih_reduzida.md` cites Portaria GM/MS nº 2.418/2005 for the
companion of the woman in labour, whose daily rates `diar_acom` counts. That ordinance
is now art. 92 of the Portaria de Consolidação GM/MS nº 3, de 28 de setembro de 2017,
compiled text on Saúde Legis:
`https://bvsms.saude.gov.br/bvs/saudelegis/gm/2017/prc0003_03_10_2017_comp.html`.

The page was not read from this repository's tooling. It was printed to PDF from a
browser on 2026-11-24 (370 pages, header "24/11/2026, 15:47") and that PDF was read
here on 2026-11-26:

| File | Bytes | SHA-256 |
|---|---:|---|
| `PORTARIA DE CONSOLIDAÇÃO Nº 3.pdf` (browser print of the page above) | 12,101,375 | `24daf3e418e50fd75fa242a8f3f6c03c55699d3155b817d2c2a61c9a8c9753d8` |

What the print says, in the order of the text (Título V, art. 92):

- The title is "Do acompanhamento durante o trabalho de parto, parto e pós-parto
  imediato e em consultas, procedimentos e exames", "Redação dada pela PRT GM/MS
  n° 5.350 de 12.09.2024".
- The caput regulates, "em conformidade com a Lei nº 11.108, de 7 de abril de 2005, e a
  Lei nº 14.737, de 27 de novembro de 2023", the companion "durante a admissão,
  internação e alta, assim como em consultas, exames e procedimentos" (same redação).
- § 1º to § 3º have "Origem: PRT MS/GM 2418/2005, Art. 1º, § 1º" to "§ 3º" and are marked
  "Repristinado pela PRT GM/MS nº 13 de 13.01.2023". § 2º keeps the text the docs quote:
  "Fica autorizada ao prestador de serviços a cobrança, de acordo com as tabelas do SUS,
  das despesas previstas com acompanhante no trabalho de parto, parto e pós-parto
  imediato, cabendo ao gestor a devida formalização dessa autorização de cobrança na
  Autorização de Internação Hospitalar (AIH)."

The print is a browser rendering, not the bytes the server sends, so it does not go to
`sources/registry.json`; the hash identifies the copy that was read.
