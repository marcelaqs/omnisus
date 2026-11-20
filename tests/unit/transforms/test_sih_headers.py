"""SIH: the dictionaries against the DBF header of every file the server lists (#182).

`evidence/2026-11-19-sih-cabecalhos` has the header of each `SP*.dbc` and `RJ*.dbc` of
`SIHSUS/200801_/Dados` as listed on 2026-11-19: the field descriptors, with no record
read. A fixture shows one month of one UF; the headers show every layout a dictionary
has to cover. Both prefixes gain `FONTE_ORC` in 2025-03. `sih_rj_rr_2026_08_mini` is an
RJ file that has it; for SP only headers were read here.
"""

from __future__ import annotations

import csv
import hashlib
import struct
from importlib.resources import files
from pathlib import Path

import polars as pl
import pytest

import omnisus as sus
from omnisus.sources.datasus_ftp.library_columns import is_library_field
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario

ROOT = Path(__file__).resolve().parents[3]
HEADERS = ROOT / "evidence/2026-11-19-sih-cabecalhos"
CNV = files("omnisus.data.dicionarios") / "sources" / "cnv"
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
    return {"C": "string"}[spec[0]]


def month(file: str) -> str:
    return f"20{file[4:6]}-{file[6:8]}"


def pt(number: int) -> str:
    """6072 -> "6.072", as the issues write numbers."""
    return f"{number:,}".replace(",", ".")


def issue(dataset: str) -> str:
    field = load_dicionario(dataset).field_def("fonte_orc")
    assert field is not None, f"{dataset} does not declare fonte_orc"
    (found,) = field["x-metadata"]["issues"]
    assert (found["id"], found["status"]) == ("fonte_orc-sem-def", "open")
    return found["description"]


@pytest.mark.parametrize(("dataset", "census"), CENSUSES)
def test_the_dictionary_declares_the_fields_the_files_publish_and_no_other(dataset, census):
    """The columns the import adds are the dictionary's too, and are not the files'."""
    published = {field for layout in layouts(census).values() for field in layout}
    declared = {f["name"] for f in load_dicionario(dataset).fields if not is_library_field(f)}
    assert declared == published


@pytest.mark.parametrize(("dataset", "census"), CENSUSES)
def test_each_field_declares_the_type_every_layout_stages(dataset, census):
    """A field is text, a whole number or a number with decimals in every layout that has
    it, and that is its `type`; a `date` is text in the file."""
    declared = {f["name"]: f["type"] for f in load_dicionario(dataset).fields}
    assert {field for layout in layouts(census).values() for field in layout} <= set(declared)
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
    have_it = {row["file"] for row in rows if row["layout"] in with_it}
    assert have_it == {row["file"] for row in rows if month(row["file"]) >= "2025-03"}
    assert (len(have_it), max(map(month, have_it))) == (files_with_it, "2026-09")

    assert "FONTE_ORC" in (CNV / "sih/RD2008.DEF").read_bytes().decode("latin-1")
    assert "FONTE_ORC" not in (CNV / member).read_bytes().decode("latin-1").upper()
    text = issue(dataset)
    field = load_dicionario(dataset).field_def("fonte_orc")
    assert field["type"] == "string"
    assert "x-decode" not in field and "label" not in field
    assert f"dos {files_with_it} arquivos" in text and "de 2025-03 a 2026-09" in text
    assert f"os {pt(len(rows))} arquivos" in text
    assert f"nenhum dos {pt(len(rows) - files_with_it)} anteriores" in text
    assert member.split("/")[1] in text and "evidence/2026-11-19-sih-cabecalhos" in text


def test_the_rj_files_read_publish_one_value_of_fonte_orc_which_the_rd_map_does_not_label():
    """The 18 `RJRR` files of 2025-03 to 2026-08 were read whole, and `rj_fonte_orc.csv`
    has their SHA-256 and the rows per value. It is the value the RD publishes in its own
    `fonte_orc`, where the map leaves it without a label."""
    rows = read(HEADERS / "rj_fonte_orc.csv")
    listed = {row["file"]: row for row in read(HEADERS / "rj.csv")}
    assert [row["file"] for row in rows] == [
        f"RJRR{m[2:4]}{m[5:]}.dbc"
        for m in sorted({month(file) for file in listed})
        if "2025-03" <= m <= "2026-08"
    ]
    assert all(row["size_bytes"] == listed[row["file"]]["size_bytes"] for row in rows)
    assert all(row["records"] == row["rows"] == listed[row["file"]]["records"] for row in rows)
    assert {row["fonte_orc"] for row in rows} == {"00"}
    assert (len(rows), sum(int(row["rows"]) for row in rows)) == (18, 1270)
    assert "00" not in load_dicionario("sih_aih_reduzida").field_def("fonte_orc")["x-decode"]
    text = issue("sih_aih_rejeitada")
    assert "Nos 18 arquivos RJRR de 2025-03 a 2026-08, os 1.270 registros têm '00'" in text
    assert "fonte_orc-00-sem-fonte" in text


def test_a_real_rj_file_with_fonte_orc_is_staged_and_checked_as_declared(dbc_fixture):
    """RJRR2608, the four records. Before the field was declared, `check_columns` gave it
    the rule "not in dictionary"."""
    raw = dbc_fixture("sih_rj_rr_2026_08_mini").read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset="sih_aih_rejeitada").collect()
    assert frame.shape == (4, 91)
    assert frame.columns[-1] == "fonte_orc" and frame.schema["fonte_orc"] == pl.String
    assert frame["fonte_orc"].unique().to_list() == ["00"]
    report = sus.check_columns("sih_aih_rejeitada", frame)
    assert report.filter(pl.col("rule") == "not in dictionary")["column"].to_list() == []
    (row,) = report.filter(pl.col("column") == "fonte_orc").select("label", "rule").rows()
    assert row == (None, None)
    (measured,) = [r for r in read(HEADERS / "rj_fonte_orc.csv") if r["file"] == "RJRR2608.dbc"]
    assert (measured["fonte_orc"], measured["rows"]) == ("00", "4")


@pytest.mark.parametrize(
    ("census", "file", "fixture"),
    [
        ("sp", "SPRR2401.dbc", "sih_sp_rr_2024_01_mini"),
        ("rj", "RJRR2401.dbc", "sih_rj_rr_2024_01_mini"),
        ("rj", "RJRR2608.dbc", "sih_rj_rr_2026_08_mini"),
    ],
)
def test_header_sha256_is_the_digest_of_the_header_a_fixture_of_the_file_keeps(
    census, file, fixture, dbc_fixture
):
    """The three fixtures keep every record of the server file, and with it its header."""
    (row,) = [r for r in read(HEADERS / f"{census}.csv") if r["file"] == file]
    raw = dbc_fixture(fixture).read_bytes()
    header = raw[: struct.unpack("<H", raw[8:10])[0]]
    assert struct.unpack("<I", header[4:8])[0] == int(row["records"])
    assert hashlib.sha256(header).hexdigest() == row["header_sha256"]
