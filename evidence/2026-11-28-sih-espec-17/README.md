# SIH: `espec` 17 in the RD and RJ files of São Paulo

Counts taken on 2026-11-28 from 29 files of
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/`, downloaded that day,
before giving code `17` of `espec` a label in `sih_aih_reduzida` and `sih_aih_rejeitada`
(issue #254, decision 4). `medir.py` wrote `medidas.json`:

    uv run --locked python -I evidence/2026-11-28-sih-espec-17/medir.py \
        DIR evidence/2026-11-28-sih-espec-17/medidas.json

The files: `RDSP` of every month from 2020-01 to 2022-02 (26 files, 5,032,418 AIH,
390,479,686 bytes) and `RJSP` of 2022-01, 2022-02 and 2022-03 (3 files, 30,454 AIH,
1,893,258 bytes). The script reads the DBF records directly
(`omnisus.sources.datasus_ftp.dbc.decompress_bytes`), so the values are the published
text. `RDSP2201.dbc` and `RJSP2203.dbc` have the SHA-256 that `tests/fixtures/FIXTURES.md`
records for the two excerpts cut from them, and `RDSP2001.dbc` the one recorded in
`evidence/2026-11-24-rd-sp-uti-cid-raca/`.

## Where the code comes from

`CNV/LEITOS.CNV`, the member of `TAB_SIH.zip` that `RD2008.DEF` (line 229) and
`RJ2008.DEF` (line 233) bind to `ESPEC`, lists 41 codes and no `17` (packaged member,
SHA-256 `040504bd1af5aae1e28d9384abad44dcece26d03b1886a5d6ccd578da93f0eda`). Portaria SAES/MS nº 245/2020,
art. 2º (`sihsus-80babfa3a197` in
`src/omnisus/data/dicionarios/sources/registry.json`), adds "o código 17 - Estabelecimento
Exclusivo UTI SUS" to the AIH speciality table. The ordinance was not read again on
2026-11-28: its words here are the ones the issue `espec-17-sem-fonte` of the two
dictionaries transcribed from the registered file, retrieved on 2026-11-24.

## What the counts show

- **SP 2022, the counts the issue gave.** Confirmed: 36 rows in the RD (`RDSP2201` 23,
  `RDSP2202` 13) and 75 in the RJ (`RJSP2201` 6, `RJSP2202` 20, `RJSP2203` 49).
- **Procedure and UTI type.** Every row with `ESPEC` 17, in the 29 files, has `PROC_REA`
  `0303010223` and `MARCA_UTI` `51`: 1,963 rows in the RD and 75 in the RJ.
- **When it appears.** No row has 17 in `RDSP` from 2020-01 to 2020-06. The first file with
  it is `RDSP2007` (75 rows). By year of the file name: 692 rows in 2020, 1,235 in 2021 and
  36 in the two months of 2022. The month with most rows is 2020-12 (292).
- **Establishments.** The RD rows come from 5 distinct `CNES` over the 26 files (at most 5
  in one file, `RDSP2105`), the RJ rows from 2.
- **Other codes.** `17` is the only value of `ESPEC` in these files that `LEITOS.CNV` does
  not list.

What this does not settle: the other UFs, the RD after 2022-02, and the RJ outside the
three months read.

## Files

| File | SHA-256 | Bytes | AIH | ESPEC 17 | PROC_REA of those rows | MARCA_UTI of those rows | Distinct CNES |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: |
| RDSP2001.dbc | `ea611bb554aa00062c8aee2c3041d3065b2635938cdd32d6ce6636cb91436478` | 17083017 | 215766 | 0 | none | none | 0 |
| RDSP2002.dbc | `78e3493a21d52b6ec5dbb9b02869667b579bcdbccf1e8f1c5d178eb229a00678` | 15807732 | 205588 | 0 | none | none | 0 |
| RDSP2003.dbc | `a19bd181d39674213ee5a4238fe950ee486a9bf8df7e0bc990740aabdf68c417` | 16136638 | 208684 | 0 | none | none | 0 |
| RDSP2004.dbc | `00511f50e3bcfd6e86724a50d60e9013aea190e1f3f52fa2af86371b95c47aa3` | 12311769 | 158154 | 0 | none | none | 0 |
| RDSP2005.dbc | `f2c21020ea246a53039f899b13bc4465d67737d837c519b393cfa0f22b1bc94f` | 12616169 | 163154 | 0 | none | none | 0 |
| RDSP2006.dbc | `ad036b4872637ef9e0613a3ac1bebcce6ef5696c9919fd50dda63da6afb9f3a8` | 13217058 | 172034 | 0 | none | none | 0 |
| RDSP2007.dbc | `8adcc84f3cff9fdca5510ff02fcfaa6a1cb30e5d76139256af428e861ddd6a17` | 14415177 | 186658 | 75 | `0303010223` 75 | `51` 75 | 3 |
| RDSP2008.dbc | `a46690ce47cdce0f97b3eae98a524645c1e7c2cdd8d1c7cc6433fb0cfe8c4385` | 14271920 | 184527 | 52 | `0303010223` 52 | `51` 52 | 2 |
| RDSP2009.dbc | `6704c2ad52186cab31903bea91301d7a4bf2783f5be2dda14981af925bcec7a9` | 14856531 | 190926 | 109 | `0303010223` 109 | `51` 109 | 2 |
| RDSP2010.dbc | `47960b7bef955ddaceb9a678e9233ec24eba7a467fb99482ea6d12eb49c3f03b` | 15268036 | 196014 | 72 | `0303010223` 72 | `51` 72 | 2 |
| RDSP2011.dbc | `af54813ccc1ee57cb05a2d676f390f26f4719534bf34cdad25f84901245aa715` | 15181331 | 195262 | 92 | `0303010223` 92 | `51` 92 | 2 |
| RDSP2012.dbc | `beb0372a2615932adcaf15e809216cc85497ab0a4e5526fd5f175d88a704d125` | 14609333 | 188128 | 292 | `0303010223` 292 | `51` 292 | 1 |
| RDSP2101.dbc | `226547f04f23b9f18db84b402bcd02b66c47f37ebf366d534ad63abe5c5e7f3c` | 15281896 | 195978 | 146 | `0303010223` 146 | `51` 146 | 1 |
| RDSP2102.dbc | `c679e2a82871de03fc946682fc34ba5e6f25354f1237ac0248a01da006306291` | 14730967 | 191120 | 113 | `0303010223` 113 | `51` 113 | 1 |
| RDSP2103.dbc | `f631714d40a47ab461d9e1d219ae05e51e176d929a5c018f1083cd45de163d2b` | 15251695 | 199489 | 87 | `0303010223` 87 | `51` 87 | 1 |
| RDSP2104.dbc | `3d1586db27ae09be6dfe7e541774a4692998bc2dc9ebd051ddab40a4a03ffbdf` | 14650762 | 192501 | 188 | `0303010223` 188 | `51` 188 | 3 |
| RDSP2105.dbc | `aa7447a8686b7c24ad699b181bce7225cc5a6ae6b15530d87c68e8258330bfd4` | 15374265 | 202051 | 150 | `0303010223` 150 | `51` 150 | 5 |
| RDSP2106.dbc | `7e42253f6676ccc70d58ca89ce30912f0356a98deaf2ccb25d3f4b742a9d619b` | 15398229 | 201017 | 204 | `0303010223` 204 | `51` 204 | 4 |
| RDSP2107.dbc | `429bc327419e28e73728558adf8f83007cc14f7b69bf49a82da6c5662f24cab7` | 15651610 | 200591 | 156 | `0303010223` 156 | `51` 156 | 4 |
| RDSP2108.dbc | `cf6a9cf0cfeb508aa4e467f892bbdd4aad3a21ea6ce8206ba8cb04471256070e` | 15748366 | 201312 | 87 | `0303010223` 87 | `51` 87 | 2 |
| RDSP2109.dbc | `1bebbd6a2a72146df2c1465040a63ebe49bd8cc936322e6d29f3c38ac380d59d` | 15398983 | 196878 | 58 | `0303010223` 58 | `51` 58 | 3 |
| RDSP2110.dbc | `39e252c49cff03f25b1f131b2249070cfabc78ae42fe0843f9f5c453fadc23de` | 15324314 | 195013 | 27 | `0303010223` 27 | `51` 27 | 3 |
| RDSP2111.dbc | `acf6a9bb25509cb2de0bc494ba29bb9afb642de966cda8f1432d7ad7dda7b938` | 15326784 | 197590 | 15 | `0303010223` 15 | `51` 15 | 3 |
| RDSP2112.dbc | `7f96f44bd8188eb0f7c3924149830449789343487322c03872c10ad88569317d` | 15969903 | 203150 | 4 | `0303010223` 4 | `51` 4 | 1 |
| RDSP2201.dbc | `8ae4e3a106dbdd27e7c1a75591f4f692255364d8238044451fb00b7d85346c68` | 15549230 | 199070 | 23 | `0303010223` 23 | `51` 23 | 1 |
| RDSP2202.dbc | `adde15599eb92152b61316c86122d4e0f3fa9580dff02a51bd4cec4ccc04d335` | 15047971 | 191763 | 13 | `0303010223` 13 | `51` 13 | 1 |
| RJSP2201.dbc | `2ea4a600fec594ce4dfb00075e5ae29a72b378b3375946c3b74c8ff50b76c241` | 621582 | 9912 | 6 | `0303010223` 6 | `51` 6 | 2 |
| RJSP2202.dbc | `cadf30eec97f970949f63522171143cbd87f6c0101abaa2f44e1a2d95894d060` | 599573 | 9594 | 20 | `0303010223` 20 | `51` 20 | 1 |
| RJSP2203.dbc | `f85760f7cf7befa7507266736e5ae5bda02b9b92cf5a7a020db30dc4e2873100` | 672103 | 10948 | 49 | `0303010223` 49 | `51` 49 | 2 |
