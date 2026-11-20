"""Import one DENGBR file of each layout into one new lake, in the order given.

    uv run python evidence/2026-11-20-sinan-dengue/lake_misto.py <empty folder> 2017 2012 2013 2006

Downloads each file from the DATASUS server with `sus.import_dataset` and prints the
outcome of each scope, so a layout the lake table refuses shows its error.
"""

from __future__ import annotations

import sys
from pathlib import Path

import omnisus as sus


def main() -> None:
    folder = Path(sys.argv[1])
    target = f"ducklake:{folder / 'dengue.ducklake'}"
    for year in map(int, sys.argv[2:]):
        report = sus.import_dataset(
            "sinan_dengue",
            scopes=[sus.ScopeKey(uf=None, ano=year)],
            target=target,
            policy="skip_same",
            run_id=f"dengue-{year}",
        )
        for outcome in report.outcomes:
            rows = outcome.result.rows if outcome.result else None
            print(year, outcome.status, outcome.code, rows, outcome.reason, flush=True)


if __name__ == "__main__":
    main()
