"""RD: the DBF header of every file, against the two censuses of layouts (#182, #219).

The censuses of `evidence/2026-10-01-rd-1992-2007-layouts` and
`evidence/2026-10-06-rd-2008-layouts` read one UF a month. `evidence/2026-11-19-sih-cabecalhos`
has the header of every `RD*.dbc` the two directories listed on 2026-11-19. The headers
confirm the 19 and the 6 layouts in every UF, and show one file outside them:
`RDAC0909.dbc`, of which `sih_rd_ac_2009_09_excerpt` keeps five records.
"""

from __future__ import annotations

import csv
import hashlib
import struct
from pathlib import Path

import polars as pl
import pyarrow as pa
import pytest

from omnisus.sources.datasus_ftp import dbc
from omnisus.sources.datasus_ftp.dbf_batches import physical_arrow_types
from omnisus.sources.datasus_ftp.inventory import _parse_msdos_line
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario
from tests.support.listings import listing_lines

ROOT = Path(__file__).resolve().parents[3]
HEADERS = ROOT / "evidence/2026-11-19-sih-cabecalhos"
CENSUS_BEFORE_2008 = ROOT / "evidence/2026-10-01-rd-1992-2007-layouts/census.csv"
CENSUS_FROM_2008 = ROOT / "evidence/2026-10-06-rd-2008-layouts/census.csv"
DIRECTORY_BEFORE_2008 = "/dissemin/publicos/SIHSUS/199201_200712/Dados"
LISTING_BEFORE_2008 = "sihsus_199201_200712_dados_rd"
DATASET = "sih_aih_reduzida"
ODD = "RDAC0909.dbc"
# Fields whose descriptor in RDAC0909 is of another type family than in every other file.
VALUES_AS_WHOLE_NUMBERS = {
    "val_sh",
    "val_sp",
    "val_sadt",
    "val_rn",
    "val_acomp",
    "val_ortp",
    "val_sangue",
    "val_sadtsr",
    "val_transp",
    "val_obsang",
    "val_ped1ac",
}
TEXT_AS_WHOLE_NUMBERS = {"num_proc", "cpf_aut", "gestor_cod", "gestor_dt", "infehosp", "faec_tp"}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def layouts(name: str) -> dict[str, str]:
    """Layout number -> its descriptors, as `census.csv` writes them."""
    return {row["layout"]: row["fields"] for row in read(HEADERS / f"{name}.layouts.csv")}


def descriptors(fields: str) -> dict[str, str]:
    words = fields.split(" ")
    return dict(zip((w.lower() for w in words[::2]), words[1::2], strict=True))


def family(spec: str) -> str:
    """The `type` a descriptor is staged as: `dbf_batches._arrow_type`."""
    if spec[0] == "N":
        return "number" if int(spec.split(".")[1]) else "integer"
    return {"C": "string", "F": "number"}[spec[0]]


def month(file: str) -> str:
    year = int(file[4:6])
    return f"{(1900 if year >= 92 else 2000) + year}-{file[6:8]}"


@pytest.mark.parametrize(
    ("name", "census", "files", "records", "sampled", "unchanged"),
    [
        ("rd_1992_2007", CENSUS_BEFORE_2008, 5165, 205_572_316, 260, 260),
        ("rd", CENSUS_FROM_2008, 6072, 227_938_672, 243, 232),
    ],
)
def test_the_headers_have_the_layout_the_census_recorded_in_every_file_both_read(
    name, census, files, records, sampled, unchanged
):
    """A file the census downloaded has, here, the layout the census recorded. The record
    count is the same too where the server still lists the file with the same size and
    time; it replaced 11 of the 243 files from 2008 after that census."""
    rows = {row["file"]: row for row in read(HEADERS / f"{name}.csv")}
    old = read(census)
    assert (len(rows), len(old)) == (files, sampled)
    assert sum(int(row["records"]) for row in rows.values()) == records
    assert {row["file"] for row in old} <= set(rows)
    assert all(layouts(name)[rows[row["file"]]["layout"]] == row["fields"] for row in old)
    same = [
        row
        for row in old
        if (row["size_bytes"], row["server_modified"])
        == (rows[row["file"]]["size_bytes"], rows[row["file"]]["server_modified"])
    ]
    assert len(same) == unchanged
    assert all(row["records"] == rows[row["file"]]["records"] for row in same)


