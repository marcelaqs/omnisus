"""SIH: the dictionaries against the DBF header of every file the server lists (#182).

`evidence/2026-11-19-sih-cabecalhos` has the header of each `SP*.dbc` and `RJ*.dbc` of
`SIHSUS/200801_/Dados` as listed on 2026-11-19: the field descriptors, with no record
read. A fixture shows one month of one UF; the headers show every layout a dictionary
has to cover. `SP` and `RJ` have no fixture of 2025-03 on, when both gain `FONTE_ORC`.
"""

from __future__ import annotations

import csv
from importlib.resources import files
from pathlib import Path

import pytest

from omnisus.transforms.dictionaries import load_dicionario

ROOT = Path(__file__).resolve().parents[3]
HEADERS = ROOT / "evidence/2026-11-19-sih-cabecalhos"
CNV = files("omnisus.data.dicionarios") / "sources" / "cnv"
# The columns the import adds; a dictionary may declare them, and no file has them.
LIBRARY_COLUMNS = {"ano", "mes", "uf", "_source_release"}
CENSUSES = [("sih_servicos_profissionais", "sp"), ("sih_aih_rejeitada", "rj")]


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def layouts(name: str) -> dict[str, dict[str, str]]:
    """Layout number -> {field, lowercased: descriptor such as "C2.0"}."""
    out = {}
    for row in read(HEADERS / f"{name}.layouts.csv"):
        words = row["fields"].split(" ")
        out[row["layout"]] = {
            field.lower(): spec for field, spec in zip(words[::2], words[1::2], strict=True)
        }
    return out


def family(spec: str) -> str:
    """The `type` a descriptor is staged as: `dbf_batches._arrow_type`."""
    if spec[0] == "N":
        return "number" if int(spec.split(".")[1]) else "integer"
    return {"C": "string", "F": "number"}[spec[0]]


def month(file: str) -> str:
    return f"20{file[4:6]}-{file[6:8]}"


def pt(number: int) -> str:
    """6072 -> "6.072", as the issues write numbers."""
    return f"{number:,}".replace(",", ".")


@pytest.mark.parametrize(("dataset", "census"), CENSUSES)
def test_the_dictionary_declares_every_field_a_file_publishes(dataset, census):
    published = {field for layout in layouts(census).values() for field in layout}
    declared = {f["name"] for f in load_dicionario(dataset).fields}
    assert published - declared == set()
    assert declared - published <= LIBRARY_COLUMNS


@pytest.mark.parametrize(("dataset", "census"), CENSUSES)
def test_each_field_declares_the_type_every_layout_stages(dataset, census):
    """A field is text, a whole number or a number with decimals in every layout that has
    it, and that is its `type`; a `date` is text in the file."""
    declared = {f["name"]: f["type"] for f in load_dicionario(dataset).fields}
    assert {
        (number, field, declared[field], family(spec))
        for number, layout in layouts(census).items()
        for field, spec in layout.items()
        if declared[field] != family(spec)
        and (declared[field], family(spec)) != ("date", "string")
    } == set()


@pytest.mark.parametrize(
    ("dataset", "census", "member", "files_with_it"),
    [
        ("sih_servicos_profissionais", "sp", "sih/SP2008.DEF", 510),
        ("sih_aih_rejeitada", "rj", "sih/RJ2008.DEF", 510),
    ],
)
def test_fonte_orc_is_declared_from_the_headers_and_takes_no_label(
    dataset, census, member, files_with_it
):
    """`FONTE_ORC C(2)` is the last field of every file from 2025-03 on and of none before.
    `RD2008.DEF` names the RD's `FONTE_ORC`; the DEF of this dataset does not name the
    field, so the map the RD has is not this field's (a map needs a DEF line)."""
    with_it = {number for number, layout in layouts(census).items() if "fonte_orc" in layout}
    assert {layouts(census)[number]["fonte_orc"] for number in with_it} == {"C2.0"}
    assert all(list(layouts(census)[number])[-1] == "fonte_orc" for number in with_it)
    rows = read(HEADERS / f"{census}.csv")
    months = {month(row["file"]) for row in rows if row["layout"] in with_it}
    assert min(months) == "2025-03"
    assert months == {month(row["file"]) for row in rows if month(row["file"]) >= "2025-03"}
    assert sum(row["layout"] in with_it for row in rows) == files_with_it

    assert "FONTE_ORC" in (CNV / "sih/RD2008.DEF").read_bytes().decode("cp850")
    assert "FONTE_ORC" not in (CNV / member).read_bytes().decode("cp850").upper()
    field = load_dicionario(dataset).field_def("fonte_orc")
    assert field["type"] == "string"
    assert "x-decode" not in field and "label" not in field
    (issue,) = field["x-metadata"]["issues"]
    assert (issue["id"], issue["status"]) == ("fonte_orc-sem-def", "open")
    text = issue["description"]
    assert f"{files_with_it} arquivos" in text and "2025-03" in text
    assert f"os {pt(len(rows))} arquivos" in text
    assert f"nenhum dos {pt(len(rows) - files_with_it)} anteriores" in text
    assert member.split("/")[1] in text and "evidence/2026-11-19-sih-cabecalhos" in text


def test_the_rj_files_read_publish_one_value_of_fonte_orc_which_fonterem_does_not_list():
    """The 18 `RJRR` files of 2025-03 to 2026-08 were read whole, and `rj_fonte_orc.csv`
    has their SHA-256 and the rows per value. No SP file was: it names the professional."""
    rows = read(HEADERS / "rj_fonte_orc.csv")
    listed = {row["file"]: row for row in read(HEADERS / "rj.csv")}
    assert {row["size_bytes"] for row in rows if row["file"] not in listed} == set()
    assert all(row["size_bytes"] == listed[row["file"]]["size_bytes"] for row in rows)
    assert all(row["records"] == listed[row["file"]]["records"] for row in rows)
    assert len({row["file"] for row in rows}) == 18
    assert {row["fonte_orc"] for row in rows} == {"00"}
    assert sum(int(row["rows"]) for row in rows) == 1270
    assert "00" not in load_dicionario("sih_aih_reduzida").field_def("fonte_orc")["x-decode"]
    (issue,) = load_dicionario("sih_aih_rejeitada").field_def("fonte_orc")["x-metadata"]["issues"]
    assert (
        "Nos 18 arquivos RJRR de 2025-03 a 2026-08, os 1.270 registros têm '00'"
        in (issue["description"])
    )
