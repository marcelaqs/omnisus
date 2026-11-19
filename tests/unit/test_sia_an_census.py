"""The AN dictionary against the census of every AN file the server lists (#183).

``evidence/2026-11-18-censo-sia-an/`` holds what was read on 2026-11-18 from the 2,145
files ``AN*.dbc`` of ``SIASUS/200801_/Dados``: one row per file with its SHA-256
(``files.csv``), the records per published value of ten fields (``values.csv``) and how
the six dates read (``dates.csv``). The files are not committed. The two that are, as
fixtures, tie the census to real bytes: their SHA-256 in ``tests/fixtures/FIXTURES.md``
and their two DBF headers, which are the only two of the census. The other tests check
that what the dictionary says of each field is what the census tables hold; they do not
read the 2,143 other files.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

import pytest

from omnisus.sources.datasus_ftp.dbc import decompress_bytes
from omnisus.sources.datasus_ftp.dbf_contract import _read_field_descriptors
from omnisus.transforms.dictionaries import _lookup_decode, load_dicionario
from tests.unit.test_fixture_provenance import load_fixture_rows

AN = "sia_apac_nefrologia"
FOLDER = "evidence/2026-11-18-censo-sia-an"
CENSUS = Path(__file__).resolve().parents[2] / FOLDER
DATES = ["ap_dtinic", "ap_dtfim", "ap_dtsolic", "ap_dtaut", "ap_dtocor", "an_dtpdr"]


def _rows(name: str) -> list[dict[str, str]]:
    with (CENSUS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _values(field: str) -> dict[str, int]:
    return {r["value"]: int(r["records"]) for r in _rows("values.csv") if r["field"] == field}


def _issue(field: str, issue_id: str) -> str:
    issues = load_dicionario(AN).field_def(field)["x-metadata"].get("issues", [])
    (issue,) = [i for i in issues if i["id"] == issue_id]
    assert issue["status"] == "open"
    assert FOLDER in issue["description"], (field, issue_id)
    return issue["description"]


def test_the_census_rows_of_the_two_fixtures_are_the_files_fixtures_md_records() -> None:
    files = {r["file"]: r for r in _rows("files.csv")}
    assert len(files) == 2145
    assert sum(int(r["records"]) for r in files.values()) == 6534272
    checked = 0
    for row in load_fixture_rows():
        name = row["source"].rsplit("/", 1)[-1]
        if not row["file"].startswith("dbc/sia_an_"):
            continue
        census = files[name]
        assert (census["sha256"], census["listed"]) == (
            row["source_sha256"],
            row["server_modified"],
        )
        assert census["records"] == row["records"]
        checked += 1
    assert checked == 2


@pytest.mark.parametrize(
    ("field", "unlabelled"),
    [
        ("ap_ufdif", {}),
        ("ap_mndif", {}),
        ("ap_tippre", {}),
        ("ap_coidade", {"0": 18}),
        (
            "ap_ufnacio",
            {
                "000": 122,
                " 01": 39,
                "39": 12,
                "24": 10,
                "050": 7,
                "": 5,
                "41": 2,
                "95": 2,
                "43": 1,
                " 04": 1,
                "001": 1,
            },
        ),
    ],
)
def test_the_issue_names_every_published_value_the_map_does_not_label(field, unlabelled) -> None:
    decode = load_dicionario(AN).field_def(field)["x-decode"]
    measured = {v: n for v, n in _values(field).items() if _lookup_decode(decode, v) is None}
    assert measured == unlabelled
    issues = load_dicionario(AN).field_def(field)["x-metadata"].get("issues", [])
    if not unlabelled:
        assert "codigo-sem-rotulo" not in {i["id"] for i in issues}
        return
    text = _issue(field, "codigo-sem-rotulo")
    for value, count in unlabelled.items():
        assert (f"'{value}' ({count})" if value else f"branco ({count})") in text


def test_ap_coidade_2_3_and_5_are_measured_in_an_files() -> None:
    values = _values("ap_coidade")
    text = _issue("ap_coidade", "ap_coidade-sem-tabela")
    assert "não foram medidos em arquivo AN" not in text
    for code in "2345":
        assert f"'{code}' em {values[code]}" in text


def test_ap_natjur_is_in_the_files_of_two_months_and_filled_in_two_records(dbc_fixture) -> None:
    """The census has two headers, and they are the headers of the two fixtures: ANRR1401's
    60 fields, ending in AN_HB, and ANPA1410's 61, ending in AP_NATJUR. Neither has a field
    named AP_NAT_JUR, the name the DEF writes."""
    headers = {}
    for fixture in ("sia_an_rr_2014_01_mini", "sia_an_pa_2014_10_mini"):
        raw = decompress_bytes(dbc_fixture(fixture).read_bytes())
        names = [d.name.strip() for d in _read_field_descriptors(raw)]
        assert "AP_NAT_JUR" not in names
        headers[hashlib.sha256(",".join(names).encode()).hexdigest()] = names
    assert sorted((len(n), n[-1]) for n in headers.values()) == [(60, "AN_HB"), (61, "AP_NATJUR")]
    files = _rows("files.csv")
    assert {r["header_sha256"] for r in files} == set(headers)
    for row in files:
        names = headers[row["header_sha256"]]
        assert (int(row["fields"]), row["ap_natjur"]) == (
            len(names),
            str(int("AP_NATJUR" in names)),
        )
    months = Counter(r["file"][4:8] for r in files if r["ap_natjur"] == "1")
    assert months == {"1112": 27, "1410": 1}
    assert [r["file"] for r in files if r["file"][4:8] == "1410"] == ["ANPA1410.dbc"]
    assert _values("ap_natjur") == {"": 87203, "3999": 2}
    text = _issue("ap_natjur", "ap_natjur-nem-sempre-publicado")
    assert "não se sabe em que mês" not in text
    assert "2011-12" in text and "87203" in text


def test_ap_mndif_is_1_in_every_record_and_ap_ufdif_only_0_and_1() -> None:
    assert _values("ap_mndif") == {"1": 6534272}
    assert set(_values("ap_ufdif")) == {"0", "1"}
    mndif = _issue("ap_mndif", "informe-diverge-do-arquivo")
    assert "6534272" in mndif and "não foi lido" not in mndif and "SIMNAO.CNV" in mndif
    ufdif = _issue("ap_ufdif", "informe-diverge-do-arquivo")
    assert all(str(n) in ufdif for n in _values("ap_ufdif").values())


def test_ap_mvm_is_the_month_of_the_file_name_and_ap_cmp_a_year_and_a_month() -> None:
    """``values.csv`` adds the files up, so the check is by month: each value of AP_MVM is in
    exactly the files named after that month, with exactly their records."""
    by_month: dict[str, list[int]] = {}
    for row in _rows("files.csv"):
        by_month.setdefault("20" + row["file"][4:8], []).append(int(row["records"]))
    rows = [r for r in _rows("values.csv") if r["field"] == "ap_mvm"]
    assert {r["value"]: (int(r["records"]), int(r["files"])) for r in rows} == {
        month: (sum(records), len(records)) for month, records in by_month.items()
    }
    assert len(_values("ap_cmp")) == 79
    assert all(re.fullmatch(r"20\d\d(0[1-9]|1[0-2])", value) for value in _values("ap_cmp"))


@pytest.mark.parametrize("field", DATES)
def test_the_dates_say_how_many_values_the_census_read_as_yyyymmdd(field) -> None:
    """ "Reads as yyyyMMdd" is eight digits with a calendar month and day in any year from
    0001 to 9999, so a year such as 0008 or 9153 reads; the issue counts those apart."""
    (row,) = [r for r in _rows("dates.csv") if r["field"] == field]
    issues = load_dicionario(AN).field_def(field)["x-metadata"]["issues"]
    said = f"acha {row['filled']} valores preenchidos de {field.upper()}, dos quais {row['yyyymmdd']} leem"
    assert any(said in i["description"] and FOLDER in i["description"] for i in issues)
    outside = int(row["files_with_year_outside_1900_2100"])
    after = int(row["files_with_year_after_2015"])
    if not (outside or after or int(row["not_yyyymmdd"])):
        assert "data-implausivel" not in {i["id"] for i in issues}
        return
    text = _issue(field, "data-implausivel")
    assert f"Os outros {row['not_yyyymmdd']} não leem assim" in text
    assert f"{outside} arquivos têm" in text and f"{after} arquivos ao menos um" in text
    assert f"(anos {row['min'][:4]} a {row['max'][:4]})" in text


@pytest.mark.parametrize("field", ["an_albumi", "an_hb"])
def test_the_two_measures_in_g_percent_have_an_issue_with_what_the_census_counted(field) -> None:
    """The Informe says "em g%" and CHAR (2). The census counts integer zero, integers from 1
    to 9, integers from 10 to 99 and text that is not an integer; it does not say what any
    of them measures, and the dictionary declares no map."""
    bands: Counter[str] = Counter()
    for value, count in _values(field).items():
        text = value.strip()
        number = int(text) if text.isdigit() else None
        bands[
            "text" if number is None else "0" if number == 0 else "1-9" if number < 10 else "10-99"
        ] += count
    assert all(bands.values()) and sum(bands.values()) == 6534272
    text = _issue(field, "escala-sem-documento")
    assert f"{bands['0']} registros com valor inteiro zero" in text
    assert f"{bands['1-9']} com valor inteiro de 1 a 9" in text
    assert f"{bands['10-99']} com valor inteiro de 10 a 99" in text
    assert f"{bands['text']} com texto" in text
    assert "x-decode" not in load_dicionario(AN).field_def(field)