def test_the_layout_numbers_are_the_census_ones_but_for_the_file_apart_from_2008():
    def numbers(census: Path) -> dict[str, str]:
        return {row["fields"]: row["layout"] for row in read(census)}

    before = numbers(CENSUS_BEFORE_2008)
    assert {n: before[fields] for n, fields in layouts("rd_1992_2007").items()} == {
        str(n): str(n) for n in range(1, 20)
    }
    from_2008 = numbers(CENSUS_FROM_2008)
    assert {n: from_2008.get(fields) for n, fields in layouts("rd").items()} == {
        "1": "1",
        "2": None,
        "3": "2",
        "4": "3",
        "5": "4",
        "6": "5",
        "7": "6",
    }


@pytest.mark.parametrize(
    ("census", "file", "fixture"),
    [
        ("rd_1992_2007", "RDRR9412.dbc", "sih_rd_rr_1994_12_mini"),
        ("rd_1992_2007", "RDRR9709.dbc", "sih_rd_rr_1997_09_mini"),
        ("rd_1992_2007", "RDRR0712.dbc", "sih_rd_rr_2007_12_mini"),
        ("rd", "RDRR2401.dbc", "sih_rr_2024_01_mini"),
        ("rd", ODD, "sih_rd_ac_2009_09_excerpt"),
    ],
)
def test_header_sha256_is_the_digest_of_the_header_a_fixture_of_the_file_keeps(
    census, file, fixture, dbc_fixture
):
    """`scripts/dbc_excerpt.py` keeps the server file's header and changes only the record
    count, so with the count the census read the fixture's header is the one hashed."""
    (row,) = [r for r in read(HEADERS / f"{census}.csv") if r["file"] == file]
    raw = dbc_fixture(fixture).read_bytes()
    header = raw[: struct.unpack("<H", raw[8:10])[0]]
    as_served = header[:4] + struct.pack("<I", int(row["records"])) + header[8:]
    assert hashlib.sha256(as_served).hexdigest() == row["header_sha256"]


def test_every_rd_file_of_1992_2007_has_one_of_the_19_layouts_of_the_census():
    """The census read 260 of the 5,165 files. The other 4,905 add no layout, and the files
    are the ones of the listing captured on 2026-10-02 (FIXTURES.md), size and time."""
    assert set(layouts("rd_1992_2007").values()) == {
        row["fields"] for row in read(CENSUS_BEFORE_2008)
    }
    assert len(layouts("rd_1992_2007")) == 19
    entries = (
        _parse_msdos_line(line, DIRECTORY_BEFORE_2008)
        for line in listing_lines(LISTING_BEFORE_2008)
    )
    listed = {e.name: (str(e.size_bytes), f"{e.modified:%Y-%m-%dT%H:%M}") for e in entries if e}
    assert listed == {
        row["file"]: (row["size_bytes"], row["server_modified"])
        for row in read(HEADERS / "rd_1992_2007.csv")
    }


def test_three_fields_of_1992_2007_are_numbers_in_some_months_in_every_uf():
    """#40: NUM_PROC is N in every file of 1996-01 to 1996-07, and INSC_PN and SEQ_AIH5 in
    every file of 2004-07 to 2006-03; in no other file, and no other field changes."""
    by_layout = {number: descriptors(fields) for number, fields in layouts("rd_1992_2007").items()}
    kinds: dict[str, set[str]] = {}
    months: dict[str, set[str]] = {}
    files: dict[str, int] = {}
    for row in read(HEADERS / "rd_1992_2007.csv"):
        for field, spec in by_layout[row["layout"]].items():
            kinds.setdefault(field, set()).add(spec[0])
            if spec[0] == "N" and field in {"num_proc", "insc_pn", "seq_aih5"}:
                months.setdefault(field, set()).add(month(row["file"]))
                files[field] = files.get(field, 0) + 1
    assert {field for field, seen in kinds.items() if len(seen) > 1} == set(months)
    assert {f: (min(m), max(m), len(m), files[f]) for f, m in months.items()} == {
        "num_proc": ("1996-01", "1996-07", 7, 188),
        "insc_pn": ("2004-07", "2006-03", 21, 567),
        "seq_aih5": ("2004-07", "2006-03", 21, 567),
    }
    for row in read(HEADERS / "rd_1992_2007.csv"):
        if month(row["file"]) in months["num_proc"]:
            assert by_layout[row["layout"]]["num_proc"] == "N4.0"
        if month(row["file"]) in months["insc_pn"]:
            assert by_layout[row["layout"]]["insc_pn"] == "N10.0"


