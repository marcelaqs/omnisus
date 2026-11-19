"""RD from 2008: the dictionary declares every field the layouts of real files publish (#86).

The census of `SIHSUS/200801_/Dados` (evidence/2026-10-06-rd-2008-layouts/census.csv) has
six layouts, the fifth from 2014-01 and the sixth from 2025-03, which adds FONTE_ORC. One
fixture of each of the last two: RDRR2401 and an excerpt of RDRR2503.
"""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

import pytest
from scripts.gen_dicionario import fields_of

import omnisus as sus
from omnisus.metadata import sources_registry
from omnisus.sources.datasus_ftp import dbc
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario

ROOT = Path(__file__).resolve().parents[3]
CENSUS = ROOT / "evidence/2026-10-06-rd-2008-layouts/census.csv"
DATASET = "sih_aih_reduzida"
LAYOUTS = {"sih_rr_2024_01_mini": 5, "sih_rd_rr_2025_03_excerpt": 6}
IT_1603 = ROOT / "evidence/2026-11-18-it-sihsus-1603-layout-rd/tabela1.csv"
RD2008_DEF = ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/RD2008.DEF"
OLDER_CLAIMS = {"nasc", "sexo", "dt_inter", "dt_saida", "gestor_dt", "diagsec9"}
"""Fields whose `/field/physical_type` claim predates #182 and words its locator and note
another way; their width and status are checked like the others."""
OWN_DESCRIPTION = {"uf_zi", "cnes", "natureza"}
"""Fields whose description is not the document's sentence: `uf_zi` and `cnes` add what
the DEF and the lake say, and `natureza` has a paraphrase with its own verified claim."""


def census_layouts() -> dict[int, set[str]]:
    """Layout number -> its fields, lowercased, from the census."""
    out: dict[int, set[str]] = {}
    with CENSUS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out.setdefault(int(row["layout"]), set()).update(
                name.lower() for name in row["fields"].split(" ")[::2]
            )
    return out


def official_layout() -> list[dict[str, str]]:
    """Table 1 of IT_SIHSUS_1603.pdf (`sihsus-1e89d5f2cc41`), one dict per row."""
    with IT_1603.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fixture_fields(dbc_fixture, fixture: str) -> dict[str, str]:
    raw = dbc_fixture(fixture).read_bytes()
    return {f["name"]: f["type"] for f in fields_of(dbc.decompress_bytes(raw))}


def test_the_dictionary_declares_every_field_of_every_layout():
    declared = {f["name"] for f in load_dicionario(DATASET).fields}
    assert sorted(set().union(*census_layouts().values()) - declared) == []


@pytest.mark.parametrize("fixture", sorted(LAYOUTS))
def test_each_fixture_publishes_the_fields_of_its_layout(dbc_fixture, fixture):
    assert set(fixture_fields(dbc_fixture, fixture)) == census_layouts()[LAYOUTS[fixture]]


def test_the_official_layout_lists_the_fields_of_layout_5():
    """IT_SIHSUS_1603 is the report of 2016-03, and its Table 1 has the 113 fields the
    files publish from 2014-01 to 2025-02, in the order of the DBF header, once the three
    names it misspells are read as the DBF spells them (MÊS_CMPT, DI_INTER, DESTAO)."""
    rows = official_layout()
    assert len(rows) == 113
    assert {row["campo"] for row in rows} == census_layouts()[5]
    with CENSUS.open(encoding="utf-8", newline="") as f:
        (in_file_order,) = {row["fields"] for row in csv.DictReader(f) if row["layout"] == "5"}
    assert [row["campo"] for row in rows] == [
        name.lower() for name in in_file_order.split(" ")[::2]
    ]
    assert [
        row["nome_no_documento"]
        for row in rows
        if row["campo"] != row["nome_no_documento"].lower()
    ] == ["MÊS_CMPT", "DI_INTER", "DESTAO"]


def test_each_field_of_the_official_layout_carries_the_documents_description():
    """The description of a field is the sentence Table 1 prints for it, with a claim
    that names the page and quotes the row (#182). The 19 rows that say only "Zerado"
    are described as "Zerado"."""
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    for row in official_layout():
        if row["campo"] in OWN_DESCRIPTION:
            continue
        item = contract[row["campo"]]
        assert item["field"]["description"] == row["descricao"], row["campo"]
        claim = next(c for c in item["claims"] if c["target"] == "/field/description")
        assert (claim["status"], claim["method"]) == ("verified_in_source", "pdf-read")
        (evidence,) = claim["evidence"]
        assert evidence["source_id"] == "sihsus-1e89d5f2cc41"
        assert evidence["pages"] == [int(row["pagina"])]
        assert evidence["locator"] == (
            f"Tabela 1, linha {row['seq']}, {row['nome_no_documento']} {row['tipo']}: "
            f'"{row["descricao"]}"'
        )


def test_the_fields_the_document_calls_zerado_are_empty_in_rdrr2401(dbc_fixture):
    """Table 1 says only "Zerado" of 19 fields. In RDRR2401 the 17 numeric ones are 0 in
    every record, and the two text ones, NUM_PROC and CPF_AUT, are blank, not zeros."""
    zerado = [row["campo"] for row in official_layout() if row["descricao"] == "Zerado"]
    assert len(zerado) == 19
    raw = dbc_fixture("sih_rr_2024_01_mini").read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect().select(zerado)
    values = {name: frame[name].unique().to_list() for name in zerado}
    assert {name: found for name, found in values.items() if found != [0]} == {
        "num_proc": [""],
        "cpf_aut": [""],
    }


