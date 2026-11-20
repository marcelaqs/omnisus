# TP_FINAN: the CNV the DEF names and the DBF its line seems written for (#182)

`RD2008.DEF` (lines 271-273) and `RJ2008.DEF` (lines 274-276) bind `FAEC_TP` with lines
such as `LSubTp FAEC, FAEC_TP, DS_TPFIN, CNV\TP_FINAN.CNV`. A line that binds a CNV has a
start column in the third part (TabWin.pdf, `tabwin-bb98cff14765`, p. 88); this one has
`DS_TPFIN`. A line whose third part is a column name is the form that relates a field to
another DBF (same page), and `TAB_SIH.zip` has a `DBF/TP_FINAN.dbf` whose description
column is `DS_TPFIN`. So the line has the shape of a DBF relation and names a CNV.

`comparacao.csv` puts the two tables side by side, one row per code. `comparar.py` wrote
it from `TAB_SIH.zip` (`sih-tab-21e42384645a`, SHA-256
`21e42384645a9386add9f3644264145f39fc00bbb602f305d87bd0793b7e476b`) and stops when the
file it is given has another SHA-256:

    uv run --locked python evidence/2026-11-18-tp-finan-cnv-e-dbf/comparar.py TAB_SIH.zip \
        > evidence/2026-11-18-tp-finan-cnv-e-dbf/comparacao.csv

| Member | Bytes | SHA-256 |
|---|---:|---|
| `CNV/TP_FINAN.CNV` | 12,146 | `f6986095b663c4a22b69e027c582b7094c56c40abaf26a8183206531d9336683` |
| `DBF/TP_FINAN.dbf` | 13,913 | `6105618f52f5e19781fb91f1f1a1b196afd16a6717b3cdd0377e7fcb5ae8649e` |

Both hashes are also in `evidence/2026-11-15-tab-sih-republicado/members.csv`. The DBF
has two fields, `CO_TPFIN` C(6) and `DS_TPFIN` C(150), and 88 records.

- 103 codes in all: 101 in the CNV (100 of 6 digits and the blank code), 88 in the DBF,
  86 in both.
- Only in the CNV: the blank code and 14 others, `021012`, `021014` and `040081` to
  `040092`.
- Only in the DBF: `000000` "Não identificado" and `040000` "Sem definição".
- Of the 86 in both, 2 differ: `040078` ("QualiSUS Cardio" in the CNV, with a full stop
  in the DBF) and `040080` ("Programa Agora Tem Especialistas - Componente Cirúrgico
  (antigo Reduçäo das Filas)" in the CNV, with three blanks before the parenthesis;
  "Reduçäo das Filas de Procedimentos Eletivos." in the DBF).
- Of the 32 codes the 238 RD files of `evidence/2026-11-18-rd-medidas` publish, 3 are
  not in the DBF: `021014` (1,550 records), `040082` (873) and `040084` (10).

**What it is used for.** `faec_tp` of `sih_aih_reduzida` and `sih_aih_rejeitada` takes
its labels from the CNV, the file the DEF names, read at position 1 (#182, decision
C10). The open issue `faec_tp-faixa-de-reserva` of the field says that the DBF exists
and how it differs; `tests/unit/transforms/test_sih_rd_fields.py` compares the column
`rotulo_no_cnv` with the dictionary and the counts above with this file.

**What it does not settle.** Which of the two tables TabWin reads for that line: no
TabWin was run. Position 1 holds under either reading, because the key is the whole
6-character code.