def test_one_rd_file_from_2008_is_outside_the_six_layouts_of_the_census():
    new = layouts("rd")
    known = {row["fields"] for row in read(CENSUS_FROM_2008)}
    assert len(known) == 6 and known < set(new.values())
    (number,) = [n for n, fields in new.items() if fields not in known]
    rows = read(HEADERS / "rd.csv")
    (odd,) = [row for row in rows if row["layout"] == number]
    assert (odd["file"], odd["server_modified"], odd["size_bytes"], odd["records"]) == (
        ODD,
        "2024-05-22T09:17",
        "197298",
        "4540",
    )
    # The other files of Acre in 2009 are as the server had them in 2013.
    assert {
        row["server_modified"] for row in rows if row["file"].startswith("RDAC09") and row != odd
    } == {"2013-11-01T11:32"}
    (usual,) = {
        new[row["layout"]] for row in rows if month(row["file"]) == "2009-09" and row != odd
    }
    before, after = descriptors(usual), descriptors(new[number])
    assert (len(before), len(after)) == (86, 82)
    assert set(before) - set(after) == {"qt_diarias", "etnia", "sequencia", "remessa"}
    assert set(after) <= set(before)
    assert len([f for f in after if after[f] != before[f]]) == 33
    assert {f for f in after if family(after[f]) != family(before[f])} == (
        VALUES_AS_WHOLE_NUMBERS | TEXT_AS_WHOLE_NUMBERS
    )
    assert {after[f] for f in VALUES_AS_WHOLE_NUMBERS | TEXT_AS_WHOLE_NUMBERS} == {"N1.0"}
    assert {after[f] for f in ("val_tot", "val_uti", "us_tot")} == {"F8.2"}
    # In each of the six layouts the values have decimals and the six other fields are text.
    for fields in known:
        usual_layout = descriptors(fields)
        assert {family(usual_layout[f]) for f in VALUES_AS_WHOLE_NUMBERS} == {"number"}
        assert {family(usual_layout[f]) for f in TEXT_AS_WHOLE_NUMBERS} == {"string"}


def test_rdac0909_has_val_sh_and_val_sp_zeroed_and_the_month_before_has_them_filled():
    """`rdac0909.csv`: the rows in which each field is neither blank nor zero, in the file
    and in RDAC0908. Of the 17 fields that change family, only VAL_SH and VAL_SP are filled
    in the month before."""
    rows = read(HEADERS / "rdac0909.csv")
    listed = {row["file"]: row for row in read(HEADERS / "rd.csv")}
    for row in rows:
        assert (row["size_bytes"], row["records"]) == (
            listed[row["file"]]["size_bytes"],
            listed[row["file"]]["records"],
        )
    filled = {(row["file"], row["field"].lower()): int(row["filled"]) for row in rows}
    changed = VALUES_AS_WHOLE_NUMBERS | TEXT_AS_WHOLE_NUMBERS
    assert {f: filled[ODD, f] for f in changed if filled[ODD, f]} == {}
    assert {f: filled["RDAC0908.dbc", f] for f in changed if filled["RDAC0908.dbc", f]} == {
        "val_sh": 4379,
        "val_sp": 4379,
    }
    assert (filled[ODD, "val_tot"], filled[ODD, "us_tot"]) == (4540, 4540)
    assert (filled["RDAC0908.dbc", "val_tot"], filled["RDAC0908.dbc", "us_tot"]) == (4379, 4379)
    assert {(row["file"], row["sha256"]) for row in rows} == {
        (ODD, "25a4aeccfd1025c88630afb60b782442a0e8471d2803ae42c5da01a2b10c9200"),
        ("RDAC0908.dbc", "13488ebc2ce3e404eed83fd814fc089f7a5be0a8cb427205d82ce44751ef2261"),
    }