def test_fonte_orc_and_sis_just_are_labelled_as_their_sources_call_them():
    """RD2008.DEF line 274 calls FONTE_ORC "Fonte Orçamentária", and the field had no
    label. IT_SIHSUS_1603, p. 3, says SIS_JUST is the justification of the
    estabelecimento; the dictionary called it "Justificativa do sistema" (#182)."""
    def_line = RD2008_DEF.read_text(encoding="latin-1").splitlines()[273]
    assert [part.strip() for part in def_line.split(",")[:2]] == [
        "XFonte Orçamentária",
        "FONTE_ORC",
    ]
    (sis_just,) = (row for row in official_layout() if row["campo"] == "sis_just")
    assert sis_just["descricao"].startswith("Justificativa do estabelecimento para aceitação")
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    expected = {
        "fonte_orc": (
            "Fonte Orçamentária",
            "RD2008.DEF, linha 274: XFonte Orçamentária, FONTE_ORC",
        ),
        "sis_just": (
            "Justificativa do estabelecimento",
            'SIS_JUST char (50): "Justificativa do est',
        ),
    }
    for name, (label, quoted) in expected.items():
        assert contract[name]["field"]["label"] == label
        claim = next(c for c in contract[name]["claims"] if c["target"] == "/field/label")
        assert claim["status"] == "verified_in_source"
        assert quoted in claim["evidence"][0]["locator"]


OLDER_LAYOUT = ROOT / "evidence/2026-11-18-layout-reduzida-sihd/layout.csv"
WORDS_OF_THE_OFFICIAL_LAYOUT = {
    "ano_cmpt": "Ano de processamento da AIH",
    "mes_cmpt": "Mês de processamento da AIH",
    "qt_diarias": "Quantidade de diárias",
    "us_tot": "Valor total, em dólar",
    "cobranca": "Motivo de Saída/Permanência",
    "ind_vdrl": "Indica exame VDRL",
    "cid_notif": "CID de Notificação",
    "gestrisco": "Indicador se é gestante de risco",
    "gestor_tp": "Tipo de gestor",
}


ZERADO_LABELS = {
    "uti_mes_in": "Qtd de dias de UTI no mês inicial da internação",
    "uti_mes_an": "Qtd de dias de UTI no mês anterior à alta",
    "uti_mes_al": "Qtd de dias de UTI no mês da alta",
    "uti_int_in": "Dias em UTI no mês inicial (tipo ato = 34 ou 56)",
    "uti_int_an": "Dias em UTI no mês anterior à alta (tipo ato = 34 ou 56)",
    "uti_int_al": "Dias em UTI no mês da alta (tipo ato = 34 ou 56)",
    "val_sadt": "Valor de SADT",
    "val_rn": "Valor de recém-nato",
    "val_acomp": "Valor de acompanhante",
    "val_ortp": "Valor de órtese e prótese",
    "val_sangue": "Valor de sangue",
    "val_sadtsr": "Valor de SADT sem rateio",
    "val_transp": "Valor de transplante",
    "val_obsang": "Valor de anestesia",
    "val_ped1ac": "Valor de pediatria",
    "rubrica": "Número da rubrica",
    "num_proc": "Número do processamento",
    "tot_pt_sp": "Total de pontos em SP",
    "cpf_aut": "CPF do auditor que autorizou o homônimo",
}


