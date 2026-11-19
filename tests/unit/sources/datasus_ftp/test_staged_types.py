"""Staging gives a whole-number DBF field the type the dictionary declares (#40, #219).

A field the DBF header declares `N` with no decimals is read as a whole number. When the
dictionary declares it `string` or `date`, staging writes the number as text, with no
zeros to its left; when it declares `number`, staging writes a number with decimals. No
other difference is converted. Three fixtures have such fields, and no other does:

- `RDAC0909.dbc` (`sih_rd_ac_2009_09_excerpt`): eleven value fields and six text fields
  are `N1.0`, in no other RD file from 2008 on;
- `RDRR0407.dbc` (`sih_rd_rr_2004_07_excerpt`): `INSC_PN` and `SEQ_AIH5` are `N`, and
  text in `RDRR0712.dbc` (`sih_rd_rr_2007_12_mini`);
- `RDRR9603.dbc` (`sih_rd_rr_1996_03_excerpt`): `NUM_PROC` is `N4.0`, and `C4` in
  `RDRR9709.dbc` (`sih_rd_rr_1997_09_mini`).
"""

from __future__ import annotations

import csv
from dataclasses import replace
from importlib.resources import files
from pathlib import Path, PurePosixPath

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml

import omnisus as sus
from omnisus.lake import Lake
from omnisus.lake.schema import UnsafeSchemaError
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp import dbc
from omnisus.sources.datasus_ftp._runner import ingest_raw
from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.dbf_batches import physical_arrow_types
from omnisus.sources.datasus_ftp.filenames import parse_name
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from omnisus.transforms.dictionaries import load_dicionario
from tests.support.listings import fixture_entry
from tests.unit.test_fixture_provenance import FIXTURES, load_fixture_rows

