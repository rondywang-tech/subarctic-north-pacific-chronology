#!/usr/bin/env python3
"""Deterministically derive Bacon acc.mean from eligible dated-depth clusters.

Algorithm frozen before C1n execution:
1. Calibrate each retained determination independently on the integer-year grid
   bundled with rintcal (IntCal20/Marine20/SHCal20).  For curve row i,
   weight_i = NormalPDF(age - delta_R | curve_14C_i,
                        sqrt(error^2 + delta_STD^2 + curve_SD_i^2)).
   The calibrated median is the first grid age whose normalized cumulative
   probability is >= 0.5.  cc=0 determinations retain their supplied age.
2. At an exactly duplicated reported depth, take the ordinary median of the
   independently calibrated medians. Duplicate depths therefore form one
   eligible independent dated-depth cluster.
3. For every ordered depth pair i<j, compute
   (cal_median_j-cal_median_i)/(depth_j-depth_i). Exact duplicate depths have
   already been clustered, so every denominator is positive.
4. Sort all pairwise slopes numerically. The Theil-Sen result is the middle
   value for an odd count, or the arithmetic mean of the two middle values for
   an even count (Python statistics.median). No library regression default is
   used and ties are retained as separate pairwise observations.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
from pathlib import Path


def rintcal_curve_path(cc: int) -> Path:
    names = {1: "intcal20", 2: "marine20", 3: "shcal20"}
    if cc not in names:
        raise ValueError(f"No curve for cc={cc}")
    expr = f'cat(system.file("extdata/3Col_{names[cc]}.14C",package="rintcal"))'
    p = subprocess.run(["/usr/local/bin/Rscript", "-e", expr], check=True,
                       text=True, stdout=subprocess.PIPE).stdout.strip()
    path = Path(p)
    if not path.is_file():
        raise FileNotFoundError(f"rintcal curve unavailable: {path}")
    return path


def read_curve(path: Path) -> list[tuple[float, float, float]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            a, b, s = line.split()[:3]
            rows.append((float(a), float(b), float(s)))
    return rows


def calibrated_median(age: float, error: float, cc: int, dr: float,
                      drstd: float, curves: dict[int, list[tuple[float,float,float]]]) -> float:
    if cc == 0:
        return age
    curve = curves[cc]
    logs = []
    for _, curve_age, curve_sd in curve:
        sd = math.sqrt(error * error + drstd * drstd + curve_sd * curve_sd)
        z = (age - dr - curve_age) / sd
        logs.append(-0.5 * z * z - math.log(sd))
    m = max(logs)
    weights = [math.exp(v - m) for v in logs]
    half = 0.5 * sum(weights)
    cumulative = 0.0
    for (cal_bp, _, _), w in zip(curve, weights):
        cumulative += w
        if cumulative >= half:
            return cal_bp
    raise RuntimeError("calibrated median not found")


def derive(input_csv: Path) -> dict:
    with input_csv.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"labID", "age", "error", "depth", "cc", "delta.R", "delta.STD", "ta", "tb"}
    if not rows or set(rows[0]) != required:
        raise ValueError(f"unexpected input schema: {list(rows[0]) if rows else 'empty'}")
    ccs = sorted({int(float(r["cc"])) for r in rows if int(float(r["cc"])) != 0})
    curves = {cc: read_curve(rintcal_curve_path(cc)) for cc in ccs}
    by_depth: dict[float, list[float]] = {}
    determinations = []
    for row in rows:
        depth = float(row["depth"])
        med = calibrated_median(float(row["age"]), float(row["error"]),
                                int(float(row["cc"])), float(row["delta.R"]),
                                float(row["delta.STD"]), curves)
        by_depth.setdefault(depth, []).append(med)
        determinations.append({"labID": row["labID"], "depth_cm": depth,
                               "calibrated_median_cal_BP": med})
    clusters = [{"depth_cm": d, "calibrated_median_cal_BP": statistics.median(v),
                 "n_determinations": len(v)} for d, v in sorted(by_depth.items())]
    if len(clusters) < 2:
        raise ValueError("Theil-Sen is undefined with fewer than two dated-depth clusters")
    slopes = []
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            slopes.append((clusters[j]["calibrated_median_cal_BP"] - clusters[i]["calibrated_median_cal_BP"]) /
                          (clusters[j]["depth_cm"] - clusters[i]["depth_cm"]))
    return {"input_file": str(input_csv), "n_determinations": len(rows),
            "n_dated_depth_clusters": len(clusters), "clusters": clusters,
            "n_pairwise_slopes": len(slopes), "pairwise_slopes_sorted": sorted(slopes),
            "acc_mean_theil_sen_yr_cm": statistics.median(slopes),
            "determinations": determinations}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = derive(args.input_csv)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
