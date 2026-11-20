"""Import DENGBR files into one table of a lake, in the order given.

    uv run python evidence/2026-11-20-sinan-dengue/lake_misto.py <folder> <dataset> 2012 2006

The table is the dataset's (`sinan_dengue_2000_2012`, `sinan_dengue_2013` or `sinan_dengue`).

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
    dataset = sys.argv[2]
    for year in map(int, sys.argv[3:]):
        report = sus.import_dataset(
            dataset,
            scopes=[sus.ScopeKey(uf=None, ano=year)],
            target=target,
            policy="skip_same",
            run_id=f"{dataset}-{year}",
        )
        for outcome in report.outcomes:
            rows = outcome.result.rows if outcome.result else None
            print(dataset, year, outcome.status, outcome.code, rows, outcome.reason, flush=True)


if __name__ == "__main__":
    main()
