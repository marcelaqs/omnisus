# RD: four measures left open by the review of `sih_aih_reduzida`

Counts taken on 2026-11-28 from 114 `RD*.dbc` files of
`ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/`, the same files as
`evidence/2026-11-28-rd-uti-mes-to-regct/` (same SHA-256 and bytes, listed again below):
the 27 UFs of 2008-01, 2012-01, 2016-01 and 2025-12, and `RDSP` of 2014-12, 2015-02,
2019-02, 2020-01, 2023-03 and 2023-06. In all, 4,939,510 AIH and 359,203,926 bytes. The
review had seen four things in the raw files without recording them; `medir.py` records
them in `medidas.json`:

    uv run --locked python evidence/2026-11-28-rd-medidas-da-revisao/medir.py \
        DIR evidence/2026-11-28-rd-medidas-da-revisao/medidas.json

The script reads each file with the repository reader
(`omnisus.sources.datasus_ftp.parse.dbc_bytes_to_lazyframe`, dataset `sih_aih_reduzida`),
so text fields come without the padding spaces and a blank field is an empty string. Two
runs wrote the same bytes. Measure (c) covers the 114 files; (a), (b), (d) and the blank
diagnoses cover the seven `RDSP` files of `evidence/2026-11-24-rd-sp-uti-cid-raca/`
("the seven São Paulo files" below).

## (a) `raca_cor` 99 after the announcement of April 2023

Key `raca_cor_99` of each São Paulo file.

- No AIH with `dt_inter` from 2023-04-01 on has `raca_cor` 99 in any of the seven files
  (`dt_inter_from_2023_04_01` is 0 in all); only `RDSP2306` and `RDSP2512` are of a later
  competence, so only they can hold such AIH.
- `RDSP2306`: 282 AIH with 99, latest `dt_inter` 2023-03-31. By month of `dt_saida`:
  2023-02 3, 2023-03 50, 2023-04 29, 2023-05 8, 2023-06 192, so 229 left from 2023-04-01
  on. By `ident`: 92 with 1 and 190 with 5.
- `RDSP2512`: 97 AIH with 99, latest `dt_inter` 2022-11-25, all with `dt_saida` in
  2025-12 and `ident` 5.

These equal the unrecorded check (229 of 282; 97 of 97).

## (b) `diar_acom` above zero, by group

Key `diar_acom` of each São Paulo file. The groups are disjoint and cover every AIH:
`cobranca` 61 to 67, and the other AIH by age in years. Each group has its AIH (`rows`)
and those with `diar_acom` above zero (`rows_above_0`).

Age rule: `cod_idade` 2 (days) and 3 (months) are under one year; 4 is `idade` years; 5 is
`idade` plus 100 years. It is the decode map of `cod_idade` in
`src/omnisus/data/dicionarios/sih_aih_reduzida.yaml` (`"2": "Dias"`, `"3": "Meses"`,
`"4": "Anos"`, `"5": "Anos (somar 100)"`), which the dictionary marks as measured, not
read (issue `cod_idade-sem-tabela`). No AIH of the seven files has another unit
(`other_age_unknown` has 0 rows in all).

| File | `diar_acom` > 0 | `cobranca` 61-67 | other, under 18 | other, 18 to 59 | other, 60 or more |
| --- | ---: | ---: | ---: | ---: | ---: |
| RDSP1412 | 52,346 | 9,499 of 26,207 | 15,921 of 29,007 | 5,126 of 87,126 | 21,800 of 51,449 |
| RDSP1502 | 52,350 | 10,264 of 29,456 | 15,792 of 29,051 | 5,221 of 86,516 | 21,073 of 50,799 |
| RDSP1902 | 65,566 | 15,645 of 29,633 | 15,318 of 27,077 | 7,297 of 89,318 | 27,306 of 57,571 |
| RDSP2001 | 73,016 | 16,937 of 30,271 | 16,385 of 28,570 | 8,091 of 93,726 | 31,603 of 63,199 |
| RDSP2303 | 75,108 | 17,013 of 29,007 | 19,921 of 34,420 | 7,383 of 98,275 | 30,791 of 71,947 |
| RDSP2306 | 76,343 | 15,729 of 27,274 | 19,348 of 33,296 | 7,836 of 97,257 | 33,430 of 74,436 |
| RDSP2512 | 85,178 | 13,909 of 20,855 | 16,916 of 29,252 | 13,110 of 100,356 | 41,243 of 80,284 |

