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

The zip has three members. The one read is `layout sisaih01-sihd - para cmpt
09-2015.pdf` (61,467 bytes, 9 pages, SHA-256
`6c7f1298ed25fbd3efb40a140e93cd6978ba23d62f8af9eaaa86fe049e2f89b1`), titled "Layout da
interface texto do SISAIH01": the layout of the text file a hospital sends through the
SISAIH01. `dicionario_de_dados_AIH.pdf` (13 pages, "Atualizado em 02/05/2016") describes
columns named `AH_...`, not fields of the RD.

`trechos.csv` has ten rows, one per field: the nine `DIAG_SEC_n_CLASS` of the SISAIH01
layout and `AH_ST_DUPLICIDADE` of the dictionary. Each has the registry id, the pages,
the name the document gives the field, and the text from the row of that field to the
next row of the table. `extrair.py` wrote it with pypdf 7.1.0 and stops when a file has another
SHA-256:

    uv run --locked --with pypdf==7.1.0 python \
        evidence/2026-11-18-sih-codigos-em-outros-documentos/extrair.py \
        "layout sisaih01-sihd - para cmpt 09-2015.pdf" dicionario_de_dados_AIH.pdf \
        > evidence/2026-11-18-sih-codigos-em-outros-documentos/trechos.csv

- SISAIH01, p. 7, field 101 `DIAG_SEC_1_CLASS`: "0 - Quando não é preenchido o campo
  anterior", "1-Preexistente", "2-Adquirido". Fields 103 to 117 (`DIAG_SEC_2_CLASS` to
  `DIAG_SEC_9_CLASS`) say "ver campo 101".
- Dictionary of the AIH, pp. 8-9, `AH_ST_DUPLICIDADE`: "Marca de homônimo, onde: 0 =
  não. 1 = sim."
- A third document says the same of the homonym mark: `Layout_REDUZIDA.pdf`
  (`sihsus-f6084d22de30`), p. 2, `HOMONIMO`: "MARCA DE HOMONIMO ( 0 = não , 1 = sim)". It
  is transcribed in `evidence/2026-11-18-layout-reduzida-sihd/layout.csv`.

**What it is used for.** The issues `tpdisec-0-sem-fonte` and `homonimo-sem-fonte` of
`sih_aih_reduzida.yaml` name these documents and quote them;
`tests/unit/transforms/test_sih_rd_fields.py` compares the quotes with `trechos.csv` and
`layout.csv`, and checks that the codes stay without a label.

**What it does not settle.** None of the three documents describes the RD files from
2008. No DEF of `TAB_SIH.zip` relates `TPDISEC1` or `HOMONIMO` to them, and none
mentions the `2` the RD publishes in `homonimo`. That the `0` of `tpdisec1` goes with a
blank `diagsec1` in every row of RDRR2401 agrees with the SISAIH01 text and is not a
source for a label.
