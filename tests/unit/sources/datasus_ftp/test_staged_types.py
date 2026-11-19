"""Staging gives a whole-number DBF field the type the dictionary declares (#40, #219).

A field the DBF header declares `N` with no decimals is read as a whole number. When the
dictionary declares it `string` or `date`, staging writes text, with no zeros added; when
it declares `number`, staging writes a number with decimals. No other difference is
converted. The files below are the ones that publish such fields:

- `RDAC0909.dbc` (`sih_rd_ac_2009_09_excerpt`): eleven value fields and six text fields
  are `N1.0`, and nowhere else from 2008 on;
- `RDRR0407.dbc` (`sih_rd_rr_2004_07_excerpt`): `INSC_PN` and `SEQ_AIH5` are `N`, and
  text in `RDRR0712.dbc` (`sih_rd_rr_2007_12_mini`).
"""

from __future__ import annotations

import polars as pl
import pyarrow as pa
import pytest

from omnisus.lake import Lake
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp import dbc
from omnisus.sources.datasus_ftp._runner import ingest_raw
from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.dbf_batches import physical_arrow_types
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario
from tests.support.listings import fixture_entry

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
AS_NUMBER = ("sih_rd_rr_2004_07_excerpt", "RDRR0407.dbc", ScopeKey("RR", 2004, 7))
AS_TEXT = ("sih_rd_rr_2007_12_mini", "RDRR0712.dbc", ScopeKey("RR", 2007, 12))


def whole_numbers_in_header(raw: bytes) -> set[str]:
    types = physical_arrow_types(dbc.decompress_bytes(raw))
    return {name for name, kind in types.items() if pa.types.is_integer(kind)}


def import_in_order(dataset_name, dbc_fixture, lake, *files) -> None:
    dataset = REGISTRY[dataset_name]
    for fixture, name, scope in files:
        raw = dbc_fixture(fixture).read_bytes()
        ingest_raw(dataset, scope, [(fixture_entry(dataset.ftp_dir, name, raw), raw)], lake)


def test_rdac0909_is_staged_with_the_types_of_every_other_rd_file(dbc_fixture, monkeypatch):
    """The 17 fields are `N1.0` in this file's header alone. The eleven the dictionary
    declares `number` are staged as numbers with decimals, and the six it declares
    `string` or `date` as text. The six are blank in the five records of the fixture, and
    a blank number is no value; `rdac0909.csv` has them blank or zero in the 4,540."""
    monkeypatch.setenv("OMNISUS_DBF_BACKEND", "auto")
    raw = dbc_fixture(APART[0]).read_bytes()
    dictionary = load_dicionario(RD)
    declared = {name: dictionary.field_def(name)["type"] for name in VALUES | TEXT}
    assert {declared[name] for name in VALUES} == {"number"}
    assert {declared[name] for name in TEXT} == {"string", "date"}
    assert whole_numbers_in_header(raw) >= VALUES | TEXT

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
        import_in_order(RD, dbc_fixture, lake, *order)
        assert [p["scope"] for p in lake.publications()] == [scope for _, _, scope in order]
        columns = ", ".join(sorted(VALUES | TEXT))
        table = lake.connect().sql(f"SELECT uf, {columns} FROM lake.{RD}").pl()
    assert {table.schema[name] for name in VALUES} == {pl.Float64}
    assert {table.schema[name] for name in TEXT} == {pl.String}
    acre = table.filter(pl.col("uf") == "AC")
    assert acre.height == 5
    assert all(acre[name].to_list() == [0.0] * 5 for name in VALUES)
    assert all(acre[name].to_list() == [None] * 5 for name in TEXT)


@pytest.mark.parametrize(
    "order", [(AS_TEXT, AS_NUMBER), (AS_NUMBER, AS_TEXT)], ids=["N second", "N first"]
)
def test_a_month_with_insc_pn_as_a_number_and_one_with_it_as_text_share_a_lake(
    dbc_fixture, tmp_path, order
):
    """The decision of #40: the number is written as text with no zeros added, so the
    month that publishes `N` has `0` where the month that publishes `C` has the zeros of
    the field's width. Staged as published, the second import failed with
    `VARCHAR versus BIGINT`."""
    assert whole_numbers_in_header(dbc_fixture(AS_NUMBER[0]).read_bytes()) >= {
        "insc_pn",
        "seq_aih5",
    }
    assert (
        whole_numbers_in_header(dbc_fixture(AS_TEXT[0]).read_bytes())
        & {
            "insc_pn",
            "seq_aih5",
        }
        == set()
    )
    with Lake.local(f"ducklake:{tmp_path}/x.ducklake") as lake:
        import_in_order(RD_BEFORE_2008, dbc_fixture, lake, *order)
        assert len(lake.publications()) == 2
        table = (
            lake.connect()
            .sql(f"SELECT DISTINCT ano, insc_pn, seq_aih5 FROM lake.{RD_BEFORE_2008} ORDER BY ano")
            .pl()
        )
    assert (table.schema["insc_pn"], table.schema["seq_aih5"]) == (pl.String, pl.String)
    assert table.rows() == [(2004, "0", "0"), (2007, "0000000000", "000")]


def test_a_field_declared_a_whole_number_and_published_as_text_stays_text(dbc_fixture):
    """Only a whole number of the file is converted. `peso` of the SIM is declared
    `integer` and published `C`: it is staged as the text the file has."""
    raw = dbc_fixture("sim_rr_2023_mini").read_bytes()
    assert load_dicionario("sim_obitos").field_def("peso")["type"] == "integer"
    assert "peso" not in whole_numbers_in_header(raw)
    frame = dbc_bytes_to_lazyframe(raw, dataset="sim_obitos").collect()
    assert frame.schema["peso"] == pl.String
