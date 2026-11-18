"""RD from 2008: the dictionary declares every field the layouts of real files publish (#86).

The census of `SIHSUS/200801_/Dados` (evidence/2026-10-06-rd-2008-layouts/census.csv) has
six layouts, the fifth from 2014-01 and the sixth from 2025-03, which adds FONTE_ORC. One
fixture of each of the last two: RDRR2401 and an excerpt of RDRR2503.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from scripts.gen_dicionario import fields_of

import omnisus as sus
from omnisus.sources.datasus_ftp import dbc
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario

ROOT = Path(__file__).resolve().parents[3]
CENSUS = ROOT / "evidence/2026-10-06-rd-2008-layouts/census.csv"
DATASET = "sih_aih_reduzida"
LAYOUTS = {"sih_rr_2024_01_mini": 5, "sih_rd_rr_2025_03_excerpt": 6}
IT_1603 = ROOT / "evidence/2026-11-18-it-sihsus-1603-layout-rd/tabela1.csv"
RD2008_DEF = ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/RD2008.DEF"
OWN_DESCRIPTION = {"uf_zi", "cnes", "natureza"}
"""Fields whose description is not the document's sentence: `uf_zi` and `cnes` add what
the DEF and the lake say, and `natureza` has a paraphrase with its own verified claim."""


def census_layouts() -> dict[int, set[str]]:
    """Layout number -> its fields, lowercased, from the census."""
    out: dict[int, set[str]] = {}
    with CENSUS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out.setdefault(int(row["layout"]), set()).update(
                name.lower() for name in row["fields"].split(" ")[::2]
            )
    return out


def official_layout() -> list[dict[str, str]]:
    """Table 1 of IT_SIHSUS_1603.pdf (`sihsus-1e89d5f2cc41`), one dict per row."""
    with IT_1603.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def census_widths() -> dict[str, dict[int, tuple[int, int]]]:
    """Text field -> width -> (first, last) layout that publishes it with that width."""
    out: dict[str, dict[int, tuple[int, int]]] = {}
    with CENSUS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            tokens = row["fields"].split(" ")
            for name, descriptor in zip(tokens[::2], tokens[1::2], strict=True):
                if descriptor.startswith("C"):
                    width, layout = int(descriptor[1:].split(".")[0]), int(row["layout"])
                    first, last = out.setdefault(name.lower(), {}).get(width, (layout, layout))
                    out[name.lower()][width] = (min(first, layout), max(last, layout))
    return out


def fixture_fields(dbc_fixture, fixture: str) -> dict[str, str]:
    raw = dbc_fixture(fixture).read_bytes()
    return {f["name"]: f["type"] for f in fields_of(dbc.decompress_bytes(raw))}


def test_the_dictionary_declares_every_field_of_every_layout():
    declared = {f["name"] for f in load_dicionario(DATASET).fields}
    assert sorted(set().union(*census_layouts().values()) - declared) == []


@pytest.mark.parametrize("fixture", sorted(LAYOUTS))
def test_each_fixture_publishes_the_fields_of_its_layout(dbc_fixture, fixture):
    assert set(fixture_fields(dbc_fixture, fixture)) == census_layouts()[LAYOUTS[fixture]]


def test_the_official_layout_lists_the_fields_of_layout_5():
    """IT_SIHSUS_1603 is the report of 2016-03, and its Table 1 has the 113 fields the
    files publish from 2014-01 to 2025-02, once the three names it misspells are read as
    the DBF spells them (MÊS_CMPT, DI_INTER, DESTAO)."""
    rows = official_layout()
    assert len(rows) == 113
    assert {row["campo"] for row in rows} == census_layouts()[5]


def test_each_field_of_the_official_layout_carries_the_documents_description():
    """The description of a field is the sentence Table 1 prints for it, with a claim
    that names the page and quotes the row (#182). The 19 rows that say only "Zerado"
    are described as "Zerado"."""
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    for row in official_layout():
        if row["campo"] in OWN_DESCRIPTION:
            continue
        item = contract[row["campo"]]
        assert item["field"]["description"] == row["descricao"], row["campo"]
        claim = next(c for c in item["claims"] if c["target"] == "/field/description")
        assert (claim["status"], claim["method"]) == ("verified_in_source", "pdf-read")
        (evidence,) = claim["evidence"]
        assert evidence["source_id"] == "sihsus-1e89d5f2cc41"
        assert evidence["pages"] == [int(row["pagina"])]
        assert row["nome_no_documento"] in evidence["locator"]
        assert row["descricao"] in evidence["locator"]


def test_fonte_orc_and_sis_just_are_labelled_as_their_sources_call_them():
    """RD2008.DEF line 274 calls FONTE_ORC "Fonte Orçamentária", and the field had no
    label. IT_SIHSUS_1603, p. 3, says SIS_JUST is the justification of the
    estabelecimento; the dictionary called it "Justificativa do sistema" (#182)."""
    def_line = RD2008_DEF.read_text(encoding="latin-1").splitlines()[273]
    assert [part.strip() for part in def_line.split(",")[:2]] == [
        "XFonte Orçamentária",
        "FONTE_ORC",
    ]
    (sis_just,) = (row for row in official_layout() if row["campo"] == "sis_just")
    assert sis_just["descricao"].startswith("Justificativa do estabelecimento para aceitação")
    dictionary = load_dicionario(DATASET)
    assert dictionary.field_def("fonte_orc")["label"] == "Fonte Orçamentária"
    assert dictionary.field_def("sis_just")["label"] == "Justificativa do estabelecimento"


def test_each_text_field_declares_the_width_the_files_publish():
    """`physical_type` of a C field is its DBF descriptor in the layout in force (6, from
    2025-03), read from the census. The claim is verified where Table 1 of IT_SIHSUS_1603
    prints the same width and conflicting where it prints another; FONTE_ORC is not in
    the document, so its claim stays unreviewed (#182)."""
    printed = {row["campo"]: row["tipo"] for row in official_layout()}
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    for name, widths in census_widths().items():
        (width,) = (w for w, (_, last) in widths.items() if last == 6)
        item = contract[name]
        assert item["field"]["physical_name"] == name.upper()
        assert item["field"]["physical_type"] == {"type": "string", "length": width}, name
        claim = next(c for c in item["claims"] if c["target"] == "/field/physical_type")
        if name not in printed:
            expected = "unreviewed"
        elif printed[name] == f"char({width})":
            expected = "verified_in_source"
        else:
            expected = "conflicting"
        assert claim["status"] == expected, name


def test_the_document_and_the_files_disagree_on_the_width_of_six_text_fields():
    """Printed type in Table 1 against the DBF descriptor of layout 6. Each of the six
    has an open issue that says so; `diagsec9` had it already (#67)."""
    printed = {row["campo"]: row["tipo"] for row in official_layout()}
    differing = {}
    for name, widths in census_widths().items():
        (width,) = (w for w, (_, last) in widths.items() if last == 6)
        if name in printed and printed[name] != f"char({width})":
            differing[name] = (printed[name], width)
    assert differing == {
        "nacional": ("char(2)", 3),
        "raca_cor": ("char(4)", 2),
        "cbor": ("char(3)", 6),
        "gestor_cod": ("char(3)", 5),
        "gestor_cpf": ("char(11)", 15),
        "diagsec9": ("char(4)", 1),
    }
    dictionary = load_dicionario(DATASET)
    for name in differing:
        issues = dictionary.field_def(name)["x-metadata"]["issues"]
        expected = "diagsec9-c1" if name == "diagsec9" else "largura-difere-do-documento"
        assert expected in [i["id"] for i in issues if i["status"] == "open"], name


def test_two_text_fields_change_width_in_2012():
    """GESTOR_COD is C(3) and INSC_PN C(10) in layouts 1 and 2 (2008-01 to 2011-12), and
    C(5) and C(12) from layout 3 on; no other text field changes width. The contract
    holds one `physical_type` per field, so the claim's note carries the older width."""
    changing = {name: widths for name, widths in census_widths().items() if len(widths) > 1}
    assert changing == {
        "gestor_cod": {3: (1, 2), 5: (3, 6)},
        "insc_pn": {10: (1, 2), 12: (3, 6)},
    }
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    for name, widths in changing.items():
        claim = next(c for c in contract[name]["claims"] if c["target"] == "/field/physical_type")
        assert f"C({min(widths)})" in claim["note"]
        assert "2011-12" in claim["note"]


def test_fonte_orc_takes_the_labels_of_fonterem(dbc_fixture):
    """RD2008.DEF line 274 binds FONTE_ORC to CNV/fonterem.CNV at position 1. The table
    names 01-04, each also as '1' and ' 1', and opens with the literal key '  -zz' (#24);
    '00', the only value of the excerpt, is not a key, and the field's issue says so."""
    published = fixture_fields(dbc_fixture, "sih_rd_rr_2025_03_excerpt")
    field = load_dicionario(DATASET).field_def("fonte_orc")
    assert field["type"] == published["fonte_orc"]
    labels = {
        "01": "MOD.1-SERVICO DE SAUDE - AES",
        "02": "MOD.2-EQUIPE VOLANTES-AES",
        "03": "CREDITO FINANC.PARC.VENCIDAS E VICENDAS",
        "04": "CREDITO FINANCEIRO TRANSACAO TRIBUTARIA",
    }
    expected = {"  -zz": "Branco Ignorado"}
    for code, label in labels.items():
        expected |= {code: label, code[1]: label, f" {code[1]}": label}
    assert field["x-decode"] == expected
    (claim,) = (c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes")
    assert claim["method"] == "cnv-parse"
    assert "FONTE_ORC, 1, CNV/fonterem.CNV" in claim["evidence"][0]["locator"]
    assert [i["id"] for i in field["x-metadata"]["issues"]] == ["fonte_orc-00-sem-fonte"]


def test_uf_zi_is_the_gestor_municipality(dbc_fixture):
    """RD2008.DEF lines 175-176 call UF_ZI 'Município gestor' (CNV/br_municgestor.cnv),
    and RDRR2401 publishes it with 6 digits, the width of a municipality code; the
    dictionary called it "UF do gestor" (#155)."""
    def_lines = (
        (ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/RD2008.DEF")
        .read_text(encoding="latin-1")
        .splitlines()
    )
    assert [line.split(",")[0][1:].strip() for line in def_lines[174:176]] == [
        "Município gestor",
        "Município gestor",
    ]
    raw = dbc_fixture("sih_rr_2024_01_mini").read_bytes()
    values = dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect()["uf_zi"]
    assert values.str.contains(r"^\d{6}$").all()
    assert load_dicionario(DATASET).field_def("uf_zi")["label"] == "Município gestor"


COD_IDADE = {"2": "Dias", "3": "Meses", "4": "Anos", "5": "Anos (somar 100)"}


@pytest.mark.parametrize(
    ("dataset", "fixture", "def_member", "def_lines", "published"),
    [
        (
            "sih_aih_reduzida",
            "sih_rr_2024_01_mini",
            "RD2008.DEF",
            range(188, 192),
            {"2": 157, "3": 175, "4": 3378, "5": 4},
        ),
        (
            "sih_aih_rejeitada",
            "sih_rj_rr_2024_01_mini",
            "RJ2008.DEF",
            range(193, 197),
            {"2": 4, "3": 4, "4": 22},
        ),
    ],
)
def test_cod_idade_labels_the_measured_units(
    dbc_fixture, dataset, fixture, def_member, def_lines, published
):
    """#6: the RD and RJ DEF bind COD_IDADE to IDADEBAS, IDADEPUB, IDADE18 and IDADEDET.CNV,
    which read 3 characters (unit + age); IDADEDET has 2xx days, 3xx months, 4xx years,
    500-530 "100 anos" to "130 anos" and 000 "Idade inválida". The 1-character unit is
    measured, not read: '5' is a year to add to 100, and '0' gets no label (no source says
    "Ignorada"; no SIH fixture publishes '0', so that part is checked on the dictionary).
    The RJ had no map and takes the same one."""
    text = (ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih" / def_member).read_text(
        encoding="latin-1"
    )
    bound = [text.splitlines()[n - 1].split(",") for n in def_lines]
    assert [(f.strip(), t.strip()) for _, f, _, t in bound] == [
        ("COD_IDADE", f"CNV\\{cnv}.CNV") for cnv in ("IDADEBAS", "IDADEPUB", "IDADE18", "IDADEDET")
    ]
    raw = dbc_fixture(fixture).read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=dataset).collect().select("cod_idade")
    assert dict(frame["cod_idade"].value_counts().rows()) == published
    labelled = sus.label(dataset, frame, columns=["cod_idade"])
    assert dict(labelled.unique().rows()) == {code: COD_IDADE[code] for code in published}
    field = load_dicionario(dataset).field_def("cod_idade")
    assert field["x-decode"] == COD_IDADE
    (claim,) = (c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes")
    assert claim["status"] == "unreviewed"
    assert "sih-tab-714ed980d483" in {e["source_id"] for e in claim["evidence"]}
    (entry,) = field["x-metadata"]["issues"]
    assert (entry["id"], entry["status"]) == ("cod_idade-sem-tabela", "open")
    assert all(s in entry["description"] for s in ("IDADEDET.CNV", "IDADEBAS.CNV", "'0'"))
