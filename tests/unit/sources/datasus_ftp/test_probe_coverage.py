"""The weekly probe checks a row's coverage against names read without the coverage cut.

`parse_name` gives a name outside a row's coverage to no row (ADR 0002), so `sources_for`
never returns one. The probe's two coverage checks read the listing themselves, or a file
published after a declared end (`EESP2610.dbc`, evidence/2026-11-20-cnes-ee-2610) would no
longer fail `test_coverage_end_is_not_a_stale_claim`.

The listing is the committed one of `SIHSUS/199201_200712/Dados` (FIXTURES.md), which the
two RD rows share.
"""

from __future__ import annotations

from dataclasses import replace

from omnisus.sources.datasus_ftp.datasets import REGISTRY
from omnisus.sources.datasus_ftp.inventory import Listing, _parse_msdos_line
from tests.integration.test_registry_probe import _published
from tests.support.listings import listing_lines

DIRECTORY = "/dissemin/publicos/SIHSUS/199201_200712/Dados"


def _listing(directory: str) -> Listing:
    assert directory == DIRECTORY
    lines = listing_lines("sihsus_199201_200712_dados_rd")
    entries = tuple(e for e in (_parse_msdos_line(line, DIRECTORY) for line in lines) if e)
    return Listing(entries=entries, skipped=0, path=DIRECTORY)


def _ends(scopes) -> tuple[tuple[int, int], tuple[int, int]]:
    months = [(s.ano, s.mes) for s in scopes]
    return min(months), max(months)


def test_each_rd_row_is_checked_against_its_own_months_only():
    """The files of the other era are read by the other row, so they are not this row's."""
    assert _ends(_published(REGISTRY["sih_aih_reduzida_1992_1997"], _listing)) == (
        (1992, 1),
        (1997, 12),
    )
    assert _ends(_published(REGISTRY["sih_aih_reduzida_1998_2007"], _listing)) == (
        (1998, 1),
        (2007, 12),
    )


def test_a_file_after_the_declared_end_is_still_seen():
    """A row that closed its coverage at 2006-12 would have the 323 files of 2007 after its
    end, read by no row; the probe has to see them to say the end is stale."""
    stale = replace(REGISTRY["sih_aih_reduzida_1998_2007"], coverage=((1998, 1), (2006, 12)))
    scopes = _published(stale, _listing)
    assert _ends(scopes) == ((1998, 1), (2007, 12))
    assert sum(1 for s in scopes if s.ano == 2007) == 323
