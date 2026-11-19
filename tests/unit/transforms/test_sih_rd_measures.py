"""RD: what the dictionary says of a few fields agrees with counts from real files (#182).

`evidence/2026-11-18-rd-medidas` holds counts taken from 238 RD files of 2008-01 to
2026-07 and from 24 of 2006 and 2007: per file, the rows where a field is filled or has
a given value. The files are not in the repository; their SHA-256 are, and most are the
ones the two censuses of layouts recorded.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pytest

from omnisus.transforms.dictionaries import load_dicionario

ROOT = Path(__file__).resolve().parents[3]
MEASURES = ROOT / "evidence/2026-11-18-rd-medidas"
DATASET = "sih_aih_reduzida"
FROM_2008, BEFORE_2008 = "2008-2026", "2006-2007"


def read(period: str, name: str) -> list[dict[str, str]]:
    with (MEASURES / period / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def totals(period: str, measure: str) -> Counter[str]:
    """Key -> rows, summed over the files of the period."""
    out: Counter[str] = Counter()
    for row in read(period, "medidas.csv"):
        if row["medida"] == measure:
            out[row["chave"]] += int(row["linhas"])
    return out


def issue(field: str, ident: str, dataset: str = DATASET) -> str:
    issues = load_dicionario(dataset).field_def(field)["x-metadata"]["issues"]
    (found,) = [i["description"] for i in issues if i["id"] == ident]
    return found


def pt(number: int) -> str:
    """1994690 -> "1.994.690", as the issues write numbers."""
    return f"{number:,}".replace(",", ".")


def test_the_files_measured_are_those_the_censuses_recorded():
    """238 files and 1,994,690 records from 2008, 24 files and 41,547 records of 2006 and
    2007. Every file the censuses of layouts also read has the SHA-256 recorded there,
    except 11 of 2025-09 to 2026-07, which the server published again after 2026-10-06."""
    counted = {
        period: (len(files), sum(int(f["records"]) for f in files))
        for period in (FROM_2008, BEFORE_2008)
        for files in [read(period, "arquivos.csv")]
    }
    assert counted == {FROM_2008: (238, 1994690), BEFORE_2008: (24, 41547)}
    for period, census, shared in (
        (FROM_2008, "evidence/2026-10-06-rd-2008-layouts/census.csv", 224),
        (BEFORE_2008, "evidence/2026-10-01-rd-1992-2007-layouts/census.csv", 24),
    ):
        with (ROOT / census).open(encoding="utf-8", newline="") as f:
            recorded = {row["file"]: row["sha256"] for row in csv.DictReader(f)}
        files = {f["file"]: f["sha256"] for f in read(period, "arquivos.csv")}
        assert len(files.keys() & recorded.keys()) == shared
        changed = sorted(n for n in files.keys() & recorded.keys() if files[n] != recorded[n])
        if period == BEFORE_2008:
            assert changed == []
        else:
            assert len(changed) == 11
            assert min(name[4:8] for name in changed) == "2509"


def test_the_zerado_fields_are_empty_from_2008_and_were_filled_before():
    """IT_SIHSUS_1603 calls 19 fields "Zerado". None is filled in any record of the 238
    files from 2008. In 2006 and 2007, the months whose layout gives them their labels,
    14 of them are filled, and each field's issue gives its count."""
    assert set(totals(FROM_2008, "zerado_preenchido").values()) == {0}
    before = totals(BEFORE_2008, "zerado_preenchido")
    assert len(before) == 19
    assert sorted(name for name, rows in before.items() if rows == 0) == [
        "uti_int_al",
        "uti_int_an",
        "uti_int_in",
        "val_ortp",
        "val_transp",
    ]
    assert (before["val_sadt"], before["cpf_aut"]) == (41405, 439)
    for name, rows in before.items():
        text = issue(name, "rotulo-do-layout-ate-2007")
        assert "em nenhum dos 1.994.690 registros dos 238 arquivos RD lidos de 2008-01" in text
        filled = f"em {pt(rows)} dos 41.547" if rows else "em nenhum dos 41.547"
        assert f"{filled} registros dos 24 arquivos RDRR de 2006 e 2007" in text, name


