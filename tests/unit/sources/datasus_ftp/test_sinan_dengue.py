"""sinan_dengue on real DENGBR files (tests/fixtures/FIXTURES.md)."""

from __future__ import annotations

import pyarrow.parquet as pq
import pytest

import omnisus as sus
from omnisus.sources._base import ScopeKey
from omnisus.sources.datasus_ftp.identity import validate_identity
from omnisus.sources.datasus_ftp.staging import dbc_bytes_to_parquet
from omnisus.transforms.dictionaries import load_dicionario

FIXTURE = "sinan_dengue_br_2017_excerpt"


def _fields() -> dict[str, dict]:
    return {f["field"]["name"]: f["field"] for f in sus.describe_dataset("sinan_dengue")["fields"]}


def _stage(dbc_fixture, tmp_path):
    out = tmp_path / "dengue.parquet"
    raw = dbc_fixture(FIXTURE).read_bytes()
    result = dbc_bytes_to_parquet(
        raw, out, dataset="sinan_dengue", source_ano=2017, release="final"
    )
    return out, result


def test_excerpt_stages_every_field_of_the_dictionary(dbc_fixture, tmp_path):
    """DENGBR17: 121 fields, the layout of DENGBR14 to DENGBR26."""
    out, result = _stage(dbc_fixture, tmp_path)
    assert result.rows == 5000
    staged = pq.read_schema(out).names
    assert staged == [*_fields(), "_source_ano", "_source_release"]
    assert len(_fields()) == 121


def test_identity_is_the_file_year_and_the_agravo_a90(dbc_fixture, tmp_path):
    out, _ = _stage(dbc_fixture, tmp_path)
    dicionario = load_dicionario("sinan_dengue")
    validate_identity(out, dicionario, ScopeKey(uf=None, ano=2017))
    with pytest.raises(ValueError, match="most frequent nu_ano is 2017"):
        validate_identity(out, dicionario, ScopeKey(uf=None, ano=2016))
    assert dicionario.raw["x-identity"]["code"] == "A90"


def test_classification_takes_8_from_the_cnv_and_the_rest_from_the_page():
    """The dictionary page lists 5, 10, 11, 12 and 13; DENGBR17 holds 8 in 73,852
    records, which only Classdeng.cnv names (Inconclusivo)."""
    field = _fields()["classi_fin"]
    assert {c["value"]: c["label"] for c in field["codes"]} == {
        "5": "Descartado",
        "8": "Inconclusivo",
        "10": "Dengue",
        "11": "Dengue com sinais de alarme",
        "12": "Dengue grave",
        "13": "Chikungunya",
    }


def test_labels_of_the_excerpt(dbc_fixture, tmp_path):
    """Counted on the raw bytes of the excerpt on 2026-11-20."""
    import polars as pl

    out, _ = _stage(dbc_fixture, tmp_path)
    labelled = sus.label(
        "sinan_dengue", pl.read_parquet(out), columns=["classi_fin", "evolucao", "tp_sistema"]
    )

    def counts(column: str) -> dict:
        rows = labelled.group_by(column, f"{column}_rotulo").len().rows()
        return {(code, label): n for code, label, n in rows}

    assert counts("classi_fin") == {
        ("10", "Dengue"): 4520,
        ("8", "Inconclusivo"): 453,
        ("11", "Dengue com sinais de alarme"): 14,
        ("12", "Dengue grave"): 5,
        ("", None): 8,
    }
    assert counts("evolucao") == {
        ("1", "cura"): 4405,
        ("2", "óbito pelo agravo"): 7,
        ("3", "óbito por outras causas"): 2,
        ("4", "óbito em investigação"): 1,
        ("9", "ignorado"): 25,
        ("", None): 560,
    }
    # TipoSistema.cnv labels the blank as Sinan NET.
    assert counts("tp_sistema") == {("2", "Sinan ONLINE"): 4974, ("", "Sinan NET"): 26}


