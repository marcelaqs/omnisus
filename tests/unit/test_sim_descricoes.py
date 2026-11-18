"""Every `sim_obitos` field says what the Estrutura do SIM says about it (#184).

Two editions are in `sources/registry.json`, nine pages each: 07/2025 (`sim-b4195ac8e0f8`)
and 12/2019 (`sim-b014389eca62`). A field the 2025 edition describes carries that
description with a `/field/description` claim that cites the page; three fields it leaves
blank or out take the 2019 text. The reading was made by an agent, so every claim is
`unreviewed` with no reviewer. A field neither edition describes keeps `description: null`
with a `not_found` claim, which needs the same evidence as a description (AGENTS.md rule 1).
"""

from __future__ import annotations

import pytest

import omnisus as sus
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

ESTRUTURA_2025 = "sim-b4195ac8e0f8"
ESTRUTURA_2019 = "sim-b014389eca62"
EVERY_PAGE = list(range(1, 10))

# Field -> the page of the Estrutura do SIM 2025 whose "Descrição" column describes it.
DESCRIBED = {
    **dict.fromkeys(["tipobito", "dtobito", "horaobito", "codmunnatu", "dtnasc"], 1),
    **dict.fromkeys(["idade", "sexo", "racacor", "estciv", "esc2010", "seriescfal"], 2),
    **dict.fromkeys(
        [
            "codmunres",
            "lococor",
            "codmunocor",
            "idademae",
            "escmae2010",
            "seriescmae",
            "ocupmae",
            "qtdfilvivo",
            "qtdfilmort",
        ],
        3,
    ),
    **dict.fromkeys(
        ["semagestac", "gravidez", "parto", "obitoparto", "tpmorteoco", "assistmed", "necropsia"],
        4,
    ),
    **dict.fromkeys(
        [
            "linhaii",
            "causabas",
            "atestante",
            "comunsvoim",
            "dtatestado",
            "circobito",
            "acidtrab",
            "fonte",
            "esc",
        ],
        5,
    ),
    **dict.fromkeys(
        [
            "escmae",
            "obitograv",
            "obitopuerp",
            "exame",
            "cirurgia",
            "causabas_o",
            "numerolote",
            "dtinvestig",
            "dtcadastro",
            "stcodifica",
            "codificado",
            "versaosist",
            "versaoscb",
            "fonteinv",
            "dtrecebim",
            "atestado",
            "dtrecoriga",
            "opor_do",
            "causamat",
        ],
        6,
    ),
    **dict.fromkeys(
        [
            "escmaeagr1",
            "escfalagr1",
            "stdoepidem",
            "stdonova",
            "difdata",
            "nudiasobco",
            "dtcadinv",
            "dtconinv",
        ],
        7,
    ),
    **dict.fromkeys(
        [
            "fontes",
            "tpresginfo",
            "tpnivelinv",
            "dtcadinf",
            "morteparto",
            "dtconcaso",
            "altcausa",
            "tppos",
        ],
        8,
    ),
    **dict.fromkeys(["gestacao", "cb_alt"], 9),
}

# Blank in the 2025 edition (origem, tpobitocor) or absent from it (cb_pre) -> the page of
# the 2019 edition that describes the field.
DESCRIBED_ONLY_IN_2019 = {"origem": 6, "tpobitocor": 8, "cb_pre": 9}

# In no row of either edition.
NOT_LISTED = [
    "numerodo",
    "contador",
    "estabdescr",
    "fontesinf",
    "ufinform",
    "nudiasobin",
    "nudiasinf",
    "covid_clas",
    "mat_clas",
]

# Described before #184 in the maintainers' words, with no claim; left as they were.
AUTHORED_BEFORE = ["natural", "ocup", "codestab", "peso", "linhaa", "linhab", "linhac", "linhad"]

# Columns the import adds; the document is about the DBF.
ADDED_BY_THE_IMPORT = ["ano", "uf", "_source_release"]


def _columns() -> dict[str, dict]:
    return {c["field"]["name"]: c for c in sus.describe_dataset("sim_obitos")["fields"]}


def _description_claim(column: dict) -> dict:
    (claim,) = [c for c in column["claims"] if c["target"] == "/field/description"]
    return claim


def test_every_field_is_in_exactly_one_group() -> None:
    groups = [
        *DESCRIBED,
        *DESCRIBED_ONLY_IN_2019,
        "tp_altera",
        *NOT_LISTED,
        *AUTHORED_BEFORE,
        *ADDED_BY_THE_IMPORT,
    ]
    assert sorted(groups) == sorted(_columns())


@pytest.mark.parametrize(
    ("name", "source", "page"),
    [
        *((name, ESTRUTURA_2025, page) for name, page in sorted(DESCRIBED.items())),
        *((name, ESTRUTURA_2019, page) for name, page in sorted(DESCRIBED_ONLY_IN_2019.items())),
    ],
)
def test_a_described_field_cites_the_page_and_has_no_reviewer(name, source, page) -> None:
    column = _columns()[name]
    claim = _description_claim(column)
    assert column["field"]["description"]
    assert (claim["status"], claim["reviewer"]) == ("unreviewed", None)
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [(source, [page])]


@pytest.mark.parametrize(
    ("name", "pages_2025"),
    # tp_altera: page 9 of the 2025 edition lists its codes and does not say what it is.
    [("tp_altera", [9]), *((name, EVERY_PAGE) for name in NOT_LISTED)],
)
def test_a_field_neither_edition_describes_is_not_found(name, pages_2025) -> None:
    column = _columns()[name]
    claim = _description_claim(column)
    assert column["field"]["description"] is None
    assert (claim["status"], claim["reviewer"]) == ("not_found", None)
    assert [(e["source_id"], e["pages"]) for e in claim["evidence"]] == [
        (ESTRUTURA_2025, pages_2025),
        (ESTRUTURA_2019, EVERY_PAGE),
    ]


def _open_issue(name: str, issue: str) -> dict:
    (found,) = [i for i in _columns()[name]["issues"] if i["id"] == issue]
    assert found["status"] == "open"
    return found


@pytest.mark.parametrize("fixture", ["sim_rr_2022_mini", "sim_rr_2023_mini"])
def test_horaobito_is_four_digits_where_the_document_says_five_characters(
    dbc_fixture, fixture
) -> None:
    """Real data: DORR2022 and DORR2023 write HHMM, the document says `00:00` in 5 characters."""
    frame = dbc_bytes_to_lazyframe(
        dbc_fixture(fixture).read_bytes(), dataset="sim_obitos"
    ).collect()
    values = {v for v in frame["horaobito"].to_list() if v}
    assert values and all(len(v) == 4 and v.isdigit() for v in values)
    assert "HHMM" in _open_issue("horaobito", "horaobito-formato-diverge-do-pdf")["description"]


def test_nudiasobco_label_differs_from_the_document() -> None:
    column = _columns()["nudiasobco"]
    assert column["field"]["label"] == "Dias óbito-codificação"
    assert "conclusão da investigação" in column["field"]["description"]
    _open_issue("nudiasobco", "nudiasobco-rotulo-diverge-do-pdf")
