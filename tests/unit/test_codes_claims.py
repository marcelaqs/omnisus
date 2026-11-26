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
    assert (claim["status"], claim["reviewer"]) == ("unreviewed", None)
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [
        ("sim-b4195ac8e0f8", [page])
    ]
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == f"{name}-rotulo-diverge-do-pdf"
    ]
    assert issue["status"] == "resolved" and "1-5 ano" in issue["description"]


SIA_APAC_WITH_THE_COMMON_BLOCK = [
    "sia_apac_cirurgia_bariatrica",
    "sia_apac_laudos_diversos",
    "sia_apac_medicamentos",
    "sia_apac_quimioterapia",
    "sia_apac_tratamento_dialitico",
]
SIA_APAC_SAME_MEANING = [
    "ap_racacor",
    "ap_ufdif",
    "ap_mndif",
    "ap_tpapac",
    "ap_obito",
    "ap_encerr",
    "ap_perman",
    "ap_alta",
    "ap_transf",
]
SIA_CNV_MAPS_SAME_MEANING = [
    (dataset, name) for dataset in SIA_APAC_WITH_THE_COMMON_BLOCK for name in SIA_APAC_SAME_MEANING
] + [
    ("sia_apac_medicamentos", "am_transpl"),
    ("sia_psicossocial", "racacor"),
    ("sia_psicossocial", "sit_rua"),
]


@pytest.mark.parametrize(("dataset", "name"), SIA_CNV_MAPS_SAME_MEANING)
def test_a_sia_cnv_map_that_says_what_the_older_map_said_is_verified(dataset, name) -> None:
    """A reviewer closed the conflict: the older map had no claim and meant the same."""
    field = _field(dataset, name)
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == "cnv-difere-do-mapa-anterior"
    ]
    assert issue["status"] == "resolved" and "revisora marcelaqs" in issue["description"]


@pytest.mark.parametrize(
    "dataset",
    ["sia_apac_laudos_diversos", "sia_apac_quimioterapia", "sia_apac_tratamento_dialitico"],
)
def test_ap_tpapac_4_stays_an_open_issue(dataset) -> None:
    issues = _field(dataset, "ap_tpapac")["x-metadata"]["issues"]
    assert [i["status"] for i in issues if i["id"] == "ap_tpapac-4-sem-fonte"] == ["open"]


def test_am_gestant_stays_conflicting_because_the_cnv_contradicts_itself() -> None:
    field = _field("sia_apac_medicamentos", "am_gestant")
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == "cnv-difere-do-mapa-anterior"
    ]
    assert (claim["status"], issue["status"]) == ("conflicting", "open")
    assert "GESTANTE.CNV" in issue["description"]