def older_layout() -> list[dict[str, str]]:
    """Layout_REDUZIDA.pdf (`sihsus-f6084d22de30`), one dict per row: the layout of the
    reduced file the SIHD wrote, which the DATASUS page of manuals lists under "SIHD (uso
    até 12/2007)" and whose fields are those of the RD files of 2006-04 to 2007-12."""
    with OLDER_LAYOUT.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def folded(text: str) -> str:
    """Without case and without diacritics: the document prints capitals, some of them
    without the accent ("INTERNACAO")."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").casefold()


def test_the_older_layout_is_that_of_the_rd_files_of_2006_and_2007():
    """Layout_REDUZIDA.pdf has, row by row, the name, type, width and decimals of layout
    19 of the census of the RD files until 2007: the 23 files read from 2006-04 to
    2007-12. Its 75 names are, in the same order, 75 of the 86 fields of layout 1 of the
    census from 2008 (38 files, 2008-01 to 2010-12); the other 11 are what 2008 added. So
    the document describes the same file one layout earlier, not another product."""
    older = older_layout()
    names = [row["nome"].lower() for row in older]
    assert len(names) == len(set(names)) == 75
    with (ROOT / "evidence/2026-10-01-rd-1992-2007-layouts/census.csv").open(newline="") as f:
        last_before_2008 = [row for row in csv.DictReader(f) if row["layout"] == "19"]
    months = sorted(row["month"] for row in last_before_2008)
    assert (len(months), months[0], months[-1]) == (23, "2006-04", "2007-12")
    assert {row["fields"] for row in last_before_2008} == {
        " ".join(f"{row['nome']} {row['tipo']}{row['tam']}.{row['dec']}" for row in older)
    }
    with CENSUS.open(encoding="utf-8", newline="") as f:
        first_of_2008 = [row for row in csv.DictReader(f) if row["layout"] == "1"]
    months = sorted(row["month"] for row in first_of_2008)
    assert (len(months), months[0], months[-1]) == (38, "2008-01", "2010-12")
    (fields,) = {row["fields"] for row in first_of_2008}
    layout_1 = [name.lower() for name in fields.split(" ")[::2]]
    assert [name for name in layout_1 if name in names] == names
    assert set(layout_1) - set(names) == {
        "qt_diarias",
        "gestor_tp",
        "cnpj_mant",
        "complex",
        "financ",
        "faec_tp",
        "regct",
        "raca_cor",
        "etnia",
        "sequencia",
        "remessa",
    }


def test_the_page_of_manuals_lists_the_older_layout_under_its_period():
    """The six lines kept from the DATASUS page of manuals: the heading "SIHD (uso até
    12/2007)" and, after it and before any other heading, the link to the file. The
    listing of the directory has the file with the size the registry records."""
    evidence = OLDER_LAYOUT.parent
    excerpt = (evidence / "pagina-de-manuais-trecho.html").read_text(encoding="utf-8")
    heading = "<strong>SIHD (uso at&eacute; 12/2007)</strong>"
    link = (
        '<a href="ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/'
        'Layout_REDUZIDA.pdf">Layout do arquivo de REDUZIDA gerado pelo SIHD</a>'
    )
    assert excerpt.count("<strong>") == 1
    assert 0 <= excerpt.index(heading) < excerpt.index(link)
    listing = (evidence / "manuais-listing.txt").read_text(encoding="utf-8").splitlines()
    (line,) = (line for line in listing if line.endswith(" Layout_REDUZIDA.pdf"))
    (source,) = (s for s in sources_registry()["sources"] if s["id"] == "sihsus-f6084d22de30")
    assert len(listing) == 81
    assert int(line.split()[4]) == source["bytes"] == 26945
    assert source["url"].endswith("/SIHD/Manuais/Layout_REDUZIDA.pdf")


def test_nine_labels_are_the_words_of_the_official_layout():
    """The nine labels the maintainer chose in #182 (C2 and C3) among those that said
    more than IT_SIHSUS_1603 says of the field, or something else: "competência" where
    it says "processamento", "(sífilis)", "alto risco", "cobradas", "autorizador",
    "notificação compulsória". Each is now the document's description up to its full
    stop, or up to ", no formato". Other labels of the dictionary still have no claim."""
    official = {row["campo"]: row for row in official_layout()}
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    for name, label in WORDS_OF_THE_OFFICIAL_LAYOUT.items():
        row = official[name]
        assert row["descricao"].startswith(label), name
        assert row["descricao"].removeprefix(label) in {
            "",
            ".",
            ", no formato aaaa.",
            ", no formato mm.",
        }, name
        assert contract[name]["field"]["label"] == label
        claim = next(c for c in contract[name]["claims"] if c["target"] == "/field/label")
        assert (claim["status"], claim["method"]) == ("verified_in_source", "pdf-read")
        (evidence,) = claim["evidence"]
        assert evidence["source_id"] == "sihsus-1e89d5f2cc41"
        assert evidence["pages"] == [int(row["pagina"])]
        assert evidence["locator"] == (
            f"Tabela 1, linha {row['seq']}, {row['nome_no_documento']} {row['tipo']}: "
            f'"{row["descricao"]}"'
        )


def test_the_zerado_fields_take_the_label_of_the_layout_used_until_2007():
    """IT_SIHSUS_1603 says only "Zerado" of 19 fields, so it gives them no name. Their
    label is what Layout_REDUZIDA.pdf, the layout of 2006 and 2007, prints for the same
    field name, in sentence case and with the accents the capitals lack: equal to the
    document once case and diacritics are set aside. Each field says so in an open issue,
    because the document is of another period (#182, C2). The three UTI_INT fields also
    say that IT_SIHSUS_1603 calls their total "unidade intermediaria"."""
    zerado = [row["campo"] for row in official_layout() if row["descricao"] == "Zerado"]
    older = {row["nome"].lower(): row for row in older_layout()}
    contract = {item["field"]["name"]: item for item in sus.describe_dataset(DATASET)["fields"]}
    assert len(zerado) == 19
    for name in zerado:
        row, item = older[name], contract[name]
        assert folded(item["field"]["label"]) == folded(row["descricao"]), name
        assert item["field"]["description"] == "Zerado"
        claim = next(c for c in item["claims"] if c["target"] == "/field/label")
        assert (claim["status"], claim["method"]) == ("verified_in_source", "pdf-read")
        (evidence,) = claim["evidence"]
        assert evidence["source_id"] == "sihsus-f6084d22de30"
        assert evidence["pages"] == [int(row["pagina"])]
        assert evidence["locator"] == f'{row["nome"]}: "{row["descricao"]}"'
        (issue,) = [i for i in item["issues"] if i["id"] == "rotulo-do-layout-ate-2007"]
        assert issue["status"] == "open"
    assert {name: contract[name]["field"]["label"] for name in zerado} == ZERADO_LABELS
    (total,) = (row for row in official_layout() if row["campo"] == "uti_int_to")
    assert total["descricao"] == "Quantidade de diárias em unidade intermediaria."
    for name in zerado:
        (issue,) = [i for i in contract[name]["issues"] if i["id"] == "rotulo-do-layout-ate-2007"]
        assert "2006-04 a 2007-12" in issue["description"]
        assert (f'"{total["descricao"]}"' in issue["description"]) == name.startswith("uti_int_")


OTHER_DOCUMENTS = ROOT / "evidence/2026-11-18-sih-codigos-em-outros-documentos/trechos.csv"


def test_tpdisec_0_and_homonimo_stay_unlabelled_and_say_what_was_read(dbc_fixture):
    """Three registered documents give codes to these fields in another file. For the
    class of a secondary diagnosis, the SISAIH01 text layout ("0 - Quando não é
    preenchido o campo anterior") and the dictionary of the AIH tables ("0-Quando campo
    anterior em branco"). For the homonym mark, that dictionary and the layout of the RD
    files of 2006-2007 ("0 = não", "1 = sim"), while RDRR2401 publishes `0` and `2`. The
    codes keep no label (#182, C11 and C12), and the open issue of each field names each
    document, with page and field, and quotes it."""
    with OTHER_DOCUMENTS.open(encoding="utf-8", newline="") as f:
        passages = {row["campo"]: row for row in csv.DictReader(f)}
    assert len(passages) == 19
    sisaih01, mark = passages["DIAG_SEC_1_CLASS"], passages["AH_ST_DUPLICIDADE"]
    (older,) = (row for row in older_layout() if row["nome"] == "HOMONIMO")
    zero, blank = (
        "0 - Quando não é preenchido o campo anterior",
        "0-Quando campo anterior em branco",
    )
    assert zero in sisaih01["trecho"]
    assert mark["trecho"].endswith("Marca de homônimo, onde: 0 = não. 1 = sim.")
    assert older["descricao"] == "MARCA DE HOMONIMO ( 0 = não , 1 = sim)"
    registered = {source["id"] for source in sources_registry()["sources"]}
    assert {sisaih01["source_id"], mark["source_id"], "sihsus-f6084d22de30"} <= registered

    dictionary = load_dicionario(DATASET)
    for n in range(1, 10):
        row = passages[f"DIAG_SEC_{n}_CLASS"]
        named = f"campo {99 + 2 * n} DIAG_SEC_{n}_CLASS"
        assert row["trecho"].startswith(named.removeprefix("campo "))
        if n > 1:  # the other eight rows only point to the first
            assert row["trecho"].endswith("ver campo 101 ver campo 101")
            named += ", que remete ao campo 101 DIAG_SEC_1_CLASS"
        field = dictionary.field_def(f"tpdisec{n}")
        assert set(field["x-decode"]) == {"1", "2"}
        (issue,) = [i for i in field["x-metadata"]["issues"] if i["id"] == "tpdisec-0-sem-fonte"]
        assert issue["status"] == "open"
        assert f"({row['source_id']}, p. {row['paginas']}, {named})" in issue["description"]
        assert zero in issue["description"]
        table = passages[f"AH_DIAG_SEC_{n}_CLASS"]
        assert table["trecho"].startswith(f"AH_DIAG_SEC_{n}_CLASS Text 1 /* {blank}, 1-")
        cited = f"({table['source_id']}, p. {table['paginas']}, coluna AH_DIAG_SEC_{n}_CLASS)"
        assert f'{cited}: "{blank}"' in issue["description"]
    homonimo = dictionary.field_def("homonimo")
    assert "x-decode" not in homonimo
    (issue,) = [i for i in homonimo["x-metadata"]["issues"] if i["id"] == "homonimo-sem-fonte"]
    assert issue["status"] == "open"
    assert f"sihsus-f6084d22de30, p. {older['pagina']}" in issue["description"]
    assert older["descricao"] in issue["description"]
    assert f"{mark['source_id']}, pp. {mark['paginas']}" in issue["description"]
    assert "Marca de homônimo, onde: 0 = não. 1 = sim." in issue["description"]

    raw = dbc_fixture("sih_rr_2024_01_mini").read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect()
    assert dict(frame["homonimo"].value_counts().iter_rows()) == {"0": 3675, "2": 39}


PROCESSING_MONTH = {
    "sih_rr_2024_01_mini": ("2024", "01"),
    "sih_rd_rr_2025_03_excerpt": ("2025", "03"),
}


@pytest.mark.parametrize("fixture", sorted(LAYOUTS))
def test_each_field_declares_the_type_the_library_stages(dbc_fixture, fixture):
    """`type` in the dictionary is the contract's `logical_type`, which
    docs/dicionario/contrato.md calls "tipo adotado pela lib". Every field a real file
    publishes declares the family of the type `dbc_bytes_to_lazyframe` gives it, except
    the four declared `date`, which are text in the file and stay text when staged.
    Three did not (#182, C8 of the issue): ANO_CMPT and MES_CMPT were `integer` and are
    staged as text, the month with its leading zero; RUBRICA was `string` and is staged
    as an integer. The two fixtures are of layouts 5 and 6; in the census the three
    fields are C(4), C(2) and N(5) in every file of the six layouts."""
    import polars as pl

    raw = dbc_fixture(fixture).read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect()
    dictionary = load_dicionario(DATASET)
    declared = {name: dictionary.field_def(name)["type"] for name in frame.columns}
    staged = {
        name: "string"
        if dtype == pl.String
        else "integer"
        if dtype.is_integer()
        else "number"
        if dtype.is_float()
        else str(dtype)
        for name, dtype in frame.schema.items()
    }
    dates = {name for name, kind in declared.items() if kind == "date"}
    assert dates == {"nasc", "dt_inter", "dt_saida", "gestor_dt"}
    assert {staged[name] for name in dates} == {"string"}
    assert {
        name: (declared[name], staged[name])
        for name in declared
        if name not in dates and declared[name] != staged[name]
    } == {}
    year, month = PROCESSING_MONTH[fixture]
    assert frame["ano_cmpt"].unique().to_list() == [year]
    assert frame["mes_cmpt"].unique().to_list() == [month]
    assert frame["rubrica"].unique().to_list() == [0]
    with CENSUS.open(encoding="utf-8", newline="") as f:
        headers = [row["fields"].split(" ") for row in csv.DictReader(f)]
    assert len(headers) == 243
    assert {
        tuple(
            dict(zip(h[::2], h[1::2], strict=True))[n] for n in ("ANO_CMPT", "MES_CMPT", "RUBRICA")
        )
        for h in headers
    } == {("C4.0", "C2.0", "N5.0")}


def census_files() -> dict[str, dict[int, list[str]]]:
    """Text field -> width -> months of the files that publish it with that width."""
    out: dict[str, dict[int, list[str]]] = {}
    with CENSUS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            tokens = row["fields"].split(" ")
            for name, descriptor in zip(tokens[::2], tokens[1::2], strict=True):
                if descriptor.startswith("C"):
                    width = int(descriptor[1:].split(".")[0])
                    out.setdefault(name.lower(), {}).setdefault(width, []).append(row["month"])
    return out


def printed_widths() -> dict[str, int]:
    """Text field -> the N of the `char(N)` that Table 1 of IT_SIHSUS_1603 prints."""
    return {
        row["campo"]: int(row["tipo"].replace(" ", "")[5:-1])
        for row in official_layout()
        if row["tipo"].startswith("char")
    }


def header_widths(raw: bytes) -> dict[str, int]:
    """C field -> width, from the 32-byte field descriptors of a DBF header."""
    out = {}
    for start in range(32, int.from_bytes(raw[8:10], "little") - 1, 32):
        descriptor = raw[start : start + 32]
        if descriptor[11:12] == b"C":
            out[descriptor[:11].rstrip(b"\x00").decode("ascii").lower()] = descriptor[16]
    return out


def physical_type_claims() -> dict[str, tuple[dict, dict]]:
    """Field -> (resolved field, its `/field/physical_type` claim)."""
    return {
        item["field"]["name"]: (
            item["field"],
            next(c for c in item["claims"] if c["target"] == "/field/physical_type"),
        )
        for item in sus.describe_dataset(DATASET)["fields"]
    }


def test_each_text_field_declares_the_width_the_files_publish():
    """`physical_type` of a C field is its DBF descriptor in the last layout read (6,
    2025-03 to 2026-07), from the census. The claim is verified where Table 1 of
    IT_SIHSUS_1603 prints the same width and conflicting where it prints another, and it
    cites the row; its note counts the files read with each width. FONTE_ORC is not in
    the document, so its claim is unreviewed and cites only the census (#182)."""
    printed = printed_widths()
    rows = {row["campo"]: row for row in official_layout()}
    resolved = physical_type_claims()
    for name, widths in census_files().items():
        (width,) = (w for w, months in widths.items() if max(months) == "2026-07")
        field, claim = resolved[name]
        assert field["physical_name"] == name.upper()
        assert field["physical_type"] == {"type": "string", "length": width}, name
        if name not in printed:
            assert (claim["status"], claim["evidence"]) == ("unreviewed", []), name
        else:
            expected = "verified_in_source" if printed[name] == width else "conflicting"
            assert claim["status"] == expected, name
        if name in OLDER_CLAIMS:
            continue
        if name in printed:
            (evidence,) = claim["evidence"]
            assert evidence["pages"] == [int(rows[name]["pagina"])], name
            assert evidence["locator"] == (
                f"Tabela 1, linha {rows[name]['seq']}, {rows[name]['nome_no_documento']} "
                f"{rows[name]['tipo']}"
            ), name
        for other, months in widths.items():
            assert f"C({other}) nos {len(months)} " in claim["note"], name
            assert f"de {min(months)} a {max(months)}" in claim["note"], name


@pytest.mark.parametrize("fixture", sorted(LAYOUTS))
def test_the_declared_widths_are_those_of_a_real_dbf_header(dbc_fixture, fixture):
    """The census is a transcription; RDRR2401 (layout 5) and RDRR2503 (layout 6) are the
    files. Every C field of their headers has the declared width."""
    published = header_widths(dbc.decompress_bytes(dbc_fixture(fixture).read_bytes()))
    assert set(published) == {n for n in census_files() if n in census_layouts()[LAYOUTS[fixture]]}
    resolved = physical_type_claims()
    assert {name: resolved[name][0]["physical_type"]["length"] for name in published} == published


def test_the_document_and_the_files_disagree_on_the_width_of_seven_text_fields():
    """Printed type in Table 1 against the DBF descriptors of the files read. Six fields
    differ in the last layout; INSC_PN differs only in the files of 2008-01 to 2011-12,
    which the table, "para janeiro de 2008 em diante", also covers. Each has an open
    issue that says so; `diagsec9` had it already (#67)."""
    printed = printed_widths()
    differing = {
        name: (printed[name], sorted(widths))
        for name, widths in census_files().items()
        if name in printed and set(widths) != {printed[name]}
    }
    assert differing == {
        "nacional": (2, [3]),
        "raca_cor": (4, [2]),
        "cbor": (3, [6]),
        "gestor_cod": (3, [3, 5]),
        "gestor_cpf": (11, [15]),
        "insc_pn": (12, [10, 12]),
        "diagsec9": (4, [1]),
    }
    dictionary = load_dicionario(DATASET)
    for name, (doc, widths) in differing.items():
        issues = dictionary.field_def(name)["x-metadata"]["issues"]
        expected = "diagsec9-c1" if name == "diagsec9" else "largura-difere-do-documento"
        (issue,) = (i for i in issues if i["id"] == expected and i["status"] == "open")
        assert f"char({doc})" in issue["description"].replace("char (", "char("), name
        assert all(f"C({width})" in issue["description"] for width in widths), name


def test_two_text_fields_change_width_in_2012():
    """In the files read, GESTOR_COD is C(3) and INSC_PN C(10) from 2008-01 to 2011-12, and
    C(5) and C(12) from 2012-01 on; no other text field changes width. RDRR, RDSP and
    RDMG were read on both sides of the change. The contract holds one `physical_type`
    per field, so the claim's note carries the older width."""
    changing = {
        name: {width: (min(months), max(months)) for width, months in widths.items()}
        for name, widths in census_files().items()
        if len(widths) > 1
    }
    assert changing == {
        "gestor_cod": {3: ("2008-01", "2011-12"), 5: ("2012-01", "2026-07")},
        "insc_pn": {10: ("2008-01", "2011-12"), 12: ("2012-01", "2026-07")},
    }
    with CENSUS.open(encoding="utf-8", newline="") as f:
        read = {
            row["file"][:4] for row in csv.DictReader(f) if row["month"] in ("2011-12", "2012-01")
        }
    assert read == {"RDRR", "RDSP", "RDMG"}


def test_fonte_orc_takes_the_labels_of_fonterem(dbc_fixture):
    """RD2008.DEF line 274 binds FONTE_ORC to CNV/fonterem.CNV at position 1. The table
    names 01-04, each also as '1' and ' 1', and opens with the literal key '  -zz' (#24);
    '00', the only value of the excerpt, is not a key, and the field's issue says so."""
    published = fixture_fields(dbc_fixture, "sih_rd_rr_2025_03_excerpt")
    field = load_dicionario(DATASET).field_def("fonte_orc")
    assert field["type"] == published["fonte_orc"]
    labels = {
        "01": "MOD.1-SERVICO DE SAUDE - AES",
        "02": "MOD.2-EQUIPE VOLANTES-AES",
        "03": "CREDITO FINANC.PARC.VENCIDAS E VICENDAS",
        "04": "CREDITO FINANCEIRO TRANSACAO TRIBUTARIA",
    }
    expected = {"  -zz": "Branco Ignorado"}
    for code, label in labels.items():
        expected |= {code: label, code[1]: label, f" {code[1]}": label}
    assert field["x-decode"] == expected
    (claim,) = (c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes")
    assert claim["method"] == "cnv-parse"
    assert "FONTE_ORC, 1, CNV/fonterem.CNV" in claim["evidence"][0]["locator"]
    assert [i["id"] for i in field["x-metadata"]["issues"]] == ["fonte_orc-00-sem-fonte"]


def test_uf_zi_is_the_gestor_municipality(dbc_fixture):
    """RD2008.DEF lines 175-176 call UF_ZI 'Município gestor' (CNV/br_municgestor.cnv),
    and RDRR2401 publishes it with 6 digits, the width of a municipality code; the
    dictionary called it "UF do gestor" (#155)."""
    def_lines = (
        (ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/RD2008.DEF")
        .read_text(encoding="latin-1")
        .splitlines()
    )
    assert [line.split(",")[0][1:].strip() for line in def_lines[174:176]] == [
        "Município gestor",
        "Município gestor",
    ]
    raw = dbc_fixture("sih_rr_2024_01_mini").read_bytes()
    values = dbc_bytes_to_lazyframe(raw, dataset=DATASET).collect()["uf_zi"]
    assert values.str.contains(r"^\d{6}$").all()
    assert load_dicionario(DATASET).field_def("uf_zi")["label"] == "Município gestor"


MUNICGESTOR = ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih/CNV/br_municgestor.cnv"


@pytest.mark.parametrize(
    ("dataset", "fixture", "def_member", "def_lines", "published"),
    [
        (
            "sih_aih_reduzida",
            "sih_rr_2024_01_mini",
            "RD2008.DEF",
            (175, 176),
            {"140000": 2920, "140010": 794},
        ),
        (
            "sih_aih_rejeitada",
            "sih_rj_rr_2024_01_mini",
            "RJ2008.DEF",
            (177, 178),
            {"140000": 10, "140010": 20},
        ),
    ],
)
def test_uf_zi_takes_the_labels_of_br_municgestor(
    dbc_fixture, dataset, fixture, def_member, def_lines, published
):
    """The RD and the RJ DEF bind UF_ZI to CNV/br_municgestor.cnv at position 1, and no
    other line of either names the field. The table gives the code UF0000 of each of the
    26 states the label "<state> - Gestão estadual": RDRR2401 publishes 140000 in 2,920
    of its 3,714 records and 140010 (Boa Vista) in 794. The field holds no reference to
    aux_municipios, where 140000 is "Município ignorado - RR" (#182)."""
    import io
    import json
    import zipfile

    import polars as pl

    text = (MUNICGESTOR.parent.parent / def_member).read_text(encoding="latin-1").splitlines()
    assert [n for n, line in enumerate(text, 1) if "UF_ZI" in line.upper()] == list(def_lines)
    for n in def_lines:
        _, field, start, table = (part.strip() for part in text[n - 1].split(","))
        assert (field, start, table) == ("UF_ZI", "1", "CNV\\br_municgestor.cnv")
    raw = dbc_fixture(fixture).read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=dataset).collect().select("uf_zi")
    assert dict(frame["uf_zi"].value_counts().rows()) == published
    labelled = sus.label(dataset, frame, columns=["uf_zi"])
    assert dict(labelled.unique().rows()) == {
        "140000": "140000 Roraima - Gestão estadual",
        "140010": "140010 Boa Vista",
    }
    field = load_dicionario(dataset).field_def("uf_zi")
    assert "foreignKeys" not in field
    (claim,) = (c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes")
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    assert "UF_ZI" in claim["evidence"][0]["locator"]
    assert claim["evidence"][0]["locator"].endswith("CNV/br_municgestor.cnv")
    vinculos = json.loads(
        (ROOT / "src/omnisus/data/dicionarios/sources/cnv/vinculos.json").read_text("utf-8")
    )["datasets"][dataset]
    assert vinculos["campos"]["uf_zi"] == "sih/CNV/br_municgestor.cnv"
    assert "uf_zi" not in vinculos["sem_cnv"]
    bootstrap = zipfile.ZipFile(ROOT / "src/omnisus/data/auxiliares-bootstrap.zip")
    municipios = pl.read_parquet(io.BytesIO(bootstrap.read("aux_municipios.parquet")))
    assert municipios.filter(pl.col("codigo_6") == "140000")["nome"].to_list() == [
        "Município ignorado - RR"
    ]


@pytest.mark.parametrize(
    ("dataset", "fixture", "def_member", "def_lines", "published"),
    [
        (
            "sih_aih_reduzida",
            "sih_rr_2024_01_mini",
            "RD2008.DEF",
            (271, 272, 273),
            {"": 3432, "040080": 282},
        ),
        (
            "sih_aih_rejeitada",
            "sih_rj_rr_2024_01_mini",
            "RJ2008.DEF",
            (274, 275, 276),
            {"": 26, "040080": 4},
        ),
    ],
)
def test_faec_tp_takes_the_labels_tp_finan_lists(
    dbc_fixture, dataset, fixture, def_member, def_lines, published
):
    """The RD and the RJ DEF bind FAEC_TP to CNV/TP_FINAN.CNV on three lines that write
    DS_TPFIN where the start column goes; the maintainer decided in #182 to read them as
    position 1 and to label the 100 codes the table lists one by one. RDRR2401 publishes
    040080 in 282 records and blank in 3,432; the table lists both. The open issue of the
    field says what was decided and that the table's reserve range 000000-999999 gives no
    label."""
    import json

    text = (MUNICGESTOR.parent.parent / def_member).read_text(encoding="latin-1").splitlines()
    assert [n for n, line in enumerate(text, 1) if "FAEC_TP" in line.upper()] == list(def_lines)
    for n in def_lines:
        _, field, start, table = (part.strip() for part in text[n - 1].split(","))
        assert (field, start, table) == ("FAEC_TP", "DS_TPFIN", "CNV\\TP_FINAN.CNV")
    raw = dbc_fixture(fixture).read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=dataset).collect().select("faec_tp")
    assert dict(frame["faec_tp"].value_counts().rows()) == published
    labelled = sus.label(dataset, frame, columns=["faec_tp"])
    assert dict(labelled.unique().rows()) == {
        "": "Não discriminado/Não se aplica",
        # three blanks before the parenthesis and "ä" (0xE4), as the table writes them
        "040080": "Programa Agora Tem Especialistas - Componente Cirúrgico   (antigo Reduçäo das Filas)",
    }
    field = load_dicionario(dataset).field_def("faec_tp")
    assert len(field["x-decode"]) == 101
    assert {len(code) for code in field["x-decode"]} == {0, 6}
    (claim,) = (c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes")
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    assert "FAEC_TP, DS_TPFIN (posição 1 revista)" in claim["evidence"][0]["locator"]
    assert claim["evidence"][0]["locator"].endswith("CNV/TP_FINAN.CNV")
    (issue,) = [i for i in field["x-metadata"]["issues"] if i["id"] == "faec_tp-faixa-de-reserva"]
    assert issue["status"] == "open"
    assert "000000-999999" in issue["description"] and "DS_TPFIN" in issue["description"]
    vinculos = json.loads(
        (ROOT / "src/omnisus/data/dicionarios/sources/cnv/vinculos.json").read_text("utf-8")
    )["datasets"][dataset]
    assert vinculos["campos"]["faec_tp"] == "sih/CNV/TP_FINAN.CNV"
    assert "faec_tp" not in vinculos["sem_cnv"]


def test_br_municgestor_writes_ranges_in_a_table_of_long_codes():
    """TabWin.pdf (pp. 90-91) documents `first-last` only for variables of up to 4
    characters. br_municgestor.cnv declares 6 and writes ranges on three lines (Rio de
    Janeiro, São Paulo, Distrito Federal), which the map expands: 10,087 of its 15,731
    keys are labelled only through them. The maintainer decided in #182 that the map
    follows the table as published, ranges included: the five RDDF files measured
    publish 530000, which only a range reaches (test_sih_rd_measures.py). The field's
    issue records the divergence and the decision, as resolved, in both datasets. Read
    from the packaged table, line by line."""
    header, *body = MUNICGESTOR.read_text(encoding="latin-1").splitlines()
    assert header.split() == ["5596", "6"]
    explicit: set[str] = set()
    ranged: set[str] = set()
    with_range = []
    for line in body:
        for token in line[60:].strip().rstrip(",").split(","):
            if "-" in token:
                first, last = token.split("-")
                ranged.update(f"{n:06d}" for n in range(int(first), int(last) + 1))
                with_range.append(line[9:59].strip())
            else:
                explicit.add(token)
    assert sorted(set(with_range)) == [
        "330455 Rio de Janeiro",
        "355030 São Paulo",
        "530000 Distrito Federal",
    ]
    assert len(ranged - explicit) == 10087
    assert sum("Gestão estadual" in line for line in body) == 26
    for dataset in ("sih_aih_reduzida", "sih_aih_rejeitada"):
        field = load_dicionario(dataset).field_def("uf_zi")
        assert set(field["x-decode"]) == explicit | ranged
        assert len(field["x-decode"]) == 15731
        assert field["x-decode"]["149999"] == "140000 Roraima - Gestão estadual"
        assert field["x-decode"]["530010"] == "530000 Distrito Federal"
        (issue,) = field["x-metadata"]["issues"]
        assert (issue["id"], issue["status"]) == ("uf_zi-faixa-em-codigo-longo", "resolved")
        assert "10.087 das 15.731" in issue["description"]
        assert (
            "Resolvido em 2026-11-18 (issue #182): o mapa expande as faixas"
            in issue["description"]
        )


COD_IDADE = {"2": "Dias", "3": "Meses", "4": "Anos", "5": "Anos (somar 100)"}


@pytest.mark.parametrize(
    ("dataset", "fixture", "def_member", "def_lines", "published"),
    [
        (
            "sih_aih_reduzida",
            "sih_rr_2024_01_mini",
            "RD2008.DEF",
            range(188, 192),
            {"2": 157, "3": 175, "4": 3378, "5": 4},
        ),
        (
            "sih_aih_rejeitada",
            "sih_rj_rr_2024_01_mini",
            "RJ2008.DEF",
            range(193, 197),
            {"2": 4, "3": 4, "4": 22},
        ),
    ],
)
def test_cod_idade_labels_the_measured_units(
    dbc_fixture, dataset, fixture, def_member, def_lines, published
):
    """#6: the RD and RJ DEF bind COD_IDADE to IDADEBAS, IDADEPUB, IDADE18 and IDADEDET.CNV,
    which read 3 characters (unit + age); IDADEDET has 2xx days, 3xx months, 4xx years,
    500-530 "100 anos" to "130 anos" and 000 "Idade inválida". The 1-character unit is
    measured, not read: '5' is a year to add to 100, and '0' gets no label (no source says
    "Ignorada"; no SIH fixture publishes '0', so that part is checked on the dictionary).
    The RJ had no map and takes the same one."""
    text = (ROOT / "src/omnisus/data/dicionarios/sources/cnv/sih" / def_member).read_text(
        encoding="latin-1"
    )
    bound = [text.splitlines()[n - 1].split(",") for n in def_lines]
    assert [(f.strip(), t.strip()) for _, f, _, t in bound] == [
        ("COD_IDADE", f"CNV\\{cnv}.CNV") for cnv in ("IDADEBAS", "IDADEPUB", "IDADE18", "IDADEDET")
    ]
    raw = dbc_fixture(fixture).read_bytes()
    frame = dbc_bytes_to_lazyframe(raw, dataset=dataset).collect().select("cod_idade")
    assert dict(frame["cod_idade"].value_counts().rows()) == published
    labelled = sus.label(dataset, frame, columns=["cod_idade"])
    assert dict(labelled.unique().rows()) == {code: COD_IDADE[code] for code in published}
    field = load_dicionario(dataset).field_def("cod_idade")
    assert field["x-decode"] == COD_IDADE
    (claim,) = (c for c in field["x-metadata"]["claims"] if c["target"] == "/field/codes")
    assert claim["status"] == "unreviewed"
    assert "sih-tab-714ed980d483" in {e["source_id"] for e in claim["evidence"]}
    (entry,) = field["x-metadata"]["issues"]
    assert (entry["id"], entry["status"]) == ("cod_idade-sem-tabela", "open")
    assert all(s in entry["description"] for s in ("IDADEDET.CNV", "IDADEBAS.CNV", "'0'"))
