"""AP_NATJUR of the APAC files against APAC_Dados_Comuns.DEF and NATJURC.CNV (#183).

``APAC_Dados_Comuns.DEF`` (``TAB_SIA.zip``, files ``A?*.DBC``) binds ``AP_NATJUR`` to
``CNV/NATJURC.CNV``. The DEF of each APAC dataset either writes the field ``AP_NAT_JUR``
or has no line for it, so ``vinculos.json`` names the common DEF for this one field in
``def_do_campo``. ``evidence/2026-11-19-apac-ap-natjur/`` holds what was read on
2026-11-19 from 9,527 files of the nine other APAC datasets: none has a field named
``AP_NAT_JUR``, and every filled ``AP_NATJUR`` is a code of the table. The census files
are not committed; nine of them are fixtures, and their SHA-256 ties the tables to
``tests/fixtures/FIXTURES.md``. Only the parametrised test reads published bytes; the
others check the committed tables and what the dictionaries say of them.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import re
from importlib.resources import files
from pathlib import Path

import pytest

from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.cnv import cnv_map, parse_cnv, parse_def
from omnisus.transforms.dictionaries import _lookup_decode, load_dicionario
from tests.unit.test_fixture_provenance import load_fixture_rows

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "evidence/2026-11-19-apac-ap-natjur"
CNV = files("omnisus").joinpath("data/dicionarios/sources/cnv")
# Dataset -> the fixture that publishes the field, the file prefix, and the lines on which
# the dataset's own DEF writes AP_NAT_JUR (None: the DEF has no line for the field).
BOUND = {
    "sia_apac_quimioterapia": ("sia_aq_rr_2024_01_mini", "AQ", (250, 255)),
    "sia_apac_radioterapia": ("sia_ar_ac_2024_01_mini", "AR", (245, 250)),
    "sia_apac_medicamentos": ("sia_am_rr_2024_01_mini", "AM", (212, 217)),
    "sia_apac_laudos_diversos": ("sia_ad_rr_2024_01_mini", "AD", (204, 209)),
    "sia_apac_cirurgia_bariatrica": ("sia_abo_sp_2024_01_mini", "ABO", (235, 240)),
    "sia_apac_acompanhamento_bariatrica": ("sia_ab_se_2025_07_mini", "AB", (221, 226)),
    "sia_apac_nefrologia": ("sia_an_pa_2014_10_mini", "AN", (221, 226)),
    "sia_apac_fistula_arteriovenosa": ("sia_acf_rr_2024_01_mini", "ACF", None),
    "sia_apac_tratamento_dialitico": ("sia_atd_rr_2024_01_mini", "ATD", None),
}
COMMON = "sia/APAC_Dados_Comuns.DEF"


def _rows(name: str) -> list[dict[str, str]]:
    with (CENSUS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _vinculos() -> dict:
    return json.loads(CNV.joinpath("vinculos.json").read_text("utf-8"))


def _table() -> dict[str, str]:
    return cnv_map(parse_cnv(CNV.joinpath("sia/CNV/natjurc.cnv").read_bytes().decode("latin-1")))


def test_the_census_rows_of_nine_fixtures_are_the_files_fixtures_md_records() -> None:
    census = {r["file"]: r for r in _rows("files.csv")}
    assert len(census) == 9527
    checked = 0
    for row in load_fixture_rows():
        name = row["source"].rsplit("/", 1)[-1]
        if name in census and "/SIASUS/200801_/Dados/" in row["source"]:
            assert census[name]["sha256"] == row["source_sha256"], name
            assert census[name]["listed"] == row["server_modified"], name
            checked += 1
    assert checked == 9


def test_no_census_file_names_the_field_as_the_seven_defs_do() -> None:
    """The field is AP_NATJUR, the last of the header, or absent; never AP_NAT_JUR. The AN
    files are in ``test_sia_an_census``: two headers, those of the two AN fixtures."""
    rows = _rows("files.csv")
    assert {r["natjur_names"] for r in rows} == {"", "AP_NATJUR"}
    assert all(r["position"] == r["fields"] for r in rows if r["natjur_names"])


def test_every_filled_value_of_the_census_is_a_code_of_natjurc() -> None:
    table = _table()
    assert len(table) == 98 and "    -zzzz" in table
    values = _rows("values.csv")
    filled = [r for r in values if r["value"]]
    assert sum(int(r["records"]) for r in filled) == 2276452
    assert len({r["value"] for r in filled}) == 28
    assert {r["value"] for r in filled} <= set(table)


def test_the_common_def_binds_the_published_name_to_four_tables() -> None:
    """Lines 203-208: NATJUR.CNV (L) and NATJURC.CNV (C and S) under AP_NATJUR, and the two
    ESFERAJUR tables under AP_NAT_JUR. The reader refuses the NATJUR.CNV of the zip ("CNV
    line outside the column layout"; #7 discusses that layout for the SIH), so the map is
    NATJURC.CNV's: a choice of the table the reader reads, which #7 leaves open for the SIH."""
    lines = CNV.joinpath(COMMON).read_bytes().decode("latin-1").splitlines()
    assert lines[2] == "ADADOS\\A?*.DBC"
    bound = [parse_def(lines[n - 1])[0] for n in range(203, 209)]
    assert [(b.kind, b.field, b.start, b.table) for b in bound] == [
        ("L", "AP_NATJUR", 1, "CNV/NATJUR.CNV"),
        ("C", "AP_NATJUR", 1, "CNV/NATJURC.CNV"),
        ("S", "AP_NATJUR", 1, "CNV/NATJURC.CNV"),
        ("L", "AP_NAT_JUR", 1, "CNV/ESFERAJUR.CNV"),
        ("C", "AP_NAT_JUR", 1, "CNV/ESFERAJURC.CNV"),
        ("S", "AP_NAT_JUR", 1, "CNV/ESFERAJURC.CNV"),
    ]


@pytest.mark.parametrize("dataset", list(BOUND))
def test_the_dictionary_takes_the_table_the_common_def_binds(dataset, dbc_fixture) -> None:
    spec = _vinculos()["datasets"][dataset]
    fixture, prefix, own_lines = BOUND[dataset]
    (def_path,) = spec["def"]
    own = CNV.joinpath(def_path).read_bytes().decode("latin-1")
    # The override is needed: the dataset's own DEF never names the published field.
    assert "AP_NATJUR" not in own
    assert ("AP_NAT_JUR" in own) == (own_lines is not None)
    assert spec["def_do_campo"] == {"ap_natjur": COMMON}
    assert spec["campos"]["ap_natjur"] == "sia/CNV/natjurc.cnv"
    dictionary = load_dicionario(dataset)
    assert dictionary.field_def("ap_nat_jur") is None
    field = dictionary.field_def("ap_natjur")
    assert {str(k): v for k, v in field["x-decode"].items()} == _table()
    (claim,) = [c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes"]
    assert claim["method"] == "cnv-parse"
    assert "APAC_Dados_Comuns.DEF e não pelo DEF do dataset" in claim["note"]
    assert claim["evidence"] == [
        {
            "source_id": "sia-tab-1ce232b217c6",
            "pages": [],
            "locator": "APAC_Dados_Comuns.DEF: CNatureza Jurídica, AP_NATJUR, 1, "
            "CNV/NATJURC.CNV; CNV/natjurc.cnv",
        }
    ]
    frame = dbc_bytes_to_lazyframe(dbc_fixture(fixture).read_bytes(), dataset=dataset)
    published = set(frame.select("ap_natjur").collect()["ap_natjur"])
    assert published and all(_lookup_decode(field["x-decode"], v) for v in published)
    assert _lookup_decode(field["x-decode"], "") is None
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == "ap_natjur-nem-sempre-publicado"
    ]
    assert issue["status"] == "open" and "APAC_Dados_Comuns.DEF" in issue["description"]
    assert "A máscara sozinha não diz que um arquivo segue esse DEF" in issue["description"]
    if own_lines:
        first, last = own_lines
        assert all("AP_NAT_JUR" in line for line in own.splitlines()[first - 1 : last])
        assert f"(linhas {first}-{last})" in issue["description"]
        assert "AP_NAT_JUR" in issue["description"]
    if prefix == "AN":
        return
    name = re.compile(prefix + r"[A-Z]{2}\d{4}\.dbc", re.IGNORECASE)
    rows = [r for r in _rows("files.csv") if name.fullmatch(r["file"])]
    have = sum(1 for r in rows if r["natjur_names"])
    values = [r for r in _rows("values.csv") if r["prefix"] == prefix]
    filled = sum(int(r["records"]) for r in values if r["value"])
    blank = sum(int(r["records"]) for r in values if not r["value"])
    assert f"{len(rows)} arquivos {prefix} " in issue["description"]
    assert (
        f" {have} têm AP_NATJUR, sempre o último campo, e {len(rows) - have} não têm"
        in (issue["description"])
    )
    assert {r["width"] for r in rows if r["natjur_names"]} == {"4"}
    distinct = len([r for r in values if r["value"]])
    assert f"com {distinct} códigos distintos, todos no natjurc.cnv" in issue["description"]
    assert f"preenchido em {filled} registros" in issue["description"]
    assert f"em branco em {blank}." in issue["description"]


def _gerar():
    spec = importlib.util.spec_from_file_location(
        "gerar_decode_cnv", ROOT / "scripts/metadados/gerar_decode_cnv.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_def_do_campo_is_only_for_a_field_no_def_of_the_dataset_binds() -> None:
    """With the real AN entry: AP_NATJUR, which APAC_Nefrologia.DEF never names, takes the
    common DEF; AP_SEXO, which it binds, is refused; a field with no entry keeps the
    dataset's DEF; and the common DEF's line is the evidence."""
    gerar, vinculos = _gerar(), _vinculos()
    spec = vinculos["datasets"]["sia_apac_nefrologia"]
    assert gerar.defs_for(spec, "ap_natjur", vinculos) == [COMMON]
    assert gerar.defs_for(spec, "ap_sexo", vinculos) == spec["def"]
    wrong = {**spec, "def_do_campo": {"ap_sexo": COMMON}}
    with pytest.raises(ValueError, match=r"which sia/APAC_Nefrologia\.DEF binds"):
        gerar.defs_for(wrong, "ap_sexo", vinculos)
    with pytest.raises(ValueError, match="does not bind ap_natjur"):
        gerar.evidence_for(spec["def"], "ap_natjur", "sia/CNV/natjurc.cnv", vinculos)
    (entry,) = gerar.evidence_for([COMMON], "ap_natjur", "sia/CNV/natjurc.cnv", vinculos)
    assert "AP_NATJUR" in entry["locator"]