Each cell is AIH with `diar_acom` above zero of the AIH of the group.

Difference from the unrecorded check: for `RDSP2512` it had 41,168 with 60 or more and
16,991 under 18; this run has 41,243 and 16,916. The total (85,178), `cobranca` 61 to 67
(13,909) and 18 to 59 (13,110) are equal: 75 AIH are under 18 there and 60 or more here.
The rule the unrecorded check used for the age was not kept.

## (c) External cause in `diag_secun`

Key `external_cause` of every file, summed per competence in `competences`: AIH whose
`diag_princ` starts with S or T, and those of them whose `diag_secun` starts with V, W, X
or Y.

| Competence | Files | AIH | `diag_princ` S or T | of which `diag_secun` V to Y |
| --- | ---: | ---: | ---: | ---: |
| 2008-01 | 27 | 651,615 | 39,931 | 39,073 |
| 2012-01 | 27 | 918,846 | 82,992 | 82,696 |
| 2014-12 | 1 | 193,789 | 19,086 | 18,726 |
| 2015-02 | 1 | 195,822 | 18,321 | 0 |
| 2016-01 | 27 | 919,331 | 94,147 | 0 |
| 2019-02 | 1 | 203,599 | 19,456 | 0 |
| 2020-01 | 1 | 215,766 | 21,533 | 0 |
| 2023-03 | 1 | 233,649 | 22,918 | 0 |
| 2023-06 | 1 | 232,263 | 22,463 | 0 |
| 2025-12 | 27 | 1,174,830 | 140,632 | 0 |

- 2008-01: in 3 of the 27 files every AIH with S or T has V to Y (`RDDF0801`, `RDRR0801`,
  `RDSE0801`); the lowest share is `RDAP0801`, 58 of 65.
- 2012-01: in 19 of the 27 files every AIH with S or T has V to Y; the lowest share is
  `RDES1201`, 1,451 of 1,491.
- `RDSP1412`: 18,726 of 19,086, equal to the unrecorded check.
- From 2015-02 on, no AIH of the files read has V to Y in `diag_secun`: the six later
  São Paulo files and the 54 files of 2016-01 and 2025-12.

Blank and `0000` (key `blank_or_0000` of each São Paulo file): in `RDSP1412`, `diag_secun`
is blank in 134,282 of the 193,789 AIH and `cid_asso` in 187,186, and neither field has
`0000` in any AIH. In the six later São Paulo files both fields are `0000` in every AIH
and never blank.

What this does not settle: the months of 2008 to 2014 other than 2008-01, 2012-01 and,
for São Paulo, 2014-12.

## (d) The same `n_aih` in more than one row

Within a file (key `n_aih_repeated` of each São Paulo file): the `n_aih` values that occur
in more than one row, the rows they take, and how many of those values have a single
`dt_inter` in all their rows.

| File | `n_aih` in more than one row | rows | with a single `dt_inter` |
| --- | ---: | ---: | ---: |
| RDSP1412 | 258 | 548 | 258 |
| RDSP1502 | 254 | 528 | 254 |
| RDSP1902 | 63 | 144 | 63 |
| RDSP2001 | 95 | 206 | 95 |
| RDSP2303 | 45 | 95 | 45 |
| RDSP2306 | 174 | 353 | 174 |
| RDSP2512 | 62 | 128 | 62 |