HEADERS = Path(__file__).resolve().parents[4] / "evidence/2026-11-19-sih-cabecalhos"
SERVER = "ftp://ftp.datasus.gov.br"
VALUES = {
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
TEXT = {"num_proc", "cpf_aut", "gestor_cod", "gestor_dt", "infehosp", "faec_tp"}

RD = "sih_aih_reduzida"
RD_BEFORE_2008 = "sih_aih_reduzida_1992_2007"
USUAL = ("sih_rd_rr_2025_01_excerpt", "RDRR2501.dbc", ScopeKey("RR", 2025, 1))
APART = ("sih_rd_ac_2009_09_excerpt", "RDAC0909.dbc", ScopeKey("AC", 2009, 9))
RDRR0407 = ("sih_rd_rr_2004_07_excerpt", "RDRR0407.dbc", ScopeKey("RR", 2004, 7))
RDRR0712 = ("sih_rd_rr_2007_12_mini", "RDRR0712.dbc", ScopeKey("RR", 2007, 12))
RDRR9603 = ("sih_rd_rr_1996_03_excerpt", "RDRR9603.dbc", ScopeKey("RR", 1996, 3))
RDRR9709 = ("sih_rd_rr_1997_09_mini", "RDRR9709.dbc", ScopeKey("RR", 1997, 9))


def whole_numbers_in_header(raw: bytes) -> set[str]:
    types = physical_arrow_types(dbc.decompress_bytes(raw))
    return {name for name, kind in types.items() if pa.types.is_integer(kind)}


def import_in_order(dataset, dbc_fixture, lake, *files_, policy="append") -> None:
    for fixture, name, scope in files_:
        raw = dbc_fixture(fixture).read_bytes()
        entry = fixture_entry(dataset.ftp_dir, name, raw)
        ingest_raw(dataset, scope, [(entry, raw)], lake, policy=policy)


def test_in_the_fixtures_only_three_files_have_a_field_staged_with_another_type(tmp_path):
    """Every real DBC fixture is staged with the dictionary of its dataset, and each field
    is compared with the type of its descriptor. The 20 that differ are whole numbers the
    dictionary declares `number`, `string` or `date`. Everything else keeps the
    descriptor's type: the text the SIM declares `integer`, the `D` dates of the SINAN."""
    differ, staged_files = set(), 0
    for row in load_fixture_rows():
        if not row["file"].startswith("dbc/") or row["kind"] not in ("whole", "excerpt"):
            continue
        source = PurePosixPath(row["source"].removeprefix(SERVER))
        (dataset,) = [
            d
            for d in REGISTRY.values()
            if str(source.parent) in d.directories().values() and parse_name(d, source.name)
        ]
        raw = (FIXTURES / row["file"]).read_bytes()
        target = tmp_path / "staged.parquet"
        dbc_bytes_to_parquet(raw, target, dataset=dataset.name)
        staged = pq.read_schema(target)
        staged_files += 1
        for name, kind in physical_arrow_types(dbc.decompress_bytes(raw)).items():
            if staged.field(name).type != kind:
                differ.add((source.name, name, str(kind), str(staged.field(name).type)))
    assert staged_files == 66
    assert differ == (
        {("RDAC0909.dbc", name, "int64", "double") for name in VALUES}
        | {("RDAC0909.dbc", name, "int64", "string") for name in TEXT}
        | {("RDRR0407.dbc", name, "int64", "string") for name in ("insc_pn", "seq_aih5")}
        | {("RDRR9603.dbc", "num_proc", "int64", "string")}
    )


def test_rdac0909_is_staged_with_the_types_of_every_other_rd_file(dbc_fixture, monkeypatch):
    """The 17 fields are `N1.0` in this file's header alone. The eleven the dictionary
    declares `number` are staged as numbers with decimals, and the six it declares
    `string` or `date` as text. In the 4,540 records of the file (`rdac0909.csv`) the
    eleven hold a zero and the six are blank, and a blank number is no value."""
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", "auto")
    raw = dbc_fixture(APART[0]).read_bytes()
    dictionary = load_dicionario(RD)
    declared = {name: dictionary.field_def(name)["type"] for name in VALUES | TEXT}
    assert {declared[name] for name in VALUES} == {"number"}
    assert {declared[name] for name in TEXT} == {"string", "date"}
    assert whole_numbers_in_header(raw) >= VALUES | TEXT
    with (HEADERS / "rdac0909.csv").open(encoding="utf-8", newline="") as f:
        counted = {
            row["field"].lower(): (row["records"], row["filled"], row["blank"])
            for row in csv.DictReader(f)
            if row["file"] == APART[1]
        }
    assert {counted[name] for name in VALUES} == {("4540", "0", "0")}
    assert {counted[name] for name in TEXT} == {("4540", "0", "4540")}

    apart = dbc_bytes_to_lazyframe(raw, dataset=RD).collect()
    usual = dbc_bytes_to_lazyframe(dbc_fixture(USUAL[0]).read_bytes(), dataset=RD).collect()
    assert set(apart.columns) & set(usual.columns) >= VALUES | TEXT
    assert {
        (name, str(apart.schema[name]), str(usual.schema[name]))
        for name in set(apart.columns) & set(usual.columns)
        if apart.schema[name] != usual.schema[name]
    } == set()
    assert {apart.schema[name] for name in VALUES} == {pl.Float64}
    assert {apart.schema[name] for name in TEXT} == {pl.String}
    assert all(apart[name].to_list() == [0.0] * 5 for name in VALUES)
    assert all(apart[name].to_list() == [None] * 5 for name in TEXT)
    assert apart["val_tot"].min() > 0


@pytest.mark.parametrize("order", [(USUAL, APART), (APART, USUAL)], ids=["second", "first"])
def test_rdac0909_and_another_rd_file_share_a_lake_in_either_order(
    dbc_fixture, tmp_path, monkeypatch, order
):
    """Staged as published, whichever came second was refused (`DOUBLE versus BIGINT`),
    and a lake that began with RDAC0909 refused every other RD file (#219)."""
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", "auto")
    with Lake.local(f"ducklake:{tmp_path}/x.ducklake") as lake:
        import_in_order(REGISTRY[RD], dbc_fixture, lake, *order)
        assert [p["scope"] for p in lake.publications()] == [scope for _, _, scope in order]
        columns = ", ".join(sorted(VALUES | TEXT))
        table = lake.connect().sql(f"SELECT uf, {columns} FROM lake.{RD}").pl()
    assert {table.schema[name] for name in VALUES} == {pl.Float64}
    assert {table.schema[name] for name in TEXT} == {pl.String}
    acre = table.filter(pl.col("uf") == "AC")
    assert acre.height == 5
    assert all(acre[name].to_list() == [0.0] * 5 for name in VALUES)
    assert all(acre[name].to_list() == [None] * 5 for name in TEXT)


@pytest.mark.parametrize("backend", ["python", "auto"])
@pytest.mark.parametrize(
    ("order", "fields", "rows"),
    [
        (
            (RDRR0712, RDRR0407),
            ("insc_pn", "seq_aih5"),
            [(2004, "0", "0"), (2007, "0000000000", "000")],
        ),
        (
            (RDRR0407, RDRR0712),
            ("insc_pn", "seq_aih5"),
            [(2004, "0", "0"), (2007, "0000000000", "000")],
        ),
        ((RDRR9709, RDRR9603), ("num_proc",), [(1996, "368"), (1997, "0489")]),
        ((RDRR9603, RDRR9709), ("num_proc",), [(1996, "368"), (1997, "0489")]),
    ],
    ids=["insc_pn, N second", "insc_pn, N first", "num_proc, N second", "num_proc, N first"],
)
def test_a_month_with_the_field_as_a_number_and_one_with_it_as_text_share_a_lake(
    dbc_fixture, tmp_path, monkeypatch, backend, order, fields, rows
):
    """The decision of #40: the number is written as text with no zeros to its left. The
    91 records of the RDRR0407 fixture have `0` where the 1,496 of RDRR0712 have the zeros
    of the field's width, and the 5 of RDRR9603 have `368` where the 794 of RDRR9709 have
    `0489`. Staged as published, the second import failed (`VARCHAR versus BIGINT`)."""
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", backend)
    as_number = {name for _, name, _ in order} & {RDRR0407[1], RDRR9603[1]}
    for fixture, name, _ in order:
        published = whole_numbers_in_header(dbc_fixture(fixture).read_bytes()) & set(fields)
        assert published == (set(fields) if name in as_number else set())
    with Lake.local(f"ducklake:{tmp_path}/x.ducklake") as lake:
        import_in_order(REGISTRY[RD_BEFORE_2008], dbc_fixture, lake, *order)
        assert len(lake.publications()) == 2
        columns = ", ".join(fields)
        query = f"SELECT DISTINCT ano, {columns} FROM lake.{RD_BEFORE_2008} ORDER BY ano"
        table = lake.connect().sql(query).pl()
    assert {table.schema[name] for name in fields} == {pl.String}
    assert table.rows() == rows


def test_a_lake_that_has_the_column_as_a_number_refuses_the_files_staged_as_text(
    dbc_fixture, tmp_path
):
    """Before #40 an `N` month was staged as a whole number, and a lake that began with one
    has the column as BIGINT. A dictionary that declares the two fields `integer` stages
    RDRR0407 that way. Such a lake refuses the same file staged as text, also under
    `replace`, and the months that publish text: the table has to be made again."""

    def as_before(raw: dict) -> None:
        for field in raw["schema"]["fields"]:
            if field["name"] in ("insc_pn", "seq_aih5"):
                field["type"] = "integer"

    packaged = REGISTRY[RD_BEFORE_2008]
    raw = yaml.load(
        (files("omnisus.data.dicionarios") / f"{RD_BEFORE_2008}.yaml").read_text("utf-8"),
        Loader=yaml.CSafeLoader,
    )
    as_before(raw)
    edited = tmp_path / f"{RD_BEFORE_2008}.yaml"
    edited.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    with Lake.local(f"ducklake:{tmp_path}/x.ducklake") as lake:
        import_in_order(replace(packaged, dictionary=edited), dbc_fixture, lake, RDRR0407)
        described = lake.connect().sql(f"DESCRIBE lake.{RD_BEFORE_2008}").pl()
        types = dict(zip(described["column_name"], described["column_type"], strict=True))
        assert (types["insc_pn"], types["seq_aih5"]) == ("BIGINT", "BIGINT")
        with pytest.raises(UnsafeSchemaError, match="BIGINT versus VARCHAR"):
            import_in_order(packaged, dbc_fixture, lake, RDRR0407, policy="replace")
        with pytest.raises(UnsafeSchemaError, match="BIGINT versus VARCHAR"):
            import_in_order(packaged, dbc_fixture, lake, RDRR0712)
        assert [p["scope"] for p in lake.publications()] == [RDRR0407[2]]


def test_describe_dataset_says_where_the_dictionary_type_decides_the_stored_type():
    storage = sus.describe_dataset(RD)["storage"]
    assert storage["policy"] == "source_physical_types"
    assert storage["dictionary_types"] == "applied_to_whole_numbers"
