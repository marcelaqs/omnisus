"""A `sim_obitos` map read from the CNV is verified, even where an older map differed (#184).

`gerar_decode_cnv.py` marks a claim `conflicting` when the map it replaces disagreed with
the CNV. The older maps had no source, so the disagreement is history: the claim is
`verified_in_source` and the issue that keeps the older labels is `resolved`, as in
`sih_aih_reduzida`. `tppos` is the exception: the official document gives it codes the
CNV does not list, so its claim stays `conflicting` with the issue open.
"""

from __future__ import annotations

import pytest

import omnisus as sus

ISSUE = "cnv-difere-do-mapa-anterior"


def _replaced_maps() -> dict[str, tuple[dict, dict]]:
    found = {}
    for column in sus.describe_dataset("sim_obitos")["fields"]:
        issues = [i for i in column["issues"] if i["id"] == ISSUE]
        if issues:
            (claim,) = [c for c in column["claims"] if c["target"] == "/field/codes"]
            found[column["field"]["name"]] = (claim, issues[0])
    return found


def test_twenty_six_maps_replaced_an_older_one() -> None:
    assert len(_replaced_maps()) == 26


@pytest.mark.parametrize("name", sorted(set(_replaced_maps()) - {"tppos"}))
def test_a_map_that_replaced_an_unsourced_one_is_verified(name) -> None:
    claim, issue = _replaced_maps()[name]
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    assert issue["status"] == "resolved" and "não tinha fonte" in issue["description"]


def test_tppos_stays_conflicting_because_the_document_lists_other_codes() -> None:
    claim, issue = _replaced_maps()["tppos"]
    assert (claim["status"], issue["status"]) == ("conflicting", "open")
    assert "'1' era 'Sim', CNV não lista" in issue["description"]
