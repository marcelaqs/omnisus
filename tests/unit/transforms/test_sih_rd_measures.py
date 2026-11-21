"""RD: what the issues of a few fields say agrees with counts from real files (#182).

`evidence/2026-11-18-rd-medidas` holds counts taken from 238 RD files of 2008-01 to
2026-07 (222 of them of Roraima) and from the 24 Roraima files of 2006 and 2007: per
file, the rows where a field is filled or has a given value. The files are not in the
repository; their SHA-256 are, and most are the ones the two censuses of layouts
recorded. These tests tie the numbers the dictionary quotes to those counts; they cannot
tell whether the counts are right, which is what running `medir.py` again is for.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from omnisus.transforms.dictionaries import load_dicionario

ROOT = Path(__file__).resolve().parents[3]
MEASURES = ROOT / "evidence/2026-11-18-rd-medidas"
CENSUS_FROM_2008 = ROOT / "evidence/2026-10-06-rd-2008-layouts/census.csv"
CENSUS_BEFORE_2008 = ROOT / "evidence/2026-10-01-rd-1992-2007-layouts/census.csv"
DATASET = "sih_aih_reduzida"
FROM_2008, BEFORE_2008 = "2008-2026", "2006-2007"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def measured(period: str, measure: str) -> list[tuple[str, str, int]]:
    """(file, key, rows) of one measure."""
    return [
        (row["file"], row["chave"], int(row["linhas"]))
        for row in read(MEASURES / period / "medidas.csv")
        if row["medida"] == measure
    ]


def totals(period: str, measure: str) -> Counter[str]:
    """Key -> rows, summed over the files of the period."""
    out: Counter[str] = Counter()
    for _, key, rows in measured(period, measure):
        out[key] += rows
    return out


def issue(field: str, ident: str, dataset: str = DATASET) -> str:
    issues = load_dicionario(dataset).field_def(field)["x-metadata"]["issues"]
    (found,) = [i["description"] for i in issues if i["id"] == ident]
    return found


def pt(number: int) -> str:
    """1994690 -> "1.994.690", as the issues write numbers."""
    return f"{number:,}".replace(",", ".")


def test_the_files_measured_are_those_the_censuses_recorded():
    """238 files and 1,994,690 records from 2008, 222 of the files of Roraima; 24 files
    and 41,547 records of 2006 and 2007, all of Roraima. A file the censuses of layouts
    also read has the SHA-256 and the size recorded there, except 11 of 2025-09 to
    2026-07, whose SHA-256 differs from the one read on 2026-10-06."""
    files = {
        period: read(MEASURES / period / "arquivos.csv") for period in (FROM_2008, BEFORE_2008)
    }
    assert {p: (len(f), sum(int(x["records"]) for x in f)) for p, f in files.items()} == {
        FROM_2008: (238, 1994690),
        BEFORE_2008: (24, 41547),
    }
    assert Counter(f["file"][:4] for f in files[FROM_2008]) == {
        "RDRR": 222,
        "RDAP": 1,
        "RDDF": 5,
        "RDRJ": 5,
        "RDSP": 5,
    }
    assert {f["file"][:4] for f in files[BEFORE_2008]} == {"RDRR"}
    for period, census, shared, changed in (
        (FROM_2008, CENSUS_FROM_2008, 224, 11),
        (BEFORE_2008, CENSUS_BEFORE_2008, 24, 0),
    ):
        recorded = {row["file"]: (row["sha256"], row["size_bytes"]) for row in read(census)}
        found = {f["file"]: (f["sha256"], f["size_bytes"]) for f in files[period]}
        both = found.keys() & recorded.keys()
        differ = sorted(name for name in both if found[name] != recorded[name])
        assert (len(both), len(differ)) == (shared, changed)
        assert all(name[4:8] >= "2509" for name in differ)


def test_the_zerado_fields_are_empty_from_2008_and_most_were_filled_in_2006_and_2007():
    """IT_SIHSUS_1603 calls 19 fields "Zerado". None is filled in any record of the 238
    files from 2008. Their labels come from the layout of 2006-04 to 2007-12 (layout 19
    of the census): in the 21 Roraima files of those months, 13 of the 19 are filled, and
    each field's issue gives its count over the 36,983 records. NUM_PROC is not one of
    the 13: it is filled only in the three files of 2006-01 to 2006-03, of the layout
    before, which have no RUBRICA."""
    assert set(totals(FROM_2008, "zerado_preenchido").values()) == {0}
    layout = {row["file"]: row["layout"] for row in read(CENSUS_BEFORE_2008)}
    records = {f["file"]: int(f["records"]) for f in read(MEASURES / BEFORE_2008 / "arquivos.csv")}
    described = {name for name in records if layout[name] == "19"}
    assert (len(described), sum(records[name] for name in described)) == (21, 36983)
    assert min(described) == "RDRR0604.dbc" and max(described) == "RDRR0712.dbc"
    filled: Counter[str] = Counter()
    earlier: Counter[str] = Counter()
    present: dict[str, set[str]] = {}
    for name, field, rows in measured(BEFORE_2008, "zerado_preenchido"):
        (filled if name in described else earlier)[field] += rows
        present.setdefault(field, set()).add(name)
    assert len(present) == 19
    assert all(described <= names for names in present.values())
    assert sorted(field for field, names in present.items() if names == described) == ["rubrica"]
    assert sorted(field for field in present if not filled[field]) == [
        "num_proc",
        "uti_int_al",
        "uti_int_an",
        "uti_int_in",
        "val_ortp",
        "val_transp",
    ]
    assert (filled["val_sadt"], filled["rubrica"], filled["cpf_aut"]) == (36858, 36983, 293)
    assert {f: rows for f, rows in earlier.items() if rows and not filled[f]} == {"num_proc": 4564}
    for field in present:
        text = issue(field, "rotulo-do-layout-ate-2007")
        assert (
            "em nenhum dos 1.994.690 registros dos 238 arquivos RD lidos de 2008-01 a 2026-07 "
            "(222 deles de Roraima); nos 21 arquivos RDRR de 2006-04 a 2007-12"
        ) in text
        rows = f"vem preenchido em {pt(filled[field])}" if filled[field] else "não vem em nenhum"
        assert f"{rows} dos 36.983 registros" in text, field
        assert ("nos 4.564 registros dos três arquivos de 2006-01 a 2006-03" in text) == (
            field == "num_proc"
        )


def test_homonimo_publishes_0_and_2_since_2006():
    """The files read publish `0` and `2` in 2006-2007 and in every year from 2008; `1`
    appears in one file, RDAP2607. The 21 Roraima files of 2006-04 to 2007-12 have the
    layout Layout_REDUZIDA.pdf describes with "0 = não , 1 = sim", and each publishes `2`
    and no `1`."""
    assert totals(FROM_2008, "homonimo") == {"0": 1922238, "1": 34, "2": 72418}
    assert totals(BEFORE_2008, "homonimo") == {"0": 40242, "2": 1305}
    assert [name for name, key, _ in measured(FROM_2008, "homonimo") if key == "1"] == [
        "RDAP2607.dbc"
    ]
    for key in ("0", "2"):
        years = {name[4:6] for name, found, _ in measured(FROM_2008, "homonimo") if found == key}
        assert years == {f"{year:02d}" for year in range(8, 27)}
    with_2 = {name for name, key, _ in measured(BEFORE_2008, "homonimo") if key == "2"}
    assert len(with_2) == 24
    text = issue("homonimo", "homonimo-sem-fonte")
    assert "(222 deles de Roraima; evidence/2026-11-18-rd-medidas)" in text
    assert "'0' em 1.922.238 registros, '2' em 72.418 e '1' em 34, todos de RDAP2607" in text
    assert "'0' em 40.242 e '2' em 1.305, sem '1'" in text


def test_tpdisec_0_always_goes_with_a_blank_diagnosis():
    """In the 148 files read from 2015-01, each TPDISEC is `0` exactly where the DIAGSEC
    of the same number is blank. TPDISEC1 to TPDISEC7 are `1` or `2` exactly where it is
    filled; TPDISEC8 and TPDISEC9 are `0` in every record, and their DIAGSEC is never
    filled. The 12 Roraima files of 2014 publish all nine blank. No file mixes blank and
    coded. Each field's issue says which of the two it is, and that a count is no
    meaning."""
    by_file: dict[str, Counter[str]] = {}
    by_field: dict[int, Counter[str]] = {}
    for n in range(1, 10):
        for name, key, rows in measured(FROM_2008, f"tpdisec{n}"):
            by_file.setdefault(name, Counter())[key] += rows
            by_field.setdefault(n, Counter())[key] += rows
    blank = {name for name, keys in by_file.items() if set(keys) == {"|diagsec vazio"}}
    coded = set(by_file) - blank
    assert (len(by_file), len(blank), len(coded)) == (160, 12, 148)
    assert {name[:6] for name in blank} == {"RDRR14"}
    assert min(name[4:8] for name in coded) == "1501"
    assert sum((by_file[name] for name in coded), Counter()) == {
        "0|diagsec vazio": 11710387,
        "1|diagsec preenchido": 372666,
        "2|diagsec preenchido": 118796,
    }
    only_zero = [n for n, keys in by_field.items() if not {k for k in keys if k[0] in "12"}]
    assert only_zero == [8, 9]
    for n in range(1, 10):
        text = issue(f"tpdisec{n}", "tpdisec-0-sem-fonte")
        assert "os 12 arquivos de Roraima de 2014 publicam o campo em branco" in text
        if n in only_zero:
            assert f"publicam só '0', e o diagsec{n} nunca vem preenchido" in text
        else:
            assert f"publicam '0' só com o diagsec{n} em branco e '1' ou '2' só com ele" in text
        assert "A contagem diz o que os arquivos trazem, não o que o '0' quer dizer." in text


def test_cid_notif_is_z302_in_almost_every_filled_record():
    """28,388 of the 1,994,690 records from 2008 fill CID_NOTIF: Z302 in 28,207, a code
    that begins with O in 172, and five other values in 9. In the 24 files of 2006 and
    2007 the field is `0000` in 41,081 records, blank in 143 and Z302 in 323."""
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
    assert totals(BEFORE_2008, "cid_notif") == {"0000": 41081, "": 143, "Z302": 323}
    text = issue("cid_notif", "cid_notif-laqueadura-no-def")
    assert "(222 deles de Roraima; evidence/2026-11-18-rd-medidas)" in text
    assert (
        "Z302 em 28.207 dos 28.388 registros preenchidos, um código iniciado por O em 172 "
        "e outro valor em 9"
    ) in text


def test_every_faec_tp_code_the_files_publish_has_a_label():
    """The files from 2008 publish 32 distinct FAEC_TP codes in 57,820 records, and blank
    in the others. Every one is a code TP_FINAN.CNV lists one by one, so the dictionary
    labels it: no published code falls to the reserve range the map leaves out."""
    published = totals(FROM_2008, "faec_tp")
    codes = {code: rows for code, rows in published.items() if code.strip()}
    assert (len(codes), sum(codes.values())) == (32, 57820)
    assert sum(published.values()) == 1994690
    labels = load_dicionario(DATASET).field_def("faec_tp")["x-decode"]
    assert set(published) <= set(labels)
    assert codes["040080"] == max(codes.values()) == 26600
    with (ROOT / "evidence/2026-11-18-tp-finan-cnv-e-dbf/comparacao.csv").open(
        encoding="utf-8", newline=""
    ) as f:
        in_dbf = {row["codigo"] for row in csv.DictReader(f) if row["descricao_no_dbf"]}
    assert {code: rows for code, rows in codes.items() if code not in in_dbf} == {
        "021014": 1550,
        "040082": 873,
        "040084": 10,
    }
    text = issue("faec_tp", "faec_tp-faixa-de-reserva")
    assert "os 32 códigos publicados estão entre os 100" in text
    assert "(021014, 040082 e 040084, em 2.433 registros) não estão no DBF" in text


def test_the_rd_files_of_the_federal_district_publish_a_uf_zi_only_a_range_reaches():
    """Every record of the five RDDF files measured has UF_ZI 530000. br_municgestor.cnv
    lists 530010 and reaches 530000 only through the range 530000-530009 of the line
    "530000 Distrito Federal": without that range those 76,276 records would have no
    label. No file read has a code of the other three ranges. The issue of the field says
    so in both dictionaries; the one of the rejected AIH adds that no RJ file of the
    Federal District was read."""
    in_range = measured(FROM_2008, "uf_zi_em_faixa")
    records = {f["file"]: int(f["records"]) for f in read(MEASURES / FROM_2008 / "arquivos.csv")}
    assert {key for _, key, _ in in_range} == {"530000"}
    assert {name: rows for name, _, rows in in_range} == {
        name: rows for name, rows in records.items() if name.startswith("RDDF")
    }
    assert sum(rows for _, _, rows in in_range) == 76276
    table = ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/CNV/br_municgestor.cnv"
    lines = table.read_text(encoding="latin-1").splitlines()
    (line,) = (row for row in lines if "530000" in row)
    assert line[9:59].strip() == "530000 Distrito Federal"
    assert line[60:].strip() == "530010,530000-530009,530011-539999"
    unmeasured = "A medida é do RD: nenhum arquivo RJ do Distrito Federal foi lido."
    for dataset in ("sih_aih_reduzida", "sih_aih_rejeitada"):
        field = load_dicionario(dataset).field_def("uf_zi")
        assert field["x-decode"]["530000"] == "530000 Distrito Federal"
        text = issue("uf_zi", "uf_zi-faixa-em-codigo-longo", dataset)
        assert "Nenhum arquivo lido publica uma dessas chaves" not in text
        assert "530000 em todos os 76.276 registros dos cinco arquivos RDDF" in text
        assert "todos esses registros ficariam sem rótulo" in text
        assert (unmeasured in text) == (dataset == "sih_aih_rejeitada")