Between `RDSP2303` and `RDSP2306` (key `n_aih_in_both`): 3,042 `n_aih` values are in both
files, in 3,050 rows of the first and 3,139 of the second. All 3,042 have a single
`dt_inter` in all their rows of the two files, and in all of them every
`dt_saida` of `RDSP2306` is later than every `dt_saida` of `RDSP2303`
(`n_aih_later_dt_saida_in_second`). By `ident`: 2,765 have 5 in both files, 274 have 1 in
`RDSP2303` and 5 in `RDSP2306`, and 3 have rows with 1 and rows with 5 in `RDSP2303` and
5 in `RDSP2306`.

Difference from the unrecorded check: it had "3,148 in both: 2,866 ident 5/5 and 282
ident 1 then 5". 3,148 is the number of pairs of rows with the same `n_aih`, one row of
each file (`pairs_of_rows`); a value that takes two rows in a file counts twice. This
script counts `n_aih` values, and there are 3,042. That all share the `dt_inter` is equal
in both counts.

What this does not settle: other pairs of competences, other UFs, and what links two AIH
with different `n_aih` of the same stay.

## Files

| File | SHA-256 | Bytes | AIH | `diag_princ` S or T | `diag_secun` V to Y |
| --- | --- | ---: | ---: | ---: | ---: |
| RDAC0801.dbc | `fde119624f5ba8400fdd25f086be6180bb25440c141dbf9ae634b7f417d0f28d` | 114153 | 2087 | 132 | 126 |
| RDAC1201.dbc | `ed1af51e4aa132693c8c652d8173faed293f390d254413dca9ce32b4cb3a4c0b` | 282290 | 3945 | 357 | 357 |
| RDAC1601.dbc | `f65e80451faf6663187f826b66176a45eb0c35b1000f91ea5a4180246f965ac2` | 260204 | 3520 | 370 | 0 |
| RDAC2512.dbc | `0866ca3264e1fef1431de70e0f857b65bccea6c050163f3cfa99871604f68fd8` | 326478 | 4527 | 329 | 0 |
| RDAL0801.dbc | `8b72541b774a0f125905995d88578f1ef8e7bcaf0347836f584ad4d2a1c518cc` | 649292 | 12168 | 513 | 510 |
| RDAL1201.dbc | `d6f36f496e516ba5f65fefdc3d29f9cf4e3fb55d4d1506c1d506216fad2d8cfb` | 986632 | 15179 | 1138 | 1138 |
| RDAL1601.dbc | `5e2bad3270033b49f1272eae1ef37b76980581d890829c08c48f28df4a1cb20b` | 972093 | 13902 | 1376 | 0 |
| RDAL2512.dbc | `e4ef6f7f2a578fccd9909de8e9d56aeb6b6948ed34dc4b02f26c4d45082ba5ca` | 1051577 | 14176 | 1868 | 0 |
| RDAM0801.dbc | `70fc4614593552d58e2a0e13858170d8c5babfdeb6fed5bdfc73fb55207bd2f1` | 507103 | 9325 | 457 | 446 |
| RDAM1201.dbc | `0d7c3c186c3867d40d8ea1307b56bd7bb98a85536a6d0e0a947b4db071ab194d` | 836846 | 12944 | 901 | 901 |
| RDAM1601.dbc | `cfe4763cbc5276b7cb086700307be9f5df3f3f25f66252d5dce6197faa527915` | 892456 | 13492 | 894 | 0 |
| RDAM2512.dbc | `b41cf5ca53da64b4481f57662072357327bb9925280e3d0cd73addbb44a201da` | 1547730 | 21768 | 2172 | 0 |
| RDAP0801.dbc | `00afc30235fc8ada93c98a4ebe81a583ea9054bfef4198b03ee42502197ae2fc` | 138343 | 2386 | 65 | 58 |
| RDAP1201.dbc | `e84f467afd4871ff4d17fdbba7ffbf5da0c39b9a67075fb33543f28371f9e10d` | 204119 | 3055 | 262 | 262 |
| RDAP1601.dbc | `03ddc29ee17f82b348cecb3c8109bc3624ea2860d89663cae8a9896319266a70` | 167039 | 2607 | 166 | 0 |
| RDAP2512.dbc | `a530c43b1cca7995011c9121fa8be834c0022866c7446bbfd041f0f28b29c79e` | 331879 | 4900 | 446 | 0 |
| RDBA0801.dbc | `3b6a630a91cd958d07ad42d9f02b510f39d54bfd5f5e560cc8bbb27a70078813` | 2442824 | 41659 | 2216 | 2199 |
| RDBA1201.dbc | `92b8420453f03265916a93c1bc64f1ee104fc6ccb739395991d7cba51e8c7457` | 4488183 | 68584 | 5170 | 5114 |
| RDBA1601.dbc | `1d689f5fd3aaa7a389335a12ca8134a5bb05c9aed2b3fb23566acd16721724a6` | 4635410 | 64985 | 5987 | 0 |
| RDBA2512.dbc | `0e7c0ab9b4631c47f5a2f89f84bbc8f4880e9dd1d18392295b9b20647fc50619` | 5706040 | 77304 | 9568 | 0 |
| RDCE0801.dbc | `0f28c1f696c373c26ac1e051b827787427cd8c1455167192edb703e99ec0d7f8` | 1717859 | 29823 | 1695 | 1690 |
| RDCE1201.dbc | `beaf250bdedf9c30afe75397b91a08f53cbc42023b53207f01e71b19301112bf` | 2523916 | 38134 | 3903 | 3903 |
| RDCE1601.dbc | `fd8d7de66376b83d17ee6fcab6641d94f89239973d6970d08db1d5ff88dcf9ae` | 2661764 | 38221 | 4154 | 0 |
| RDCE2512.dbc | `c06b42d30e7f0607330e16b3b7229a0b21cfdec1e01623dfe7b36d68c21e0c66` | 3620722 | 48468 | 5919 | 0 |
| RDDF0801.dbc | `d8fd2676df3696d9d338f804f931cc538878f3e1b77933caed9ff38e116c704a` | 463062 | 7754 | 455 | 455 |
| RDDF1201.dbc | `ee24bdfcbd6279ab879141b66bd0aa6a6196963c870fd15dfe7249ecf9733a7e` | 1081971 | 15111 | 1353 | 1353 |
| RDDF1601.dbc | `3048ecf0c9147f507725f44d4dfb03a75a2127415a2f154d2009066e34a6d583` | 983353 | 13128 | 1316 | 0 |
| RDDF2512.dbc | `d4c111a1fd34debe6b793aeec306e0f38cfd729d8326beba6d162f234c3e8730` | 1632157 | 20360 | 2188 | 0 |
| RDES0801.dbc | `18ba01c3ca88b556a208c689d81bf58c19be8e73f949f4b13de1bc93a5bce3d0` | 599540 | 9502 | 456 | 441 |
| RDES1201.dbc | `4f47bc2a6bf69a9fba2ffa9da5b1b9b7262200e729dd4c0e57626ba1c7897c2f` | 1281519 | 17509 | 1491 | 1451 |
| RDES1601.dbc | `12111b4880aa7c397a0a43a16d946529ff1efe00a02feb7e378c94f74a99874a` | 1451513 | 18956 | 2057 | 0 |
| RDES2512.dbc | `ac8c7142b1133ee6c44adf0fa867fc9335d0d1077d43cd74f1f2a7a6430ff8e3` | 1982866 | 25613 | 3721 | 0 |
| RDGO0801.dbc | `f117d0e81ef106ac791c5d5a9e04264c8bb908def51a1d11d4930ab44e2eff9f` | 1565822 | 26465 | 1779 | 1696 |
| RDGO1201.dbc | `5b6c23df17c1f49e633e77f059d657ef24ba3d4a477dcdd0a4a7cc8bceb608e0` | 1905518 | 28427 | 2823 | 2823 |
| RDGO1601.dbc | `9c07f45d2ef5577dba3b9ca93d3cb605e47e49d4285641a58876fcd38f29989f` | 2008223 | 28199 | 3956 | 0 |
| RDGO2512.dbc | `fe36a273314aafd24e755f12e012ea98b16796466e717758c32b07312bcf303d` | 2791654 | 37218 | 6245 | 0 |
| RDMA0801.dbc | `4364e04d3ce87e3340195e08fdb36bb0a6e654f05f0ff963882fc320d94ffe27` | 1064563 | 21417 | 870 | 839 |
| RDMA1201.dbc | `155e4e550c8513a80a226231201b719a73b4e2e3bc828f6b4e79128085d99233` | 2078201 | 33818 | 2210 | 2210 |
| RDMA1601.dbc | `76cf5327a99f241b7704edb933af3b3f5872bf2ad273624d32733403691114fc` | 2328574 | 35088 | 3465 | 0 |
| RDMA2512.dbc | `f63141a68a291ceee339b892790835574c5d388a5b05ffeab6ca5fc4c5491925` | 2758504 | 40293 | 4726 | 0 |
| RDMG0801.dbc | `06ce4974f52e58b1ebade62a7e1e4bc10c87b9ec2bea5498fc16188a4c7ad204` | 4357193 | 67509 | 4526 | 4433 |
| RDMG1201.dbc | `a2073e91a6aeb39852cc0467dabe8356c7ab3307220acaf14755dc7466c97012` | 7229369 | 96614 | 9366 | 9235 |
| RDMG1601.dbc | `e146c2f419fc6394ca21f6ee2864b95cd2fbdaf7592a980c1bb36130f6a34943` | 7605837 | 97833 | 10537 | 0 |
| RDMG2512.dbc | `1f8e56e7aee39a4a0e2486f03413386061f197252ecd25000c48a423fc368cd8` | 10040304 | 128022 | 14968 | 0 |
| RDMS0801.dbc | `09d6fd890a4b290cb88e12e00c66aaba475964c3f7d13a70388d873305a1c7c0` | 618944 | 9636 | 966 | 920 |
| RDMS1201.dbc | `43fadff2f71290c242d77fafd49e0d734fd9a61c1a3da13cd033c1896d7ddcc2` | 849807 | 11936 | 1436 | 1436 |
| RDMS1601.dbc | `b5f29d49154e3e026e291a245961fbfb58d5c9e16ae10b09da280d9899ef5910` | 1041446 | 13732 | 1814 | 0 |
| RDMS2512.dbc | `a9956bdae4dd6abaed71e37dfc25eda719571a8c52356fd0f4e021cd17240f50` | 1256472 | 16193 | 2384 | 0 |
| RDMT0801.dbc | `b596449d6bc34c53092f2478ee43135fe2204055e6e16fd29f247a9ef5331383` | 623545 | 9975 | 551 | 527 |
| RDMT1201.dbc | `e6ca9867c4a97c17e9332f73a06a9aa01c8252e9fe1fb6b28c45ffcdc75377c6` | 936597 | 13512 | 1634 | 1617 |
| RDMT1601.dbc | `86857d02c2ec68fd9910c3a7e725e802b17adc0009874d9abdcdaf8e15f2d949` | 1161922 | 15805 | 2331 | 0 |
| RDMT2512.dbc | `c8444a494d944eaabe1f9af9793dc8b7e2057091b9ed2fe667b855f033019c94` | 1540767 | 20653 | 2947 | 0 |
| RDPA0801.dbc | `03337aeb2b84a9dbbc7521a1664b43ba4237439fbe7e244a36a55836cb941326` | 2050198 | 38628 | 2670 | 2606 |
| RDPA1201.dbc | `0f2f00d540e3e5a8468821763728155657bd2b634147ead02af2e9b62806ae31` | 2607609 | 42778 | 4011 | 4011 |
| RDPA1601.dbc | `6d9ea813af736595931ae6b6bd13a13398d634bc01343fded0bdf8cb203b261e` | 2420770 | 37348 | 4258 | 0 |
| RDPA2512.dbc | `6d5896f3f5f6adf9524166a834500f4789e08792fb0c34bf805f5ad0713d0c51` | 3414115 | 48817 | 7131 | 0 |
| RDPB0801.dbc | `88f23e8fca1d3a956e362fc29d6786b30f24403e568ab0bdf7164aa07add7cba` | 1049842 | 17126 | 979 | 957 |
| RDPB1201.dbc | `cbfc84b31b0978fa13b0148f1bbd276dd5d071521d9850726f7368820176e989` | 1141324 | 16259 | 1277 | 1276 |
| RDPB1601.dbc | `8ac64383afdc3a71250bf2cbcd13f50951f3585628173ebc635353974fe972cb` | 984103 | 13646 | 1070 | 0 |
| RDPB2512.dbc | `989bb9fcaf953703d40269b500f13dd3508604ed92c1f001d4e50be4e1b14546` | 1501361 | 19260 | 1990 | 0 |
| RDPE0801.dbc | `a19eee31d7c75c70dcc61d8942da2de3a84c689b3592987cedc3127112b99cc7` | 1489520 | 25390 | 1033 | 997 |
| RDPE1201.dbc | `35dad3dfec6c394e2003a48f6104b956b0101a1b26482b4cd27aca5b8d572772` | 2980539 | 43116 | 3232 | 3232 |
| RDPE1601.dbc | `f68f634da1d45b6bb3f60f989613c0566f7c394f071fa1b7c4a6f3874bbbe674` | 3182632 | 43928 | 4382 | 0 |
| RDPE2512.dbc | `6e73e0169857423e23c5c7b2b8634a4c048cdbd019b1ceae61e31bb9a4e69d2b` | 4153035 | 55935 | 7498 | 0 |
| RDPI0801.dbc | `1da2d97af82a734078782f10104142035013d9fa68014f44c976c976732107df` | 927125 | 15878 | 888 | 886 |
| RDPI1201.dbc | `38f79bd22a53a781bf7a28b7d26aa491a17594c3312334fb184403f23b62a29a` | 1289545 | 18994 | 1759 | 1759 |
| RDPI1601.dbc | `2f7ea8f2e0b8e7e6f8a3d0b00b9db2ba0bdf7cacc52a385ba1773fd56657cccb` | 1272221 | 18038 | 2097 | 0 |
| RDPI2512.dbc | `3720bb785b33df481d572872e861a9e5625de32747ed257ccf5f937251d2bfce` | 1428355 | 19014 | 2577 | 0 |
| RDPR0801.dbc | `be9aec235d3ffd2481cb482a832dd3fa71e8b156352f95fdcc64e9b5574cf825` | 3206594 | 51180 | 3678 | 3585 |
| RDPR1201.dbc | `0a935da7c6bb8b11877c571937db4ba305e4aa91997a7c9c02aa3b7860ebc8fc` | 4678129 | 64290 | 6655 | 6626 |
| RDPR1601.dbc | `783591a7530ee2cb97c56d434e7d1a40d8dc6e293288466cf084a551a748a3ec` | 4812925 | 63458 | 6812 | 0 |
| RDPR2512.dbc | `df5e4ede0d85f9fe7a4605445b11333cec5a6d0b1b4f2680713e16b84a9c8101` | 6875278 | 89610 | 10788 | 0 |
| RDRJ0801.dbc | `6a362242dcb881099929eef7a13f75a92ee1b46cbc1f98ff996354afceb37b49` | 1970037 | 34859 | 1345 | 1328 |
| RDRJ1201.dbc | `742d3fd52030906d21a986a86d2b10b5e48c8d19ff5ebcff85db48435e41cd8a` | 3636795 | 53068 | 3845 | 3828 |
| RDRJ1601.dbc | `ff0af5d0359ddd7091395eea46e1f01d8f5e27c642a2d739e456c2f4eb727033` | 4187567 | 56877 | 5681 | 0 |
| RDRJ2512.dbc | `93d6e196b52c1a5864437e6a97f8a041af71642dfd082179e4247719e61bd36b` | 5909820 | 76232 | 9085 | 0 |
| RDRN0801.dbc | `f3e93d1c76123edc4a8c9fb986e9ca9c2e7186bbf82c62b981f38b74f6250cbf` | 573433 | 9916 | 398 | 396 |
| RDRN1201.dbc | `437863e108abb46a879a343ccc9a7d790146b94af1bb1d4f236598f6d0b74880` | 896455 | 13551 | 949 | 949 |
| RDRN1601.dbc | `8815ac4345f7951e530dff5b50e3593a7572c0eacd62b8f9e1a0de04c80176ca` | 924489 | 12793 | 1014 | 0 |
| RDRN2512.dbc | `6453c7d81a3d6b5b24cdc548af3e6323b077803665281b5b481f505e1fd5ea3f` | 1293284 | 17704 | 2058 | 0 |
| RDRO0801.dbc | `c50dbfb6239025119bf2eb79e482ebb4284fc2f4e48fc240f37bca979ff6f868` | 223052 | 4142 | 283 | 280 |
| RDRO1201.dbc | `df9b50a9d2142cc7029f7edb6d205f694f3e37ac1c6eaa9db0588ee183400586` | 481274 | 7998 | 768 | 768 |
| RDRO1601.dbc | `baede1b3f33727ff239a2c60a318c23f0adec27eeab1c458c473184eee545b7d` | 612200 | 8956 | 1340 | 0 |
| RDRO2512.dbc | `25fdb0528ed640dd9ebfd32dc0c2907dc66ce47212a3c1da1a270235af5b67e4` | 804859 | 11527 | 1343 | 0 |
| RDRR0801.dbc | `ad3817afbe19f8087415f5204a677893dee767a802de093d84bb193577c2d4e7` | 75358 | 1475 | 72 | 72 |
| RDRR1201.dbc | `3f1ebc51b1e2aca35348d7440a982576c6fdd446762fb9a57373bd3e3e63eb48` | 155584 | 2289 | 180 | 180 |
| RDRR1601.dbc | `b5426ef0c50304897e6e92b6615a0b8382f61814ccd78f3b15f12fef1dfb98b5` | 196012 | 2748 | 221 | 0 |
| RDRR2512.dbc | `75988926198221313d854ca8bf80e23007b2a110c3385d3fb64ab2222aff5df9` | 157616 | 2128 | 171 | 0 |
| RDRS0801.dbc | `8d25b1e34bffb60c8abb175ef39af91ff4f5f3327d3bbdf353b9170c118c651a` | 2780100 | 41729 | 2292 | 2204 |
| RDRS1201.dbc | `8bd1b90790e4bfd08853185871d635b32bacefac6615f3e3291e2de98ca775e9` | 4268871 | 55459 | 4257 | 4257 |
| RDRS1601.dbc | `f089f0e203ea92992aca2c9aaba774f820254bbc211aba71d2dd5ee3ce58495e` | 4516083 | 58456 | 4919 | 0 |
| RDRS2512.dbc | `baa03998fc041c61b3ad2fcb24c91ff0549f85a628c65a5df60ab7a4d871783e` | 5486232 | 70967 | 6827 | 0 |
| RDSC0801.dbc | `7757608f37219b9d284dcdbe2f4641d216ed6c13bb6313a03a8f0738affcf7d2` | 1619551 | 23728 | 1672 | 1569 |
| RDSC1201.dbc | `a2802efdfe8f508ec767d4674d5769dbce6afc4f26776462f5b03aad564d8bdf` | 2440187 | 32159 | 3292 | 3292 |
| RDSC1601.dbc | `f2f89e69f67f2ae87cd4efa7ec44215423448d56d9c338e78f2e4ba47c590a43` | 2825319 | 36944 | 3689 | 0 |
| RDSC2512.dbc | `9cc6322a4167d3836a1fc229872a07ae6e8ad20f648bded0052d3242d7349a22` | 4382328 | 55204 | 5881 | 0 |
| RDSE0801.dbc | `4abed05e11b06f28275772417f711da7d7cc4d561fafc4d39cb2a57f97ba631f` | 309622 | 5832 | 429 | 429 |
| RDSE1201.dbc | `133fe250bdcfbbca55220da3e7d5024eb004d55e5e0cd0ecb22b3e204bede33c` | 516538 | 7380 | 616 | 616 |
| RDSE1601.dbc | `559316bca769156357476f693ac66713c8e8ad9d715b861de46af67165e975f2` | 496048 | 7203 | 716 | 0 |
| RDSE2512.dbc | `272cb12866dc82443fe21f94ab23699acb60ead0fb223320dabcc66c400f845a` | 797886 | 10417 | 918 | 0 |
| RDSP0801.dbc | `f2cba06b3b3d4d13d6ed3cfe69f83e46443f3e1700bc694e637fa5847c0671e9` | 7799792 | 125361 | 8925 | 8839 |
| RDSP1201.dbc | `3edf83e541c3287df66110c3222092d6f1c98b317a6f09804555d80f7244bf07` | 13891006 | 193264 | 18973 | 18968 |
| RDSP1412.dbc | `c744f524f7a98dc02b30aef346d0efa693dc00d5baeb29a47e378876b808c3ec` | 14214477 | 193789 | 19086 | 18726 |
| RDSP1502.dbc | `8011928ad0cb9119ba6ef1c95df8471a44e52a70855624810b3c30ae79b5e8b6` | 14899189 | 195822 | 18321 | 0 |
| RDSP1601.dbc | `c14bcae03b5adecadd84f7983a30faef0ceaeea0e1a3bdf7d6cfec14f8b3c7f2` | 14818924 | 193621 | 18831 | 0 |
| RDSP1902.dbc | `4653fb8f96fefacfb3a47f8f7fc1b1d1591c56be0c9800fbe0fcddf82dc254a0` | 15690982 | 203599 | 19456 | 0 |
| RDSP2001.dbc | `ea611bb554aa00062c8aee2c3041d3065b2635938cdd32d6ce6636cb91436478` | 17083017 | 215766 | 21533 | 0 |
| RDSP2303.dbc | `e6c920afdb0f432f93724893a731b22cb9303c2bed8a3342ed0c161f2e600b6b` | 18077745 | 233649 | 22918 | 0 |
| RDSP2306.dbc | `e9507c7429b4dc8990639b90b70e2ea38d42547dde7594cf1f327aae8587a95b` | 18001348 | 232263 | 22463 | 0 |
| RDSP2512.dbc | `976373cd79219b8287dcb3815f5a7b7b85c40ce542dce903e44591bc05159aa5` | 18300555 | 230747 | 25840 | 0 |
| RDTO0801.dbc | `ba2e15f2f1b53a42e35c014ddaca4716d7b07651b1460fa5180ff482ed7bc723` | 418955 | 6665 | 586 | 585 |
| RDTO1201.dbc | `bb149fb60ebf4c6cd962c272a585f4713852b5e2c5d37c6b7c78b7ef41acd6a1` | 666210 | 9473 | 1134 | 1134 |
| RDTO1601.dbc | `9fdb35647acef42416c6eb1c4de3d3e902c8f8e6325efef36cbcda8fff8709d2` | 438778 | 5847 | 694 | 0 |
| RDTO2512.dbc | `4a21a3a2c3c88ba8e6417eac0147e7f7334e46dd6bfd838d84bd48a1035f4099` | 596933 | 7773 | 1044 | 0 |
