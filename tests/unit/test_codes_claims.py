"""A code map is either written as a claim or it is not there (#72).

The maintainer's rule: a field with ``x-decode`` has an authored ``/field/codes`` claim, with
its evidence or, when the map was measured and not read, ``method: fixture-measure``,
``unreviewed`` and an open issue on the field; a map no DEF and no registered document backs
is removed, with an issue saying what was consulted.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import omnisus as sus

DICIONARIOS = Path(sus.__file__).parent / "data" / "dicionarios"


def _decoded_fields():
    for path in sorted(DICIONARIOS.glob("*.yaml")):
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
        for field in raw["schema"]["fields"]:
            if field.get("x-decode"):
                yield path.stem, field


@pytest.mark.parametrize(
    ("dataset", "field"), [pytest.param(d, f, id=f"{d}.{f['name']}") for d, f in _decoded_fields()]
)
def test_every_code_map_has_an_authored_codes_claim(dataset, field) -> None:
    claims = (field.get("x-metadata") or {}).get("claims", [])
    (claim,) = [c for c in claims if c["target"] == "/field/codes"]
    if claim["method"] == "fixture-measure":
        issues = (field["x-metadata"]).get("issues", [])
        assert claim["status"] == "unreviewed" and claim["reviewer"] is None
        assert any(i["status"] == "open" for i in issues), "a measured map keeps an open issue"
    else:
        assert claim["evidence"], "a read map cites its source"


def _field(dataset: str, name: str) -> dict:
    raw = yaml.load(
        (DICIONARIOS / f"{dataset}.yaml").read_text(encoding="utf-8"), Loader=yaml.CSafeLoader
    )
    return next(f for f in raw["schema"]["fields"] if f["name"] == name)


@pytest.mark.parametrize(
    ("dataset", "name"),
    [
        ("sim_obitos", "_source_release"),
        ("sih_aih_reduzida", "_source_release"),
    ],
)
def test_a_map_nothing_backs_is_gone(dataset, name) -> None:
    assert "x-decode" not in _field(dataset, name)


@pytest.mark.parametrize(
    ("dataset", "name"),
    [
        ("sinasc_nascidos_vivos", "stdnnova"),
    ],
)
def test_a_label_the_document_contradicts_is_a_conflicting_claim_with_an_issue(
    dataset, name
) -> None:
    field = _field(dataset, name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert claim["status"] == "conflicting" and claim["evidence"]
    assert any(i["status"] == "open" for i in field["x-metadata"]["issues"])


ESC2010_IN_THE_DOCUMENT = {
    "0": "Sem escolaridade",
    "1": "Fundamental I (1ª a 4ª série)",
    "2": "Fundamental II (5ª a 8ª série)",
    "3": "Médio (antigo 2º Grau)",
    "4": "Superior incompleto",
    "5": "Superior completo",
    "9": "Ignorado",
}


@pytest.mark.parametrize(("name", "page"), [("esc2010", 2), ("escmae2010", 3)])
def test_esc2010_labels_are_the_ones_the_estrutura_do_sim_writes(name, page) -> None:
    """The maintainer chose the document over the older labels, which no source had (#184)."""
    field = _field("sim_obitos", name)
    assert field["x-decode"] == ESC2010_IN_THE_DOCUMENT
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["evidence"][0]["source_id"], claim["evidence"][0]["pages"]) == (
        "sim-b4195ac8e0f8",
        [page],
    )
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == f"{name}-rotulo-diverge-do-pdf"
    ]
    assert issue["status"] == "resolved" and "1-5 ano" in issue["description"]


@pytest.mark.parametrize(
    ("name", "page"),
    [("assistmed", 4), ("codificado", 6), ("esc2010", 2), ("escmae2010", 3)],
)
def test_a_human_review_against_the_estrutura_do_sim_verifies_the_codes(name, page) -> None:
    """A reviewer compared the map with the Estrutura do SIM, the one document the claim cites."""
    field = _field("sim_obitos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["status"], claim["reviewer"]) == ("verified_in_source", "marcelaqs")
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [
        ("sim-b4195ac8e0f8", [page]),
    ]
    assert "tabela DO" not in claim["method"]


@pytest.mark.parametrize("name", ["atestante", "tppos"])
def test_a_reviewer_closes_a_conflict_of_wording_between_the_cnv_and_the_document(
    name,
) -> None:
    """The CNV and the Estrutura do SIM name the same answer in other words."""
    field = _field("sim_obitos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["status"], claim["method"]) == ("verified_in_source", "cnv-parse")
    issues = field["x-metadata"]["issues"]
    assert issues and all(i["status"] == "resolved" for i in issues)
    assert all("marcelaqs" in i["description"] for i in issues)


SIM_DICIONARIO_2025 = "sim-2177e17cf20b"


@pytest.mark.parametrize(
    ("name", "page"),
    [("origem", 6), ("tpnivelinv", 8), ("morteparto", 8), ("altcausa", 8), ("tp_altera", 9)],
)
def test_a_human_review_against_the_open_data_edition_verifies_the_codes(name, page) -> None:
    """A reviewer compared the map with the Estrutura do SIM of the open data portal."""
    field = _field("sim_obitos", name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["status"], claim["reviewer"]) == ("verified_in_source", "marcelaqs")
    assert (SIM_DICIONARIO_2025, [page]) in [
        (e["source_id"], e["pages"]) for e in claim["evidence"]
    ]


def test_tpnivelinv_also_cites_the_dictionary_of_table_dom() -> None:
    field = _field("sim_obitos", "tpnivelinv")
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert ("sim-dom-fb396a277981", [2]) in [
        (e["source_id"], e["pages"]) for e in claim["evidence"]
    ]
