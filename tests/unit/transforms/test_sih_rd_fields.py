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
OLDER_CLAIMS = {"nasc", "sexo", "dt_inter", "dt_saida", "gestor_dt", "diagsec9"}
"""Fields whose `/field/physical_type` claim predates #182 and words its locator and note
another way; their width and status are checked like the others."""
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
    files publish from 2014-01 to 2025-02, in the order of the DBF header, once the three
    names it misspells are read as the DBF spells them (MÊS_CMPT, DI_INTER, DESTAO)."""
    rows = official_layout()
    assert len(rows) == 113
    assert {row["campo"] for row in rows} == census_layouts()[5]
    with CENSUS.open(encoding="utf-8", newline="") as f:
        (in_file_order,) = {row["fields"] for row in csv.DictReader(f) if row["layout"] == "5"}
    assert [row["campo"] for row in rows] == [
        name.lower() for name in in_file_order.split(" ")[::2]
    ]
    assert [
        row["nome_no_documento"]
        for row in rows
        if row["campo"] != row["nome_no_documento"].lower()
    ] == ["MÊS_CMPT", "DI_INTER", "DESTAO"]


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
        assert evidence["locator"] == (
            f"Tabela 1, linha {row['seq']}, {row['nome_no_documento']} {row['tipo']}: "
            f'"{row["descricao"]}"'
        )


def test_the_fields_the_document_calls_zerado_are_empty_in_rdrr2401(dbc_fixture):
    """Table 1 says only "Zerado" of 19 fields. In RDRR2401 the 17 numeric ones are 0 in
    every record, and the two text ones, NUM_PROC and CPF_AUT, are blank, not zeros."""
    zerado = [row["campo"] for row in official_layout() if row["descricao"] == "Zerado"]
    assert len(zerado) == 19
    raw = dbc_fixture("sih_rr_2024_01_mini").read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect().select(zerado)
    values = {name: frame[name].unique().to_list() for name in zerado}
    assert {name: found for name, found in values.items() if found != [0]} == {
        "num_proc": [""],
        "cpf_aut": [""],
    }


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
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    expected = {
        "fonte_orc": (
            "Fonte Orçamentária",
            "RD2008.DEF, linha 274: XFonte Orçamentária, FONTE_ORC",
        ),
        "sis_just": (
            "Justificativa do estabelecimento",
            'SIS_JUST char (50): "Justificativa do est',
        ),
    }
    for name, (label, quoted) in expected.items():
        assert contract[name]["field"]["label"] == label
        claim = next(c for c in contract[name]["claims"] if c["target"] == "/field/label")
        assert claim["status"] == "verified_in_source"
        assert quoted in claim["evidence"][0]["locator"]


def census_files() -> dict[str, dict[int, list[str]]]:
    """Text field -> width -> months of the files that publish it with that width."""
    out: dict[str, dict[int, list[str]]] = {}
    with CENSUS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            tokens = row["fields"].split(" ")
            for name, descriptor in zip(tokens[::2], tokens[1::2], strict=True):
                if descriptor.startswith("C"):
                    width = int(descriptor[1:].split(".")[0])
                    out.setdefault(name.lower(), {}).setdefault(width, []).append(row["month"])
    return out


def printed_widths() -> dict[str, int]:
    """Text field -> the N of the `char(N)` that Table 1 of IT_SIHSUS_1603 prints."""
    return {
        row["campo"]: int(row["tipo"].replace(" ", "")[5:-1])
        for row in official_layout()
        if row["tipo"].startswith("char")
    }


def header_widths(raw: bytes) -> dict[str, int]:
    """C field -> width, from the 32-byte field descriptors of a DBF header."""
    out = {}
    for start in range(32, int.from_bytes(raw[8:10], "little") - 1, 32):
        descriptor = raw[start : start + 32]
        if descriptor[11:12] == b"C":
            out[descriptor[:11].rstrip(b"\x00").decode("ascii").lower()] = descriptor[16]
    return out


def physical_type_claims() -> dict[str, tuple[dict, dict]]:
    """Field -> (resolved field, its `/field/physical_type` claim)."""
    return {
        item["field"]["name"]: (
            item["field"],
            next(c for c in item["claims"] if c["target"] == "/field/physical_type"),
        )
        for item in sus.describe_dataset(DATASET)["fields"]
    }


def test_each_text_field_declares_the_width_the_files_publish():
    """`physical_type` of a C field is its DBF descriptor in the last layout read (6,
    2025-03 to 2026-07), from the census. The claim is verified where Table 1 of
    IT_SIHSUS_1603 prints the same width and conflicting where it prints another, and it
    cites the row; its note counts the files read with each width. FONTE_ORC is not in
    the document, so its claim is unreviewed and cites only the census (#182)."""
    printed = printed_widths()
    rows = {row["campo"]: row for row in official_layout()}
    resolved = physical_type_claims()
    for name, widths in census_files().items():
        (width,) = (w for w, months in widths.items() if max(months) == "2026-07")
        field, claim = resolved[name]
        assert field["physical_name"] == name.upper()
        assert field["physical_type"] == {"type": "string", "length": width}, name
        if name not in printed:
            assert (claim["status"], claim["evidence"]) == ("unreviewed", []), name
        else:
            expected = "verified_in_source" if printed[name] == width else "conflicting"
            assert claim["status"] == expected, name
        if name in OLDER_CLAIMS:
            continue
        if name in printed:
            (evidence,) = claim["evidence"]
            assert evidence["pages"] == [int(rows[name]["pagina"])], name
            assert evidence["locator"] == (
                f"Tabela 1, linha {rows[name]['seq']}, {rows[name]['nome_no_documento']} "
                f"{rows[name]['tipo']}"
            ), name
        for other, months in widths.items():
            assert f"C({other}) nos {len(months)} " in claim["note"], name
            assert f"de {min(months)} a {max(months)}" in claim["note"], name


@pytest.mark.parametrize("fixture", sorted(LAYOUTS))
def test_the_declared_widths_are_those_of_a_real_dbf_header(dbc_fixture, fixture):
    """The census is a transcription; RDRR2401 (layout 5) and RDRR2503 (layout 6) are the
    files. Every C field of their headers has the declared width."""
    published = header_widths(dbc.decompress_bytes(dbc_fixture(fixture).read_bytes()))
    assert set(published) == {n for n in census_files() if n in census_layouts()[LAYOUTS[fixture]]}
    resolved = physical_type_claims()
    assert {name: resolved[name][0]["physical_type"]["length"] for name in published} == published


def test_the_document_and_the_files_disagree_on_the_width_of_seven_text_fields():
    """Printed type in Table 1 against the DBF descriptors of the files read. Six fields
    differ in the last layout; INSC_PN differs only in the files of 2008-01 to 2011-12,
    which the table, "para janeiro de 2008 em diante", also covers. Each has an open
    issue that says so; `diagsec9` had it already (#67)."""
    printed = printed_widths()
    differing = {
        name: (printed[name], sorted(widths))
        for name, widths in census_files().items()
        if name in printed and set(widths) != {printed[name]}
    }
    assert differing == {
        "nacional": (2, [3]),
        "raca_cor": (4, [2]),
        "cbor": (3, [6]),
        "gestor_cod": (3, [3, 5]),
        "gestor_cpf": (11, [15]),
        "insc_pn": (12, [10, 12]),
        "diagsec9": (4, [1]),
    }
    dictionary = load_dicionario(DATASET)
    for name, (doc, widths) in differing.items():
        issues = dictionary.field_def(name)["x-metadata"]["issues"]
        expected = "diagsec9-c1" if name == "diagsec9" else "largura-difere-do-documento"
        (issue,) = (i for i in issues if i["id"] == expected and i["status"] == "open")
        assert f"char({doc})" in issue["description"].replace("char (", "char("), name
        assert all(f"C({width})" in issue["description"] for width in widths), name


def test_two_text_fields_change_width_in_2012():
    """In the files read, GESTOR_COD is C(3) and INSC_PN C(10) from 2008-01 to 2011-12, and
    C(5) and C(12) from 2012-01 on; no other text field changes width. RDRR, RDSP and
    RDMG were read on both sides of the change. The contract holds one `physical_type`
    per field, so the claim's note carries the older width."""
    changing = {
        name: {width: (min(months), max(months)) for width, months in widths.items()}
        for name, widths in census_files().items()
        if len(widths) > 1
    }
    assert changing == {
        "gestor_cod": {3: ("2008-01", "2011-12"), 5: ("2012-01", "2026-07")},
        "insc_pn": {10: ("2008-01", "2011-12"), 12: ("2012-01", "2026-07")},
    }
    with CENSUS.open(encoding="utf-8", newline="") as f:
        read = {
            row["file"][:4] for row in csv.DictReader(f) if row["month"] in ("2011-12", "2012-01")
        }
    assert read == {"RDRR", "RDSP", "RDMG"}


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


MUNICGESTOR = ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/CNV/br_municgestor.cnv"


@pytest.mark.parametrize(
    ("dataset", "fixture", "def_member", "def_lines", "published"),
    [
        (
            "sih_aih_reduzida",
            "sih_rr_2024_01_mini",
            "RD2008.DEF",
            (175, 176),
            {"140000": 2920, "140010": 794},
        ),
        (
            "sih_aih_rejeitada",
            "sih_rj_rr_2024_01_mini",
            "RJ2008.DEF",
            (177, 178),
            {"140000": 10, "140010": 20},
        ),
    ],
)
def test_uf_zi_takes_the_labels_of_br_municgestor(
    dbc_fixture, dataset, fixture, def_member, def_lines, published
):
    """The RD and the RJ DEF bind UF_ZI to CNV/br_municgestor.cnv at position 1, and no
    other line of either names the field. The table gives the code UF0000 of each of the
    26 states the label "<state> - Gestão estadual": RDRR2401 publishes 140000 in 2,920
    of its 3,714 records and 140010 (Boa Vista) in 794. The field holds no reference to
    aux_municipios, where 140000 is "Município ignorado - RR" (#182)."""
    import io
    import json
    import zipfile

    import polars as pl

    text = (MUNICGESTOR.parent.parent / def_member).read_text(encoding="latin-1").splitlines()
    assert [n for n, line in enumerate(text, 1) if "UF_ZI" in line.upper()] == list(def_lines)
    for n in def_lines:
        _, field, start, table = (part.strip() for part in text[n - 1].split(","))
        assert (field, start, table) == ("UF_ZI", "1", "CNV\\br_municgestor.cnv")
    raw = dbc_fixture(fixture).read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=dataset).collect().select("uf_zi")
    assert dict(frame["uf_zi"].value_counts().rows()) == published
    labelled = sus.label(dataset, frame, columns=["uf_zi"])
    assert dict(labelled.unique().rows()) == {
        "140000": "140000 Roraima - Gestão estadual",
        "140010": "140010 Boa Vista",
    }
    field = load_dicionario(dataset).field_def("uf_zi")
    assert "foreignKeys" not in field
    (claim,) = (c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes")
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    assert "UF_ZI" in claim["evidence"][0]["locator"]
    assert claim["evidence"][0]["locator"].endswith("CNV/br_municgestor.cnv")
    vinculos = json.loads(
        (ROOT / "src/omnisus/data/dicionarios/sources/cnv/vinculos.json").read_text("utf-8")
    )["datasets"][dataset]
    assert vinculos["campos"]["uf_zi"] == "sih/CNV/br_municgestor.cnv"
    assert "uf_zi" not in vinculos["sem_cnv"]
    bootstrap = zipfile.ZipFile(ROOT / "src/omnisus/data/auxiliares-bootstrap.zip")
    municipios = pl.read_parquet(io.BytesIO(bootstrap.read("aux_municipios.parquet")))
    assert municipios.filter(pl.col("codigo_6") == "140000")["nome"].to_list() == [
        "Município ignorado - RR"
    ]


def test_br_municgestor_writes_ranges_in_a_table_of_long_codes():
    """TabWin.pdf (pp. 90-91) documents `first-last` only for variables of up to 4
    characters. br_municgestor.cnv declares 6 and writes ranges on three lines (Rio de
    Janeiro, São Paulo, Distrito Federal), which the map expands: 10,087 of its 15,731
    keys are labelled only through them. The field's open issue says so, in both
    datasets. Read from the packaged table, line by line."""
    header, *body = MUNICGESTOR.read_text(encoding="latin-1").splitlines()
    assert header.split() == ["5596", "6"]
    explicit: set[str] = set()
    ranged: set[str] = set()
    with_range = []
    for line in body:
        for token in line[60:].strip().rstrip(",").split(","):
            if "-" in token:
                first, last = token.split("-")
                ranged.update(f"{n:06d}" for n in range(int(first), int(last) + 1))
                with_range.append(line[9:59].strip())
            else:
                explicit.add(token)
    assert sorted(set(with_range)) == [
        "330455 Rio de Janeiro",
        "355030 São Paulo",
        "530000 Distrito Federal",
    ]
    assert len(ranged - explicit) == 10087
    assert sum("Gestão estadual" in line for line in body) == 26
    for dataset in ("sih_aih_reduzida", "sih_aih_rejeitada"):
        field = load_dicionario(dataset).field_def("uf_zi")
        assert set(field["x-decode"]) == explicit | ranged
        assert len(field["x-decode"]) == 15731
        assert field["x-decode"]["149999"] == "140000 Roraima - Gestão estadual"
        assert field["x-decode"]["530010"] == "530000 Distrito Federal"
        (issue,) = field["x-metadata"]["issues"]
        assert (issue["id"], issue["status"]) == ("uf_zi-faixa-em-codigo-longo", "open")
        assert "10.087 das 15.731" in issue["description"]


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
