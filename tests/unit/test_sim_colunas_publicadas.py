"""Which declared `sim_obitos` fields no DO file on the server carries (#184).

`evidence/2026-11-18-sim-colunas-do/colunas.csv` lists the columns of every `DO` file of
`SIM/CID10/DORES`, `SIM/PRELIM/DORES` and the two `DOFET` directories, read from each DBF
header on 2026-11-18. The dataset reads the 868 `DO<UF><year>` files of the first two.
A declared field that no file carries stays only if an official layout document describes
it, with an open issue that says so; `numerodo` is one of them, so the dataset declares no
primary key.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

import omnisus as sus
from omnisus.transforms.dictionaries import load_dicionario

EVIDENCE = Path(__file__).resolve().parents[2] / "evidence/2026-11-18-sim-colunas-do/colunas.csv"
ADDED_BY_THE_IMPORT = {"ano", "uf", "_source_release"}
DOCUMENTED_AND_NOT_PUBLISHED = ["cb_alt", "numerodo", "opor_do", "tp_altera"]


def _every_file() -> list[dict[str, str]]:
    with EVIDENCE.open(encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def _files() -> list[dict[str, str]]:
    """The files `sim_obitos` reads: `DO<UF><year>` of the final and preliminary directories."""
    return [r for r in _every_file() if r["directory"].endswith("/DORES")]


def _fields() -> dict[str, dict]:
    return {c["field"]["name"]: c for c in sus.describe_dataset("sim_obitos")["fields"]}


def test_the_evidence_has_every_state_of_every_year() -> None:
    final = [r["file"].upper() for r in _files() if r["directory"].endswith("CID10/DORES")]
    per_year = {year: sum(name[4:8] == str(year) for name in final) for year in range(1996, 2025)}
    assert set(per_year.values()) == {28}
    assert len({name[2:4] for name in final}) == 28  # 27 UF and DOBR
    assert (len(final), len(_files()), len(_every_file())) == (812, 868, 1011)
    assert all(len(r["header_sha256"]) == 64 and r["columns"] for r in _every_file())


def test_one_file_the_dataset_does_not_read_carries_numerodo() -> None:
    wanted = {"NUMERODO", "OPOR_DO", "TP_ALTERA", "CB_ALT", "COVID_CLAS", "MAT_CLAS"}
    found = {r["file"]: wanted & set(r["columns"].upper().split()) for r in _every_file()}
    assert {f: c for f, c in found.items() if c} == {
        "DOREXT21.dbc": {"NUMERODO", "TP_ALTERA", "CB_ALT"}
    }
    assert "DOREXT21.dbc" in _fields()["numerodo"]["issues"][0]["description"]


def test_a_field_no_file_carries_is_one_a_document_describes() -> None:
    published = {name.lower() for row in _files() for name in row["columns"].split()}
    declared = set(_fields()) - ADDED_BY_THE_IMPORT
    assert sorted(declared - published) == DOCUMENTED_AND_NOT_PUBLISHED


@pytest.mark.parametrize("name", DOCUMENTED_AND_NOT_PUBLISHED)
def test_a_documented_field_no_file_carries_says_so(name) -> None:
    (issue,) = [i for i in _fields()[name]["issues"] if i["id"] == "absent-in-audited-snapshot"]
    assert issue["status"] == "open"
    assert "evidence/2026-11-18-sim-colunas-do" in issue["description"]


def test_no_primary_key_while_no_file_carries_numerodo() -> None:
    assert load_dicionario("sim_obitos").primary_key == []