def test_homonimo_publishes_0_and_2_since_2006():
    """The files publish `0` and `2` in 2006-2007 and from 2008; `1` appears in one file,
    RDAP2607. The 21 files of 2006-04 to 2007-12 have the layout Layout_REDUZIDA.pdf
    describes with "0 = não , 1 = sim", and publish `2` and no `1`: the lists of the
    documents the issue cites do not describe the data, which is why they are no map."""
    assert totals(FROM_2008, "homonimo") == {"0": 1922238, "1": 34, "2": 72418}
    assert totals(BEFORE_2008, "homonimo") == {"0": 40242, "2": 1305}
    ones = [
        r["file"]
        for r in read(FROM_2008, "medidas.csv")
        if (r["medida"], r["chave"]) == ("homonimo", "1")
    ]
    assert ones == ["RDAP2607.dbc"]
    with_2 = {
        r["file"]
        for r in read(BEFORE_2008, "medidas.csv")
        if (r["medida"], r["chave"]) == ("homonimo", "2")
    }
    assert len(with_2) == 24
    text = issue("homonimo", "homonimo-sem-fonte")
    assert "'0' em 1.922.238 registros, '2' em 72.418 e '1' em 34, todos de RDAP2607" in text
    assert "'0' em 40.242 e '2' em 1.305, sem '1'" in text


def test_tpdisec_0_always_goes_with_a_blank_diagnosis():
    """In the 148 files from 2015-01, each TPDISEC is `0` exactly where the DIAGSEC of the
    same number is blank, and `1` or `2` exactly where it is filled. The 12 files of 2014
    publish both blank. No file mixes the two regimes."""
    by_file: dict[str, Counter[str]] = {}
    for row in read(FROM_2008, "medidas.csv"):
        if row["medida"].startswith("tpdisec"):
            by_file.setdefault(row["file"], Counter())[row["chave"]] += int(row["linhas"])
    blank = {name for name, keys in by_file.items() if set(keys) == {"|diagsec vazio"}}
    coded = set(by_file) - blank
    assert (len(by_file), len(blank), len(coded)) == (160, 12, 148)
    assert {name[4:6] for name in blank} == {"14"}
    assert min(name[4:8] for name in coded if name.startswith("RDRR")) == "1501"
    summed = sum((by_file[name] for name in coded), Counter())
    assert summed == {
        "0|diagsec vazio": 11710387,
        "1|diagsec preenchido": 372666,
        "2|diagsec preenchido": 118796,
    }
    for n in range(1, 10):
        text = issue(f"tpdisec{n}", "tpdisec-0-sem-fonte")
        assert "os 12 arquivos de 2014 publicam o campo em branco" in text
        assert "os 148 de 2015-01 em diante publicam '0' só com o diagsec" in text


def test_cid_notif_is_z302_in_almost_every_filled_record():
    """28,388 of the 1,994,690 records from 2008 fill CID_NOTIF: Z302 in 28,207, a code
    that begins with O in 172, and five other values in 9. Z302 goes with both sexes."""
    values = totals(FROM_2008, "cid_notif")
    filled = {value: rows for value, rows in values.items() if value.strip(" 0")}
    assert sum(filled.values()) == 28388
    assert filled["Z302"] == 28207
    assert sum(rows for value, rows in filled.items() if value.startswith("O")) == 172
    assert {v: r for v, r in filled.items() if not v.startswith("O") and v != "Z302"} == {
        "302": 2,
        "Z310": 2,
        "Z3Z0": 2,
        "ZZ30": 2,
        "Z320": 1,
    }
    by_sex = totals(FROM_2008, "cid_notif|sexo")
    assert (by_sex["Z302|1"], by_sex["Z302|3"]) == (6050, 22157)
    text = issue("cid_notif", "cid_notif-laqueadura-no-def")
    assert "Z302 em 28.207 dos 28.388 registros preenchidos" in text
    assert "6.050 com sexo 1 e 22.157 com sexo 3" in text


@pytest.mark.parametrize("dataset", ["sih_aih_reduzida", "sih_aih_rejeitada"])
def test_the_federal_district_publishes_a_uf_zi_the_table_reaches_only_by_a_range(dataset):
    """Every record of the five RDDF files measured has UF_ZI 530000. br_municgestor.cnv
    lists 530010 and reaches 530000 only through the range 530000-530009 of the line
    "530000 Distrito Federal": without the ranges, the whole Federal District would have
    no label. No file has a code of the other three ranges."""
    in_range = totals(FROM_2008, "uf_zi_em_faixa")
    df_records = sum(
        int(f["records"]) for f in read(FROM_2008, "arquivos.csv") if f["file"].startswith("RDDF")
    )
    assert in_range == {"530000": 76276} and df_records == 76276
    table = ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/CNV/br_municgestor.cnv"
    (line,) = (
        row
        for row in table.read_text(encoding="latin-1").splitlines()
        if "530000 Distrito Federal" in row
    )
    assert line[60:].strip() == "530010,530000-530009,530011-539999"
    field = load_dicionario(dataset).field_def("uf_zi")
    assert field["x-decode"]["530000"] == "530000 Distrito Federal"
    text = issue("uf_zi", "uf_zi-faixa-em-codigo-longo", dataset)
    assert "Nenhum arquivo lido publica uma dessas chaves" not in text
    assert "530000 em todos os 76.276 registros dos cinco arquivos RDDF" in text