def test_every_coded_field_cites_the_dengue_dictionary_or_tab_sinannet():
    """Each agravo map cites the Dengue/Chikungunya dictionary, the TAB_SINANNET edition
    read on 2026-11-20, or both; common fields cite the Notificação Individual."""
    known = {
        "sinan-b3e0561c7a2d",
        "sinan-da262c3b9f20",
        "sinan-tab-24ac0c62fb84",
        "sinan-tab-cad66ee38781",
    }
    coded = 0
    for field in sus.describe_dataset("sinan_dengue")["fields"]:
        if not field["field"]["codes"]:
            continue
        coded += 1
        (claim,) = [c for c in field["claims"] if c["target"] == "/field/codes"]
        assert claim["status"] == "verified_in_source"
        assert {e["source_id"] for e in claim["evidence"]} <= known, field["field"]["name"]
    assert coded == 82


def _codes_claim(dataset: str, name: str) -> dict:
    (field,) = [f for f in sus.describe_dataset(dataset)["fields"] if f["field"]["name"] == name]
    (claim,) = [c for c in field["claims"] if c["target"] == "/field/codes"]
    return claim


def test_agravo_maps_carry_the_date_they_were_read():
    """`revisado_em_agravo` dates the dengue maps (2026-11-20); the common fields and the
    other agravos keep the block's `revisado_em`."""
    assert _codes_claim("sinan_dengue", "classi_fin")["checked_at"] == "2026-11-20"
    assert _codes_claim("sinan_dengue", "cs_sexo")["checked_at"] == "2026-09-22"
    assert _codes_claim("sinan_tuberculose", "tratamento")["checked_at"] == "2026-09-22"


def test_complica_has_no_map_because_two_cnv_disagree():
    field = _fields()["complica"]
    assert field["codes"] == []
    assert "CompdengM50mil.cnv" in field["description"]


def _schema(dbc_fixture, tmp_path, year: int):
    out = tmp_path / f"dengue-{year}.parquet"
    raw = dbc_fixture(f"sinan_dengue_br_{year}_excerpt").read_bytes()
    result = dbc_bytes_to_parquet(
        raw, out, dataset="sinan_dengue", source_ano=year, release="final"
    )
    return out, result, pq.read_schema(out)


@pytest.mark.parametrize(("year", "fields"), [(2006, 107), (2012, 67), (2013, 67)])
def test_the_three_older_layouts_stage_as_published_and_pass_identity(
    dbc_fixture, tmp_path, year, fields
):
    """DENGBR06, DENGBR12 and DENGBR13: the columns are the file's own, and the file year is
    the most frequent NU_ANO. DENGBR06 has no ID_AGRAVO, so only the year is checked."""
    out, result, schema = _schema(dbc_fixture, tmp_path, year)
    assert result.rows == 200
    assert len(schema.names) == fields + 2  # plus _source_ano and _source_release
    assert ("id_agravo" in schema.names) == (year != 2006)
    validate_identity(out, load_dicionario("sinan_dengue"), ScopeKey(uf=None, ano=year))


def test_the_types_that_keep_2007_to_2013_out_of_the_table_of_2014_onwards(dbc_fixture, tmp_path):
    """NU_IDADE_N is F 4 in DENGBR07-12 and N 4 afterwards; PLAQ_MENOR is N 18 with
    decimals in DENGBR13 and C 7 in the other layouts. The lake widens neither pair, so
    those years are refused in a table that holds 2014 onwards (docs/sources/sinan_dengue.md,
    Armadilhas)."""
    from omnisus.lake.schema import UnsafeSchemaError, compatible_type

    types = {
        year: {
            column: str(schema.field(column).type)
            for column in ("nu_idade_n", "plaq_menor")
            if column in schema.names
        }
        for year in (2006, 2012, 2013, 2017)
        for schema in [_schema(dbc_fixture, tmp_path, year)[2]]
    }
    assert types == {
        2006: {"plaq_menor": "string"},
        2012: {"nu_idade_n": "double", "plaq_menor": "string"},
        2013: {"nu_idade_n": "int64", "plaq_menor": "double"},
        2017: {"nu_idade_n": "int64", "plaq_menor": "string"},
    }
    for existing, incoming in [("BIGINT", "DOUBLE"), ("VARCHAR", "DOUBLE")]:
        with pytest.raises(UnsafeSchemaError):
            compatible_type(existing, incoming)