@pytest.mark.parametrize("field", ["val_sh", "val_sp"])
def test_the_dictionary_warns_that_rdac0909_publishes_the_field_zeroed(field):
    """The file is imported as published (#219), so the sum of the field for Acre in
    2009-09 is zero in the lake. The issue of the field says so, with the counts of
    `rdac0909.csv`."""
    rows = {(r["file"], r["field"].lower()): r for r in read(HEADERS / "rdac0909.csv")}
    odd, before = rows[ODD, field], rows["RDAC0908.dbc", field]
    assert (odd["records"], odd["filled"]) == ("4540", "0")
    assert (before["records"], before["filled"]) == ("4379", "4379")
    assert rows[ODD, "val_tot"]["filled"] == "4540"
    issues = load_dicionario(DATASET).field_def(field)["x-metadata"].get("issues", [])
    assert [issue["id"] for issue in issues] == ["zerado-em-rdac0909"]
    (found,) = issues
    text = " ".join(found["description"].split())
    assert found["status"] == "open"
    assert f"{field.upper()} igual a zero nos 4.540 registros" in text
    assert "preenchido nos 4.379" in text and "VAL_TOT está preenchido nos 4.540" in text
    assert odd["sha256"] in text
    assert "evidence/2026-11-19-sih-cabecalhos/rdac0909.csv" in text and "issue #219" in text
    in_layout = {number: descriptors(fields)[field] for number, fields in layouts("rd").items()}
    assert in_layout.pop("2") == "N1.0" and set(in_layout.values()) == {"N13.2"}
    others = [row for row in read(HEADERS / "rd.csv") if row["layout"] != "2"]
    assert len(others) == 6071 and "nos outros 6.071 arquivos RD" in text
    assert "é N(1), sem casas decimais" in text and "é N(13,2)" in text


def test_rdac0909_declares_17_fields_as_whole_numbers_and_is_staged_as_the_dictionary_declares(
    dbc_fixture, monkeypatch
):
    """In this file's header 17 fields are whole numbers that the dictionary declares
    `number`, `string` or `date`. Staging gives them the declared type (#219; the rule
    is tested in tests/unit/sources/datasus_ftp/test_staged_types.py). The fixture is
    records 5 to 9 as published: none has a pre-natal number or a manager's CPF."""
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", "auto")
    raw = dbc_fixture("sih_rd_ac_2009_09_excerpt").read_bytes()
    dictionary = load_dicionario(DATASET)
    header = physical_arrow_types(dbc.decompress_bytes(raw))
    assert {
        name
        for name, kind in header.items()
        if pa.types.is_integer(kind) and dictionary.field_def(name)["type"] != "integer"
    } == VALUES_AS_WHOLE_NUMBERS | TEXT_AS_WHOLE_NUMBERS
    frame = dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect()
    assert frame.shape == (5, 82)
    assert {
        name
        for name, dtype in frame.schema.items()
        if dtype.is_integer() and dictionary.field_def(name)["type"] != "integer"
    } == set()
    assert frame.select(pl.col("val_sh", "val_sp").sum()).row(0) == (0, 0)
    assert frame["val_tot"].min() > 0
    assert frame["insc_pn"].unique().to_list() == ["0000000000"]
    assert frame["gestor_cpf"].unique().to_list() == ["000000000000000"]
    assert list(raw[1:4]) == [11, 1, 13]  # the header's date of last update


@pytest.mark.rust_dbf
def test_the_rust_reader_does_not_read_rdac0909(dbc_fixture, monkeypatch):
    """VAL_TOT, VAL_UTI and US_TOT are `F` in this file and in no other of the four
    censuses. The Rust reader has no `F`; `auto` reads the file with the Python one."""
    omnisus_dbf = pytest.importorskip("omnisus_dbf")
    with_f = [
        (name, number)
        for name in ("rd", "rd_1992_2007", "sp", "rj")
        for number, fields in layouts(name).items()
        if any(spec[0] == "F" for spec in descriptors(fields).values())
    ]
    assert with_f == [("rd", "2")]
    raw = dbc_fixture("sih_rd_ac_2009_09_excerpt").read_bytes()
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", "rust")
    with pytest.raises(omnisus_dbf.UnsupportedDbfError):
        dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect()
