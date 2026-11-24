"""Counts of fields of the SIH notes of 2026-11-24 in RD files.

Usage: uv run --locked python evidence/2026-11-24-rd-sp-uti-cid-raca/medir.py DIR OUT
DIR holds the RD*.dbc files; OUT is the JSON written, one entry per file.
"""

import hashlib
import json
import sys
from pathlib import Path

import polars as pl

from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe


def counts(df: pl.DataFrame, column: str) -> dict[str, int]:
    table = df.group_by(column).len().sort(column)
    return {str(k): int(v) for k, v in zip(table[column], table["len"], strict=True)}


def measure(raw: bytes) -> dict[str, object]:
    df = dbc_bytes_to_lazyframe(raw, dataset="sih_aih_reduzida").collect()
    deaths = df.filter(pl.col("morte") == 1)
    raca99 = df.filter(pl.col("raca_cor") == "99")
    parto = df.filter(pl.col("cobranca").is_in([f"6{d}" for d in range(1, 8)]))
    injury = df.filter(pl.col("diag_princ").str.slice(0, 1).is_in(["S", "T"]))
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "rows": df.height,
        "marca_uti": counts(df, "marca_uti"),
        "uti_int_to_gt0": df.filter(pl.col("uti_int_to") > 0).height,
        "uti_int_to_gt0_marca_uti_00": df.filter(
            (pl.col("uti_int_to") > 0) & (pl.col("marca_uti") == "00")
        ).height,
        "uti_mes_to_999": df.filter(pl.col("uti_mes_to") == 999).height,
        "deaths": deaths.height,
        "deaths_cid_morte_not_0000_or_blank": deaths.filter(
            ~pl.col("cid_morte").str.strip_chars().is_in(["", "0000"])
        ).height,
        "cid_morte_0000": df.filter(pl.col("cid_morte") == "0000").height,
        "cid_asso_0000": df.filter(pl.col("cid_asso") == "0000").height,
        "raca_cor": counts(df, "raca_cor"),
        "raca_cor_99_dt_inter_max": raca99["dt_inter"].max() if raca99.height else None,
        "sexo": counts(df, "sexo"),
        "cobranca_61_67_by_morte": {
            f"{c}/{m}": int(n)
            for c, m, n in parto.group_by("cobranca", "morte")
            .len()
            .sort("cobranca", "morte")
            .rows()
        },
        "n_aih_digit5_by_ident": {
            f"{d}/{i}": int(n)
            for d, i, n in df.group_by(pl.col("n_aih").str.slice(4, 1).alias("d5"), "ident")
            .len()
            .sort("d5", "ident")
            .rows()
        },
        "raca_cor_05": df.filter(pl.col("raca_cor") == "05").height,
        "raca_cor_05_etnia_0000": df.filter(
            (pl.col("raca_cor") == "05") & (pl.col("etnia") == "0000")
        ).height,
        "raca_cor_not_05_etnia_not_0000": df.filter(
            (pl.col("raca_cor") != "05") & (pl.col("etnia") != "0000")
        ).height,
        "cobranca_61_67": parto.height,
        "cobranca_61_67_diar_acom_gt0": parto.filter(pl.col("diar_acom") > 0).height,
        "diag_princ_s_t": injury.height,
        "diag_princ_s_t_diagsec1_v_y": injury.filter(
            pl.col("diagsec1").str.slice(0, 1).is_in(["V", "W", "X", "Y"])
        ).height,
    }


def main() -> None:
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    result = {p.name: measure(p.read_bytes()) for p in sorted(folder.glob("RD*.dbc"))}
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
