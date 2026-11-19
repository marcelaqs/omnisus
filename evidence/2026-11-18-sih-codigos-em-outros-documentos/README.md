# Codes that two other DATASUS documents give to `tpdisec1-9` and `homonimo` (#182)

`sih_aih_reduzida` leaves two things without a label because no document of the RD
files gives them: the `0` of `tpdisec1` to `tpdisec9` and every code of `homonimo`. Two
documents of the same directory of manuals,
`ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/`, give codes to what
looks like the same thing in another file. They were read on 2026-11-18 and are quoted
here so that the open issues of those fields can say what was read and why it was not
used. The listing of the directory that day is
`evidence/2026-11-18-layout-reduzida-sihd/manuais-listing.txt`.

| Registry id | File | Bytes | SHA-256 |
|---|---|---:|---|
| `sihsus-af543b2b2c9b` | `Layout_do_SISAIH01_para_CMPT_201509.zip` | 71,003 | `af543b2b2c9b13de8d11a68ec5fdd04b2b53c864af8b8e77456a23795398d625` |
| `sihsus-f70974716de8` | `dicionario_de_dados_AIH.pdf` | 47,584 | `f70974716de829b97b341b2f05ba76eb382c09d867abcf1a0ffbdb95a1c57854` |

The zip has three members, all read. `layout sisaih01-sihd - para cmpt 09-2015.pdf`
(61,467 bytes, 9 pages, SHA-256
`6c7f1298ed25fbd3efb40a140e93cd6978ba23d62f8af9eaaa86fe049e2f89b1`) is titled "Layout da
interface texto do SISAIH01"; no member says who writes or sends that file.
`layout sisaih01-sihd - LEIAME.pdf` lists fields 100 to 118 (`DIAG_SEC_1` to
`DIAG_SEC_9_CLASS` and a filler) as "CAMPO INCLUIDO" among the changes "para uso à
partir da cmpt 01 / 2015". The third member holds annexes. `dicionario_de_dados_AIH.pdf`
(13 pages, "Dicionário de Dados – AIH", "Atualizado em 02/05/2016") describes the
columns of four tables, `TB_AIH` and `TB_HAIH` ("Tabela de AIHs- movimento" and
"histórico", columns `AH_...`) and two with columns `PA_...`; none is the RD.

`trechos.csv` has 19 rows, one per field of each document: the nine `DIAG_SEC_n_CLASS`
of the SISAIH01 layout, the nine `AH_DIAG_SEC_n_CLASS` of the dictionary and its
`AH_ST_DUPLICIDADE`. Each has the registry id, the pages, the name the document gives
the field, and the text from the row of that field to the next row of the table.
`extrair.py` wrote it with pypdf 7.1.0 and stops when a file has another SHA-256:

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-sih-codigos-em-outros-documentos/extrair.py \
        "layout sisaih01-sihd - para cmpt 09-2015.pdf" dicionario_de_dados_AIH.pdf \
        > evidence/2026-11-18-sih-codigos-em-outros-documentos/trechos.csv

- SISAIH01, p. 7, field 101 `DIAG_SEC_1_CLASS`: "0 - Quando não é preenchido o campo
  anterior", "1-Preexistente", "2-Adquirido". Fields 103 to 117 (`DIAG_SEC_2_CLASS` to
  `DIAG_SEC_9_CLASS`) say "ver campo 101".
- Dictionary of the AIH, p. 4, `AH_DIAG_SEC_1_CLASS` to `AH_DIAG_SEC_9_CLASS`, each:
  "0-Quando campo anterior em branco, 1- PREEXISTENTE, 2-ADQUIRIDO".
- Dictionary of the AIH, pp. 8-9, `AH_ST_DUPLICIDADE`: "Marca de homônimo, onde: 0 =
  não. 1 = sim."
- A third document says the same of the homonym mark: `Layout_REDUZIDA.pdf`
  (`sihsus-f6084d22de30`), p. 2, `HOMONIMO`: "MARCA DE HOMONIMO ( 0 = não , 1 = sim)". It
  is transcribed in `evidence/2026-11-18-layout-reduzida-sihd/layout.csv`.

**What it is used for.** The issues `tpdisec-0-sem-fonte` and `homonimo-sem-fonte` of
`sih_aih_reduzida.yaml` name these documents and quote them;
`tests/unit/transforms/test_sih_rd_fields.py` compares the quotes with `trechos.csv` and
`layout.csv`, and checks that the codes stay without a label.

**What it does not settle.**
- `tpdisec`: the two documents agree with each other, with the `1` and `2` of
  `TP_DIAGSEC.CNV` (the table `RD2008.DEF` binds to `TPDISEC1-9`) and with RDRR2401,
  where every row with `0` has the diagnosis blank. What is missing is a document or a
  DEF of the RD that gives the `0`; whether that is needed is the maintainer's decision
  (#182, C11), and the `0` stays without a label.
- The RD files have `TPDISEC1` from 2014-01 (layout 5 of
  `evidence/2026-10-06-rd-2008-layouts`), a year before the SISAIH01 readme says the
  text file gained the fields. Only the SISAIH01 edition for 09/2015 was read; the
  directory lists one for 01/2015 and eight later ones.
- `homonimo`: both lists stop at `1`. The files read (`evidence/2026-11-18-rd-medidas`)
  publish `0` and `2` in every year from 2006 to 2026, the 21 months of the layout
  `Layout_REDUZIDA.pdf` describes included, and `1` in one file of 2026. That document
  also gives 19 labels to fields the 2008 layout calls "Zerado"; its list for this field
  is not used because the data has a code it does not list, not because of its date.
- `tpdisec` again: in the files read, the 12 of 2014 publish the nine fields blank, and
  the 148 from 2015-01 publish `0` only with the diagnosis of the same number blank,
  which fits the readme's date for the SISAIH01 fields.
