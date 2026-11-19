"""What 186 DO files of ten states hold in the fields a decision of #184 rests on.

`evidence/2026-11-18-sim-valores-do/` counts the values of every coded field of
`sim_obitos`, and the shape of a few others, in the files of AC, AP, DF, RR, SE and TO of
every year from 1996 to 2024 and of BA, PA, RS and SP of 2006, 2015 and 2023: 2,557,540
records, each file listed with its SHA-256.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pytest

import omnisus as sus

EVIDENCE = Path(__file__).resolve().parents[2] / "evidence/2026-11-18-sim-valores-do"
CITATION = "evidence/2026-11-18-sim-valores-do"

# Values the files hold and the map does not label, by field: {value: records}.
NOT_IN_THE_MAP = {
    "acidtrab": {"0": 20, "3": 135, "4": 2},
    "assistmed": {"0": 16},
    "atestante": {"0": 4},
    "circobito": {"0": 18},
    "cirurgia": {"0": 4},
    "esc": {"0": 3330, "8": 3836, "A": 4958},
    "escmae": {"0": 364, "8": 1125, "A": 1007},
    "exame": {"0": 4},
    "fonte": {"0": 18},
    "gestacao": {"0": 35, "7": 21, "8": 3214, "A": 2},
    "gravidez": {"0": 35},
    "necropsia": {"0": 4},
    "obitograv": {"0": 35},
    "obitopuerp": {"8": 108},
    "parto": {"0": 35},
    "tpmorteoco": {"6": 1},
    "versaoscb": {"4.880": 53},
}


def _counts(kind: str) -> dict[str, Counter[str]]:
    found: dict[str, Counter[str]] = {}
    with (EVIDENCE / "valores.csv").open(encoding="utf-8", newline="") as rows:
        for row in csv.DictReader(rows):
            if row["kind"] == kind:
                found.setdefault(row["field"], Counter())[row["value"]] += int(row["records"])
    return found


def _fields() -> dict[str, dict]:
    return {c["field"]["name"]: c for c in sus.describe_dataset("sim_obitos")["fields"]}


def _issue(name: str, issue: str) -> str:
    (found,) = [i for i in _fields()[name]["issues"] if i["id"] == issue]
    return found["description"]


def test_the_files_are_listed_with_their_hash() -> None:
    with (EVIDENCE / "arquivos.csv").open(encoding="utf-8", newline="") as rows:
        files = list(csv.DictReader(rows))
    assert len(files) == 186 and all(len(f["sha256"]) == 64 for f in files)
    assert sum(int(f["records"]) for f in files) == 2_557_540
    assert Counter(f["file"].upper()[2:4] for f in files) == {
        **dict.fromkeys(["AC", "AP", "DF", "RR", "SE", "TO"], 29),
        **dict.fromkeys(["BA", "PA", "RS", "SP"], 3),
    }


def test_every_value_outside_a_map_is_listed_here() -> None:
    """A value with no label stays as published (AGENTS.md invariant); this is the full list."""
    fields = _fields()
    outside = {}
    for name, counts in _counts("value").items():
        labelled = {c["value"] for c in fields[name]["field"]["codes"]}
        extra = {v: n for v, n in counts.items() if v.strip() and v not in labelled}
        if extra:
            outside[name] = extra
    assert outside == NOT_IN_THE_MAP


def test_tppos_is_never_the_1_or_2_of_the_document() -> None:
    assert set(_counts("value")["tppos"]) == {"", "N", "S"}
    assert CITATION in _issue("tppos", "tppos-codigos-divergem-do-pdf")


@pytest.mark.parametrize("name", ["seriescfal", "seriescmae"])
def test_no_file_holds_the_0_or_9_of_seriefal_cnv(name) -> None:
    assert set(_counts("value")[name]) == {"", *"12345678"}
    assert CITATION in _issue(name, "seriefal-cnv-lista-0-e-9")


def test_horaobito_is_four_digits_in_every_year() -> None:
    shapes = _counts("shape")["horaobito"]
    assert shapes["9999"] == 2_185_721 and shapes["99:99"] == 0 and shapes["99999"] == 8
    assert CITATION in _issue("horaobito", "horaobito-formato-diverge-do-pdf")


def test_codestab_is_seven_digits_in_every_year() -> None:
    shapes = _counts("shape")["codestab"]
    assert {s for s in shapes if s} == {"9999999", "AAAAA"} and shapes["AAAAA"] == 1
    assert CITATION in _issue("codestab", "codestab-tamanho-diverge-do-pdf")


def test_origem_is_written_with_one_digit() -> None:
    """`1`, `2` and `3`, as the 12/2019 edition writes them; never `01`, and no `9`."""
    assert set(_counts("value")["origem"]) == {"", "1", "2", "3"}


def test_esc2010_holds_only_the_seven_codes_of_the_document() -> None:
    assert set(_counts("value")["esc2010"]) == {"", *"0123459"}
    assert set(_counts("value")["escmae2010"]) <= {"", *"0123459"}


@pytest.mark.parametrize("name", ["ocup", "ocupmae"])
def test_occupation_changes_from_five_to_six_characters_in_2006(name) -> None:
    by_year: dict[str, set[str]] = {}
    with (EVIDENCE / "valores.csv").open(encoding="utf-8", newline="") as rows:
        for row in csv.DictReader(rows):
            if (row["field"], row["kind"]) == (name, "shape") and row["value"]:
                by_year.setdefault(row["year"], set()).add(row["value"])
    assert all(by_year[str(y)] == {"99999"} for y in range(1996, 2006))
    assert by_year["2006"] == {"99999", "999999"}
    assert all(by_year[str(y)] == {"999999"} for y in range(2007, 2025))
