"""Which declared `sim_obitos` fields no DO file on the server carries (#184).

`evidence/2026-11-18-sim-colunas-do/colunas.csv` lists the columns of every `DO<UF><year>`
file of `SIM/CID10/DORES` and `SIM/PRELIM/DORES`, read from each DBF header on 2026-11-18.
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


def _files() -> list[dict[str, str]]:
    with EVIDENCE.open(encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def _fields() -> dict[str, dict]:
    return {c["field"]["name"]: c for c in sus.describe_dataset("sim_obitos")["fields"]}


def test_the_evidence_has_every_state_of_every_year() -> None:
    final = [r["file"].upper() for r in _files() if r["directory"].endswith("CID10/DORES")]
    per_year = {year: sum(name[4:8] == str(year) for name in final) for year in range(1996, 2025)}
    assert set(per_year.values()) == {28}  # 27 UF and one more file a year
    assert all(len(r["header_sha256"]) == 64 and r["columns"] for r in _files())


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
