"""Counts for four checks of the review of `sih_aih_reduzida`. Only counts leave the files.

Usage: uv run --locked python evidence/2026-11-28-rd-medidas-da-revisao/medir.py DIR OUT
DIR holds RD*.dbc files of SIHSUS/200801_/Dados/; OUT is the JSON written.

Every file gets the external-cause counts. The seven RDSP files of
evidence/2026-11-24-rd-sp-uti-cid-raca/ also get the counts of `raca_cor` 99, `diar_acom`,
blank and `0000` diagnoses and repeated `n_aih`. `n_aih_in_both` compares RDSP2303 and
RDSP2306.

Age in years: `cod_idade` 2 (days) and 3 (months) are under one year, 4 is `idade` years,
5 is `idade` plus 100 years; any other unit has no age.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import polars as pl

from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

SAO_PAULO = ("RDSP1412", "RDSP1502", "RDSP1902", "RDSP2001", "RDSP2303", "RDSP2306", "RDSP2512")
AFTER_ANNOUNCEMENT = ("RDSP2306", "RDSP2512")  # competences after April 2023
PAIR = ("RDSP2303", "RDSP2306")
ANNOUNCED = "20230401"  # dates are YYYYMMDD text, so text order is date order

AGE = (
    pl.when(pl.col("cod_idade").is_in(["2", "3"]))
    .then(0)
    .when(pl.col("cod_idade") == "4")
    .then(pl.col("idade"))
    .when(pl.col("cod_idade") == "5")
    .then(pl.col("idade") + 100)
)
PARTO = pl.col("cobranca").is_in([f"6{d}" for d in range(1, 8)])
GROUPS = {
    "cobranca_61_67": PARTO,
    "other_age_under_18": ~PARTO & (AGE < 18),
    "other_age_18_to_59": ~PARTO & (AGE >= 18) & (AGE < 60),
    "other_age_60_or_more": ~PARTO & (AGE >= 60),
    "other_age_unknown": ~PARTO & AGE.is_null(),
}


def first_letter(column: str, letters: str) -> pl.Expr:
    return pl.col(column).str.slice(0, 1).is_in(list(letters))


def blank(column: str) -> pl.Expr:
    return pl.col(column).is_null() | (pl.col(column).str.strip_chars() == "")


def counts(df: pl.DataFrame, by: pl.Expr) -> dict[str, int]:
    table = df.group_by(by.alias("key")).len().sort("key")
    return {str(k): int(n) for k, n in table.rows()}


def external_cause(df: pl.DataFrame) -> dict[str, int]:
    injury = df.filter(first_letter("diag_princ", "ST"))
    return {
        "diag_princ_s_t": injury.height,
        "diag_princ_s_t_diag_secun_v_y": injury.filter(first_letter("diag_secun", "VWXY")).height,
    }


def raca_cor_99(df: pl.DataFrame, name: str) -> dict[str, object]:
    rows = df.filter(pl.col("raca_cor") == "99")
    out: dict[str, object] = {
        "rows": rows.height,
        "dt_inter_from_2023_04_01": rows.filter(pl.col("dt_inter") >= ANNOUNCED).height,
    }
    if name in AFTER_ANNOUNCEMENT:
        out["by_dt_saida_month"] = counts(rows, pl.col("dt_saida").str.slice(0, 6))
        out["by_ident"] = counts(rows, pl.col("ident"))
        out["dt_inter_max"] = rows["dt_inter"].max()
        out["dt_saida_from_2023_04_01"] = rows.filter(pl.col("dt_saida") >= ANNOUNCED).height
    return out


def diar_acom(df: pl.DataFrame) -> dict[str, object]:
    billed = pl.col("diar_acom") > 0
    return {
        "rows_above_0": df.filter(billed).height,
        "by_group": {
            name: {
                "rows": df.filter(group).height,
                "rows_above_0": df.filter(group & billed).height,
            }
            for name, group in GROUPS.items()
        },
    }


def blank_or_0000(df: pl.DataFrame) -> dict[str, dict[str, int]]:
    return {
        column: {
            "blank": df.filter(blank(column)).height,
            "0000": df.filter(pl.col(column) == "0000").height,
        }
        for column in ("diag_secun", "cid_asso")
    }


def per_n_aih(df: pl.DataFrame) -> pl.DataFrame:
    """One row per `n_aih`: rows, the `ident` values, and the range of the two dates."""
    return df.group_by("n_aih").agg(
        pl.len().alias("rows"),
        pl.col("ident").unique().sort().str.join("+").alias("ident"),
        pl.col("dt_inter").min().alias("inter_min"),
        pl.col("dt_inter").max().alias("inter_max"),
        pl.col("dt_saida").min().alias("saida_min"),
        pl.col("dt_saida").max().alias("saida_max"),
    )


def n_aih_repeated(df: pl.DataFrame) -> dict[str, int]:
    """`n_aih` values that occur in more than one row of a file."""
    repeated = per_n_aih(df).filter(pl.col("rows") > 1)
    one_date = pl.col("inter_min") == pl.col("inter_max")
    return {
        "n_aih": repeated.height,
        "n_aih_with_one_dt_inter": repeated.filter(one_date).height,
        "rows": int(repeated["rows"].sum()),
    }


def n_aih_in_both(first: pl.DataFrame, second: pl.DataFrame) -> dict[str, object]:
    """`n_aih` values present in the two files, by `ident` in each and by `dt_inter`."""
    both = per_n_aih(first).join(per_n_aih(second), on="n_aih", suffix="_2")
    one_date = (pl.max_horizontal("inter_max", "inter_max_2")) == (
        pl.min_horizontal("inter_min", "inter_min_2")
    )
    table = both.group_by("ident", "ident_2", one_date.alias("same")).len()
    return {
        "files": list(PAIR),
        "n_aih": both.height,
        "n_aih_later_dt_saida_in_second": both.filter(
            pl.col("saida_min_2") > pl.col("saida_max")
        ).height,
        "pairs_of_rows": int((both["rows"] * both["rows_2"]).sum()),
        "rows_in_first": int(both["rows"].sum()),
        "rows_in_second": int(both["rows_2"].sum()),
        "by_ident_and_dt_inter": {
            f"{a}/{b}/{'same_dt_inter' if same else 'other_dt_inter'}": int(n)
            for a, b, same, n in table.sort("ident", "ident_2", "same").rows()
        },
    }


def by_competence(files: dict[str, dict]) -> dict[str, dict[str, int]]:
    """The external-cause counts summed over the files of each competence (YYMM of the name)."""
    out: dict[str, dict[str, int]] = {}
    for name, entry in files.items():
        month = out.setdefault(f"20{name[4:6]}-{name[6:8]}", {"files": 0, "rows": 0})
        month["files"] += 1
        month["rows"] += entry["rows"]
        for key, rows in entry["external_cause"].items():
            month[key] = month.get(key, 0) + rows
    return out


def main() -> None:
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    files: dict[str, dict] = {}
    pair: dict[str, pl.DataFrame] = {}
    for path in sorted(folder.glob("RD*.dbc")):
        raw = path.read_bytes()
        df = dbc_bytes_to_lazyframe(raw, dataset="sih_aih_reduzida").collect()
        entry: dict[str, object] = {
            "bytes": len(raw),
            "external_cause": external_cause(df),
            "rows": df.height,
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        if path.stem in SAO_PAULO:
            entry["raca_cor_99"] = raca_cor_99(df, path.stem)
            entry["diar_acom"] = diar_acom(df)
            entry["blank_or_0000"] = blank_or_0000(df)
            entry["n_aih_repeated"] = n_aih_repeated(df)
        if path.stem in PAIR:
            pair[path.stem] = df
        files[path.name] = entry
    result = {
        "competences": by_competence(files),
        "files": files,
        "n_aih_in_both": n_aih_in_both(pair[PAIR[0]], pair[PAIR[1]]),
    }
    text = json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True)
    out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
