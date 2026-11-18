"""The AN dictionary against the layout of the Informe Técnico and the DBF header (#183).

Real data: ``sia_an_pa_2014_10_mini.dbc`` is the whole ``ANPA1410.dbc`` (2 records; server
SHA-256 in ``tests/fixtures/FIXTURES.md``). The Informe Técnico SIASUS 2019-07
(``siasus-70fe69dbd4cf``) is not packaged, so no test reads its pages: section 3.4.3,
"LAYOUT DO ARQUIVO DE APAC DE NEFROLOGIA: ANUFAAMM.DBF", lists 60 fields on pages 7 to 9,
and each description claim quotes the row it was read from. What the tests can check is
that those 60 rows are the first 60 fields of the published file, in order, with the same
name, type and width.
"""

from __future__ import annotations

import re

import pytest

import omnisus as sus
from omnisus.sources.datasus_ftp.dbc import decompress_bytes
from omnisus.sources.datasus_ftp.dbf_contract import _read_field_descriptors
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe
from omnisus.transforms.dictionaries import load_dicionario

AN = "sia_apac_nefrologia"
FIXTURE = "sia_an_pa_2014_10_mini"
LOCATOR = re.compile(r"Seção 3\.4\.3, SEQ (\d+), ([A-Z_]+) (CHAR|NUMERIC) ?\((\d+)(?:\.(\d+))?\)")


@pytest.fixture
def header(dbc_fixture):
    return list(_read_field_descriptors(decompress_bytes(dbc_fixture(FIXTURE).read_bytes())))


def _description_claim(name: str) -> dict:
    claims = load_dicionario(AN).field_def(name)["x-metadata"]["claims"]
    (claim,) = [c for c in claims if c["target"] == "/field/description"]
    return claim


def test_the_60_rows_of_the_informe_layout_are_the_first_60_fields_of_the_file(header) -> None:
    """Order, name, type and width of each row the claims quote equal the DBF header."""
    assert len(header) == 61
    for position, descriptor in enumerate(header[:60], start=1):
        name = descriptor.name.strip()
        field = load_dicionario(AN).field_def(name.lower())
        assert field["description"], name
        claim = _description_claim(name.lower())
        assert claim["status"] == "unreviewed" and claim["reviewer"] is None, name
        (evidence,) = claim["evidence"]
        assert evidence["source_id"] == "siasus-70fe69dbd4cf", name
        assert evidence["pages"] == [7 if position <= 3 else 8 if position <= 58 else 9], name
        seq, quoted, kind, width, decimals = LOCATOR.fullmatch(evidence["locator"]).groups()
        assert (int(seq), quoted) == (position, name)
        assert (kind[0], int(width), int(decimals or 0)) == (
            descriptor.kind,
            descriptor.width,
            descriptor.decimals,
        ), name


def test_ap_natjur_is_published_and_the_informe_layout_does_not_list_it(header) -> None:
    """The 61st field of the file has no row in section 3.4.3, so it gets no description."""
    assert header[60].name.strip() == "AP_NATJUR"
    assert "description" not in load_dicionario(AN).field_def("ap_natjur")


def test_describe_dataset_resolves_the_descriptions_with_their_claims() -> None:
    fields = {f["field"]["name"]: f for f in sus.describe_dataset(AN)["fields"]}
    assert fields["an_peso"]["field"]["description"] == "Peso do paciente em kg"
    (claim,) = [c for c in fields["an_peso"]["claims"] if c["target"] == "/field/description"]
    assert claim["evidence"][0]["pages"] == [8]


@pytest.mark.parametrize("name", ["ap_ufdif", "ap_mndif"])
def test_the_layout_says_n_and_s_where_the_file_publishes_0_and_1(dbc_fixture, name) -> None:
    """Page 8 describes AP_UFDIF and AP_MNDIF with "(N = não, S = sim)"; ANPA1410 publishes
    0 in the first and 1 in the second, codes Invasao.CNV labels. The description is the document's, and the open
    issue says the two disagree."""
    frame = dbc_bytes_to_lazyframe(dbc_fixture(FIXTURE).read_bytes(), dataset=AN).collect()
    assert set(frame[name]) <= {"0", "1"}
    field = load_dicionario(AN).field_def(name)
    assert "(N = não, S = sim)" in field["description"]
    assert set(field["x-decode"]) == {"", "0", "1"}
    (issue,) = [
        i for i in field["x-metadata"]["issues"] if i["id"] == "informe-diverge-do-arquivo"
    ]
    assert issue["status"] == "open"
