"""What the `seriescfal` and `seriescmae` maps rest on, and where the sources differ (#184).

`Obito_1996_CID10.def` links both fields to `SERIEFAL.CNV` in lines that begin with a
lowercase `x`. TabWin.pdf (`tabwin-bb98cff14765`, p. 87) does not list `X`, in either
case, among the functions of a DEF line, so each field keeps an open issue that says so;
the same holds for every field bound by an `X` line. The CNV lists `0` and `9`; the
Estrutura do SIM says "Números de 1 a 8", and in the audited files every value is blank
or a number from 1 to 8.
"""

from __future__ import annotations

from importlib import resources

import pytest

import omnisus as sus
from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

FIELDS = ["seriescfal", "seriescmae"]


def _field(name: str) -> dict:
    fields = sus.describe_dataset("sim_obitos")["fields"]
    (found,) = [c for c in fields if c["field"]["name"] == name]
    return found


def _open_issue(name: str, issue: str) -> dict:
    (found,) = [i for i in _field(name)["issues"] if i["id"] == issue]
    assert found["status"] == "open"
    return found


@pytest.mark.parametrize("name", FIELDS)
def test_the_def_line_begins_with_a_lowercase_x_and_the_field_says_so(name) -> None:
    packaged = resources.files("omnisus") / "data/dicionarios/sources/cnv/sim/Obito_1996_CID10.def"
    lines = [
        line
        for line in packaged.read_bytes().decode("latin-1").splitlines()
        if name in line.lower() and not line.startswith(";")
    ]
    assert len(lines) == 1 and lines[0].startswith("x*") and "SERIEFAL.CNV" in lines[0]
    assert "p. 87" in _open_issue(name, "def-liga-por-linha-x")["description"]


@pytest.mark.parametrize("fixture", ["sim_rr_2022_mini", "sim_rr_2023_mini"])
@pytest.mark.parametrize("name", FIELDS)
def test_the_cnv_lists_0_and_9_and_the_files_hold_1_to_8(dbc_fixture, fixture, name) -> None:
    """Real data: in DORR2022 and DORR2023 no value is 0 or 9, which the CNV also labels."""
    frame = dbc_bytes_to_lazyframe(
        dbc_fixture(fixture).read_bytes(), dataset="sim_obitos"
    ).collect()
    values = {v for v in frame[name].to_list() if v}
    assert values and values <= set("12345678")
    codes = {c["value"] for c in _field(name)["field"]["codes"]}
    assert {"0", "9"} <= codes
    assert "1 a 8" in _open_issue(name, "seriefal-cnv-lista-0-e-9")["description"]
