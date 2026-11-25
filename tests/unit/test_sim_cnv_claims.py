"""A `sim_obitos` map read from the CNV is verified, even where an older map differed (#184).

`gerar_decode_cnv.py` marks a claim `conflicting` when the map it replaces disagreed with
the CNV. The older maps had no claim, so the disagreement is history: the claim is
`verified_in_source` and the issue that keeps the older labels is `resolved`, as in
`sih_aih_reduzida`. Two fields were closed by a reviewer instead, where the Estrutura do SIM
and the CNV word the same answer differently: it gives `tppos` the codes 1 and 2 where the
files write the S and N of the CNV, and it calls `atestante` 1 "Assistente" where the CNV
says "Sim".
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


@pytest.mark.parametrize("name", sorted(set(_replaced_maps()) - {"atestante", "tppos"}))
def test_a_map_that_replaced_one_with_no_claim_is_verified(name) -> None:
    claim, issue = _replaced_maps()[name]
    assert (claim["method"], claim["status"]) == ("cnv-parse", "verified_in_source")
    assert issue["status"] == "resolved" and "não tinha claim" in issue["description"]


@pytest.mark.parametrize("name", ["atestante", "tppos"])
def test_a_reviewer_closed_the_two_maps_the_document_words_otherwise(name) -> None:
    claim, issue = _replaced_maps()[name]
    assert (claim["status"], issue["status"]) == ("verified_in_source", "resolved")
    assert "revisora marcelaqs" in issue["description"]
