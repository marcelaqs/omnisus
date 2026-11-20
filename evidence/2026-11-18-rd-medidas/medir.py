"""Count, in RD files from 2008, what bears on decisions of issue #182.

    uv run --locked python evidence/2026-11-18-rd-medidas/medir.py DATASET DIR OUT_DIR

DIR holds `RD*.dbc` files downloaded from `SIHSUS/200801_/Dados/` (DATASET
`sih_aih_reduzida`) or `SIHSUS/199201_200712/Dados/` (`sih_aih_reduzida_1998_2007`, the
months from 1998-01) of `ftp://ftp.datasus.gov.br/dissemin/publicos/`. A field a file lacks is left out. Writes
two files in OUT_DIR: `arquivos.csv` (file, bytes, SHA-256, records) and `medidas.csv` (file,
measure, key, rows). Only counts leave the files. The decoder loads every column, but no
measure uses GESTOR_CPF, and CPF_AUT is only counted as filled or not.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import polars as pl

from omnisus.sources.datasus_ftp.parse import dbc_bytes_to_lazyframe

ZERADO = [
    "uti_mes_in",
    "uti_mes_an",
    "uti_mes_al",
    "uti_int_in",
    "uti_int_an",
    "uti_int_al",
    "val_sadt",
    "val_rn",
    "val_acomp",
    "val_ortp",
    "val_sangue",
    "val_sadtsr",
    "val_transp",
    "val_obsang",
    "val_ped1ac",
    "rubrica",
    "num_proc",
    "tot_pt_sp",
    "cpf_aut",
]
"""The 19 fields IT_SIHSUS_1603 describes only as "Zerado"."""
COUNTED = ("homonimo", "faec_tp", "cid_notif")
RANGES = ((334501, 334530), (358001, 358058), (530000, 530009), (530011, 539999))
"""The ranges br_municgestor.cnv writes for UF_ZI (Rio de Janeiro, São Paulo, DF)."""


def filled(frame: pl.DataFrame, name: str) -> pl.Expr:
    """Rows where the field is neither blank nor zero (text made only of zeros is zero)."""
    if frame.schema[name] == pl.String:
        return pl.col(name).str.strip_chars(" 0").fill_null("") != ""
    return pl.col(name).fill_null(0) != 0


def counts(frame: pl.DataFrame, *names: str) -> list[tuple[str, int]]:
    grouped = frame.group_by(names).len().sort(names)
    return [("|".join(str(v) for v in row[:-1]), row[-1]) for row in grouped.iter_rows()]


def measures(frame: pl.DataFrame) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    for name in ZERADO:
        if name in frame.columns:
            out.append(("zerado_preenchido", name, frame.filter(filled(frame, name)).height))
    for name in COUNTED:
        if name in frame.columns:
            out += [(name, key, rows) for key, rows in counts(frame, name)]
    for n in range(1, 10):
        if f"tpdisec{n}" in frame.columns:
            crossed = frame.with_columns(
                pl.when(filled(frame, f"diagsec{n}"))
                .then(pl.lit("diagsec preenchido"))
                .otherwise(pl.lit("diagsec vazio"))
                .alias("diagsec")
            )
            out += [(f"tpdisec{n}", k, r) for k, r in counts(crossed, f"tpdisec{n}", "diagsec")]
    code = pl.col("uf_zi").cast(pl.Int64, strict=False)
    in_range = pl.any_horizontal([code.is_between(low, high) for low, high in RANGES])
    out += [("uf_zi_em_faixa", k, r) for k, r in counts(frame.filter(in_range), "uf_zi")]
    return out


def main() -> None:
    dataset, source, target = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    with (
        (target / "arquivos.csv").open("w", encoding="utf-8", newline="") as files,
        (target / "medidas.csv").open("w", encoding="utf-8", newline="") as measured,
    ):
        listed = csv.writer(files, lineterminator="\n")
        written = csv.writer(measured, lineterminator="\n")
        listed.writerow(["file", "size_bytes", "sha256", "records"])
        written.writerow(["file", "medida", "chave", "linhas"])
        for path in sorted(source.glob("RD*.dbc")):
            raw = path.read_bytes()
            frame = dbc_bytes_to_lazyframe(raw, dataset=dataset).collect()
            listed.writerow([path.name, len(raw), hashlib.sha256(raw).hexdigest(), frame.height])
            written.writerows([path.name, *row] for row in measures(frame))


if __name__ == "__main__":
    main()
