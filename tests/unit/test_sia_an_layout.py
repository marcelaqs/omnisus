"""The AN dictionary against the layout of the Informe Técnico and the DBF header (#183).

Real data: ``sia_an_pa_2014_10_mini.dbc`` is the whole ``ANPA1410.dbc`` (2 records) and
``sia_an_rr_2014_01_mini.dbc`` every record of ``ANRR1401.dbc`` (162), with AP_CNSPCN
blanked; server SHA-256 in ``tests/fixtures/FIXTURES.md``. The Informe Técnico SIASUS 2019-07
(``siasus-70fe69dbd4cf``) is not packaged, so no test reads its pages: section 3.4.3,
"LAYOUT DO ARQUIVO DE APAC DE NEFROLOGIA: ANUFAAMM.DBF", lists 60 fields on pages 7 to 9,
and each description claim quotes the row it was read from. What the tests can check is
that those 60 rows are the first 60 fields of each published file, in order, with the same
name, type and width: ``ANRR1401`` has exactly those 60, and ``ANPA1410`` a 61st, AP_NATJUR.
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
FIXTURE_RR = "sia_an_rr_2014_01_mini"
LOCATOR = re.compile(r"Seção 3\.4\.3, SEQ (\d+), ([A-Z_]+) (CHAR|NUMERIC) ?\((\d+)(?:\.(\d+))?\)")


def _header(path) -> list:
    return list(_read_field_descriptors(decompress_bytes(path.read_bytes())))


def _description_claim(name: str) -> dict:
    claims = load_dicionario(AN).field_def(name)["x-metadata"]["claims"]
    (claim,) = [c for c in claims if c["target"] == "/field/description"]
    return claim


@pytest.mark.parametrize(("fixture", "fields"), [(FIXTURE, 61), (FIXTURE_RR, 60)])
def test_the_60_rows_of_the_informe_layout_are_the_first_60_fields_of_the_file(
    dbc_fixture, fixture, fields
) -> None:
    """Order, name, type and width of each row the claims quote equal the DBF header."""
    header = _header(dbc_fixture(fixture))
    assert len(header) == fields
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


def test_ap_natjur_is_in_anpa1410_only_and_the_informe_layout_does_not_list_it(
    dbc_fixture,
) -> None:
    """The 61st field of ANPA1410 (2014-10) has no row in section 3.4.3, so it gets no
    description; ANRR1401 (2014-01) ends at AN_HB, and the field's open issue says so."""
    assert _header(dbc_fixture(FIXTURE))[60].name.strip() == "AP_NATJUR"
    assert [d.name.strip() for d in _header(dbc_fixture(FIXTURE_RR))][-1] == "AN_HB"
    field = load_dicionario(AN).field_def("ap_natjur")
    assert "description" not in field
    (issue,) = field["x-metadata"]["issues"]
    assert (issue["id"], issue["status"]) == ("ap_natjur-nem-sempre-publicado", "open")


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


def test_ap_cnspcn_is_marked_as_the_cipher_anpa1410_publishes(dbc_fixture) -> None:
    """ANPA1410 fills AP_CNSPCN in its 2 records with 15 characters and no digit, the
    shape ``x-crypto: datasus-cns`` marks (``test_fixture_provenance``). The Informe row
    (p. 8) names the field and does not say it is ciphered. ANRR1401 as the server
    publishes it (SHA-256 in ``FIXTURES.md``) fills the column the same way in its 162
    records; the fixture blanks it because the cipher is reversible (#183), not because it
    was in clear, so this test reads ANPA1410 only."""
    frame = dbc_bytes_to_lazyframe(dbc_fixture(FIXTURE).read_bytes(), dataset=AN).collect()
    cells = list(frame["ap_cnspcn"])
    assert len(cells) == 2
    assert all(len(cell) == 15 and not any(ch.isdigit() for ch in cell) for cell in cells)
    assert load_dicionario(AN).field_def("ap_cnspcn").get("x-crypto") == "datasus-cns"
