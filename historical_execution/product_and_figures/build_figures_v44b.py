#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import re

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/essd_figures_mplconfig")

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter


ROOT = Path("/Volumes/UH100/paleo_data/np_terrigenous_db")
RELEASE = ROOT / "audit_2026-07/v7_metadata_correction_2026-08-31/PANGAEA_v1_metadata_corrected_v7"
OUT = ROOT / "audit_2026-07/ESSD_V44B_TARGETED_CLOSURE_2026-09-07/06_figures"
OUT.mkdir(parents=True, exist_ok=True)

MASTER_PATH = ROOT / "master_inventory_v7.csv"
AGE_DIR = RELEASE / "age_models"
RC_PATH = RELEASE / "radiocarbon/radiocarbon_input_table_v1.csv"
CLUSTER_PATH = RELEASE / "clusters/dated_depth_cluster_table_v1.csv"
CALMED_PATH = ROOT / "audit_2026-07/worklist_2026-08-01/C1h_reachable_accmean/C1h_calibrated_cluster_medians.csv"

master = pd.read_csv(MASTER_PATH)
rc = pd.read_csv(RC_PATH)
clusters = pd.read_csv(CLUSTER_PATH)
calmed = pd.read_csv(CALMED_PATH)

assert len(master) == 21
assert (master["sub_region"] == "transition_zone").sum() == 2
assert len(list(AGE_DIR.glob("*.csv"))) == 18

REGION_LABELS = {
    "bering_sea": "Bering Sea",
    "alaska_gulf": "Gulf of Alaska",
    "okhotsk": "Sea of Okhotsk",
    "open_ocean": "Open subarctic Pacific",
    "transition_zone": "Transition-zone excluded",
}
REGION_COLORS = {
    "bering_sea": "#0072B2",
    "alaska_gulf": "#E69F00",
    "okhotsk": "#009E73",
    "open_ocean": "#CC79A7",
    "transition_zone": "#858585",
}
STATUS_LABELS = {
    "precision_class_assigned": "class-assigned",
    "not_ranked_sparse_control": "sparse-control",
    "legacy": "legacy",
    "excluded_no_chronology": "no chronology",
    "excluded_transition_zone": "transition-zone excluded",
}
STATUS_MARKERS = {
    "precision_class_assigned": "o",
    "not_ranked_sparse_control": "^",
    "legacy": "s",
    "excluded_no_chronology": "x",
    "excluded_transition_zone": "D",
}

mpl.rcParams.update({
    "font.family": "Arial",
    "font.size": 8.0,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.65,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.7,
    "ytick.major.size": 2.7,
    "lines.linewidth": 1.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})


def save_all(fig: plt.Figure, stem: str) -> None:
    for ext in ("pdf", "svg"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(OUT / f"{stem}.png", dpi=600, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def write_csv(df: pd.DataFrame, name: str) -> None:
    # Seventeen significant digits preserve round-trip equality for IEEE-754 doubles.
    df.to_csv(OUT / name, index=False, encoding="utf-8", na_rep="", float_format="%.17g")


def human_status(row: pd.Series) -> str:
    return STATUS_LABELS.get(row["final_status"], row["final_status"])


def age_model_path(core_id: str, segment: str) -> Path:
    return AGE_DIR / f"{core_id}__{segment}.csv"


# ---------------------------------------------------------------------------
# Figure 1 — regional coverage

fig1_rows = master.copy()
fig1_rows["lon_plot_0_360"] = np.where(fig1_rows["lon"] < 0, fig1_rows["lon"] + 360, fig1_rows["lon"])
fig1_rows["display_label"] = np.where(
    fig1_rows["core_id"].eq("IODP-U1419"),
    "IODP-U1419 " + fig1_rows["segment"].astype(str),
    fig1_rows["core_id"],
)
fig1_rows["status_display"] = fig1_rows["final_status"].map(STATUS_LABELS)
fig1_rows["sub_region_display"] = fig1_rows["sub_region"].map(REGION_LABELS)

u = fig1_rows.loc[fig1_rows["core_id"].eq("IODP-U1419")].copy()
assert len(u) == 3 and u["lat"].nunique() == 1 and u["lon"].nunique() == 1
u_site = u.iloc[[0]].copy()
u_site.loc[:, "segment"] = "seg1;seg2;seg3"
u_site.loc[:, "display_label"] = "IODP-U1419 (segments 1–3)"
u_site.loc[:, "final_status"] = "mixed_at_shared_site"
u_site.loc[:, "status_display"] = "class-assigned + no chronology"
u_site.loc[:, "protocol_conditional_precision_class"] = "seg1 Tier-1b; seg2 NA; seg3 Tier-1a"
fig1_sites = pd.concat([fig1_rows.loc[~fig1_rows["core_id"].eq("IODP-U1419")], u_site], ignore_index=True)
region_rank = {k: i for i, k in enumerate(REGION_LABELS)}
fig1_sites["region_rank"] = fig1_sites["sub_region"].map(region_rank)
fig1_sites = fig1_sites.sort_values(["region_rank", "core_id"], kind="stable").reset_index(drop=True)
fig1_sites["site_number"] = np.arange(1, len(fig1_sites) + 1)
fig1_sites["site_note"] = np.where(
    fig1_sites["core_id"].eq("IODP-U1419"),
    "Three segments share one site location; symbol overlays class-assigned and no-chronology states.",
    "",
)

fig1_source_cols = [
    "site_number", "core_id", "segment", "display_label", "lat", "lon", "lon_plot_0_360",
    "sub_region", "sub_region_display", "final_status", "status_display",
    "protocol_conditional_precision_class", "site_note",
]
write_csv(fig1_sites[fig1_source_cols], "FIG1_regional_coverage_source.csv")

legend_rows = []
for key, label in REGION_LABELS.items():
    legend_rows.append({"key_type": "sub-region", "key_value": key, "label": label,
                        "color": REGION_COLORS[key], "marker": "", "note": "Color encoding"})
for key, label in STATUS_LABELS.items():
    legend_rows.append({"key_type": "final status", "key_value": key, "label": label,
                        "color": "#333333", "marker": STATUS_MARKERS[key],
                        "note": "Shape encoding; precision classes are not quality grades"})
legend_rows.append({"key_type": "shared site", "key_value": "IODP-U1419",
                    "label": "class-assigned + no chronology", "color": REGION_COLORS["alaska_gulf"],
                    "marker": "circle with cross overlay", "note": "Three segments share one site location"})
write_csv(pd.DataFrame(legend_rows), "FIG1_regional_coverage_legend_key.csv")

fig = plt.figure(figsize=(7.15, 3.85))
gs = fig.add_gridspec(2, 2, width_ratios=[3.35, 1.30], height_ratios=[3.15, 1.20],
                      wspace=0.04, hspace=0.02)
ax = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree(central_longitude=180))
ax.set_extent([143, 230, 40, 65], crs=ccrs.PlateCarree())
ax.set_facecolor("#DCEAF3")
land = cfeature.NaturalEarthFeature("physical", "land", "50m", edgecolor="#6F6F6F", facecolor="#F3F1EA")
ax.add_feature(land, linewidth=0.4, zorder=1)
ax.coastlines("50m", color="#696969", linewidth=0.4, zorder=2)
ax.set_xticks([150, 180, 210], crs=ccrs.PlateCarree())
ax.set_yticks([40, 50, 60], crs=ccrs.PlateCarree())
ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=False, dateline_direction_label=False))
ax.yaxis.set_major_formatter(LatitudeFormatter())
gl = ax.gridlines(crs=ccrs.PlateCarree(), xlocs=FixedLocator([150, 180, 210]),
                  ylocs=FixedLocator([40, 50, 60]), color="white", linewidth=0.45, linestyle=":")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_anchor("N")
ax.plot([143, 230], [45, 45], transform=ccrs.PlateCarree(), color="#666666",
        lw=0.75, ls="--", zorder=3)
ax.text(147, 45.45, "southern boundary of the main study domain (45°N)",
        transform=ccrs.PlateCarree(), fontsize=7.2, color="#555555", zorder=4)

number_offsets = {
    1: (0.9, 0.45), 2: (1.15, 0.60), 3: (0.65, 0.55), 4: (1.15, 0.35), 5: (0.85, -0.70),
    6: (1.0, 0.55), 7: (1.0, 0.55), 8: (1.05, -0.55), 9: (1.15, 0.95), 10: (-1.65, 0.55),
    11: (-1.55, -0.65), 12: (0.8, 0.45), 13: (0.85, -0.45), 14: (0.75, 0.55),
    15: (0.8, -0.70), 16: (0.8, 0.55), 17: (-1.75, -0.20), 18: (1.15, 0.55), 19: (1.25, 0.55),
}

for _, r in fig1_sites.iterrows():
    color = REGION_COLORS[r["sub_region"]]
    if r["core_id"] == "IODP-U1419":
        ax.scatter(r["lon"], r["lat"], transform=ccrs.PlateCarree(), s=41, marker="o",
                   facecolor=color, edgecolor="#202020", linewidth=0.7, zorder=5)
        ax.scatter(r["lon"], r["lat"], transform=ccrs.PlateCarree(), s=29, marker="x",
                   color="#202020", linewidth=0.8, zorder=6)
    else:
        marker = STATUS_MARKERS[r["final_status"]]
        if marker == "x":
            ax.scatter(r["lon"], r["lat"], transform=ccrs.PlateCarree(), s=35, marker=marker,
                       color=color, linewidth=1.0, zorder=5)
        else:
            ax.scatter(r["lon"], r["lat"], transform=ccrs.PlateCarree(), s=38, marker=marker,
                       facecolor=color, edgecolor="#202020", linewidth=0.7, zorder=5)
    dx, dy = number_offsets[int(r["site_number"])]
    ax.annotate(str(int(r["site_number"])), xy=(r["lon"], r["lat"]),
                xytext=(r["lon"] + dx, r["lat"] + dy),
                xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),
                textcoords=ccrs.PlateCarree()._as_mpl_transform(ax),
                fontsize=7.2, fontweight="bold", color="#202020", zorder=7,
                arrowprops={"arrowstyle":"-","color":"#555555","lw":0.45,"shrinkA":1,"shrinkB":2})

key_ax = fig.add_subplot(gs[:, 1])
key_ax.axis("off")
key_ax.text(0, 0.995, "Site key", fontweight="bold", fontsize=8.0, va="top")
y = 0.955
for _, r in fig1_sites.iterrows():
    key_ax.text(0.00, y, f"{int(r['site_number']):02d}", fontweight="bold", fontsize=6.6, va="center")
    key_ax.text(0.13, y, r["display_label"], fontsize=6.6, va="center")
    y -= 0.0355
key_ax.text(0, 0.014, "U1419: three segments share one site;\ncircle + cross denotes mixed segment states.",
            fontsize=7.0, color="#444444", va="bottom")
key_ax.set_xlim(0, 1)
key_ax.set_ylim(0, 1)

legend_ax = fig.add_subplot(gs[1, 0])
legend_ax.axis("off")
legend_ax.set_xlim(0, 1)
legend_ax.set_ylim(0, 1)
legend_ax.text(0.00, 0.92, "Sub-region", fontweight="bold", fontsize=6.6, va="top")
yy = 0.72
for key, label in REGION_LABELS.items():
    legend_ax.scatter(0.02, yy, s=22, marker="s", color=REGION_COLORS[key], clip_on=False)
    legend_ax.text(0.055, yy, label, fontsize=5.1, va="center")
    yy -= 0.145
legend_ax.text(0.52, 0.92, "Final status", fontweight="bold", fontsize=6.6, va="top")
yy = 0.72
for key, label in STATUS_LABELS.items():
    marker = STATUS_MARKERS[key]
    if marker == "x":
        legend_ax.scatter(0.54, yy, s=23, marker=marker, color="#333333", linewidth=0.8, clip_on=False)
    else:
        legend_ax.scatter(0.54, yy, s=23, marker=marker, facecolor="white", edgecolor="#333333",
                          linewidth=0.7, clip_on=False)
    legend_ax.text(0.575, yy, label, fontsize=5.1, va="center")
    yy -= 0.145
fig.subplots_adjust(left=0.075, right=0.995, bottom=0.08, top=0.94)
save_all(fig, "FIG1_final")


# ---------------------------------------------------------------------------
# Figure 2 — temporal coverage and precision summary

order_pairs = [
    ("SO201-2-85KL", "full"), ("SO201-2-77KL", "full"), ("SO202-18-6", "full"),
    ("SO201-2-101KL", "full"), ("SO201-2-114KL", "full"), ("HLY02-02-17JPC", "full"),
    ("IODP-U1419", "seg1"), ("IODP-U1419", "seg2"), ("IODP-U1419", "seg3"),
    ("MD02-2489", "seg_59-278cm"), ("EW0408-85JC", "full"), ("EW0408-87JC", "r4_245-540cm"),
    ("ODP-887B", "full"), ("GGC-15", "full"), ("LV29-114-3", "full"),
    ("SO201-2-12KL", "full"), ("MD01-2416", "full"), ("RNDB-PC13", "full"),
    ("VINO19-GGC37", "full"),
]
order_df = pd.DataFrame(order_pairs, columns=["core_id", "segment"])
order_df["order"] = np.arange(1, len(order_df) + 1)
fig2 = order_df.merge(master, on=["core_id", "segment"], how="left", validate="one_to_one").sort_values("order")
assert fig2["sub_region"].notna().all()
assert len(fig2) == 19
assert not fig2["core_id"].isin(["GH02-1030", "KR02-15-PC6"]).any()
fig2["display_label"] = np.where(fig2["core_id"].eq("IODP-U1419"),
                                  "U1419 " + fig2["segment"].astype(str), fig2["core_id"])
fig2["sub_region_display"] = fig2["sub_region"].map(REGION_LABELS)
fig2["status_display"] = fig2["final_status"].map(STATUS_LABELS)
fig2["model_family"] = np.select(
    [fig2["final_status"].eq("legacy"), fig2["final_status"].eq("excluded_no_chronology"),
     fig2["sub_region"].eq("transition_zone"), fig2["cal_curve"].eq("Marine20_cc2")],
    ["legacy model", "no chronology", "transition-zone excluded", "unified Marine20 model"],
    default="other",
)
# Figure 2a reports the released model-endpoint posterior-median span.  The
# inventory age_top/bottom fields are retained in the master and crosswalk but
# are not used as a substitute for the age-table endpoints here.
fig2["inventory_age_top_cal_BP"] = fig2["age_top_cal_BP"]
fig2["inventory_age_bottom_cal_BP"] = fig2["age_bottom_cal_BP"]
fig2["model_endpoint_age_top_cal_BP"] = np.nan
fig2["model_endpoint_age_bottom_cal_BP"] = np.nan
fig2["model_endpoint_depth_top_cm"] = np.nan
fig2["model_endpoint_depth_bottom_cm"] = np.nan
for ix, r in fig2.iterrows():
    p = age_model_path(r["core_id"], r["segment"])
    if p.exists():
        am = pd.read_csv(p).sort_values("depth_cm")
        fig2.loc[ix, "model_endpoint_age_top_cal_BP"] = am.iloc[0]["posterior_age_median_calBP"]
        fig2.loc[ix, "model_endpoint_age_bottom_cal_BP"] = am.iloc[-1]["posterior_age_median_calBP"]
        fig2.loc[ix, "model_endpoint_depth_top_cm"] = am.iloc[0]["depth_cm"]
        fig2.loc[ix, "model_endpoint_depth_bottom_cm"] = am.iloc[-1]["depth_cm"]
write_csv(fig2[["order", "core_id", "segment", "display_label", "sub_region", "sub_region_display",
                "inventory_age_top_cal_BP", "inventory_age_bottom_cal_BP",
                "model_endpoint_depth_top_cm", "model_endpoint_depth_bottom_cm",
                "model_endpoint_age_top_cal_BP", "model_endpoint_age_bottom_cal_BP",
                "cal_curve", "model_family", "final_status",
                "status_display"]], "FIG2a_source.csv")

fig2b = fig2.copy()
assert fig2[["core_id", "segment"]].reset_index(drop=True).equals(
    fig2b[["core_id", "segment"]].reset_index(drop=True)
)
fig2b["precision_context"] = np.select(
    [fig2b["final_status"].isin(["legacy", "not_ranked_sparse_control"]),
     fig2b["final_status"].eq("excluded_no_chronology")],
    ["shown for numerical context only", "no chronology; no value"],
    default="continuous precision summary",
)
write_csv(fig2b[["order", "core_id", "segment", "display_label", "sub_region", "sub_region_display",
                 "posterior_CI_median_yr", "posterior_CI_max_yr", "protocol_conditional_precision_class",
                 "final_status", "status_display", "precision_context"]], "FIG2b_source.csv")


def row_bands(ax, groups: pd.Series, n: int) -> None:
    vals = groups.tolist()
    start = 0
    band_i = 0
    for i in range(1, n + 1):
        if i == n or vals[i] != vals[start]:
            end = i - 1 if i < n else i
            if band_i % 2 == 1:
                ax.axhspan(start - 0.5, end + 0.5, color="#F5F5F5", zorder=0)
            if end < n - 1:
                ax.axhline(end + 0.5, color="#B7B7B7", lw=0.45, zorder=1)
            start = i
            band_i += 1


def add_subregion_labels(ax, groups: pd.Series) -> None:
    vals = groups.tolist()
    start = 0
    for i in range(1, len(vals) + 1):
        if i == len(vals) or vals[i] != vals[start]:
            end = i - 1
            midpoint = (start + end) / 2
            ax.text(0.992, midpoint, REGION_LABELS[vals[start]],
                    transform=ax.get_yaxis_transform(), ha="right", va="center",
                    fontsize=5.0, color="#777777", style="italic", zorder=5,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 0.35})
            start = i


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.15, 7.65), gridspec_kw={"width_ratios": [1.55, 1.05]})
y1 = np.arange(len(fig2))
row_bands(ax1, fig2["sub_region"], len(fig2))
add_subregion_labels(ax1, fig2["sub_region"])
ax1.set_xlim(0, 46.5)
ax1.set_ylim(len(fig2) - 0.35, -0.65)
ax1.set_xticks(np.arange(0, 46, 5))
ax1.grid(axis="x", color="#E0E0E0", lw=0.45, ls=":", zorder=0)
ax1.set_yticks(y1, fig2["display_label"], fontsize=5.9)
ax1.tick_params(axis="y", length=0)
ax1.set_xlabel("Modelled posterior-median age span (ka BP)")
ax1.set_title("a   Modelled median-age span", loc="left", fontweight="bold", pad=17)

for i, (_, r) in enumerate(fig2.iterrows()):
    color = REGION_COLORS[r["sub_region"]]
    if pd.notna(r["model_endpoint_age_top_cal_BP"]) and pd.notna(r["model_endpoint_age_bottom_cal_BP"]):
        x1 = r["model_endpoint_age_top_cal_BP"] / 1000
        x2 = r["model_endpoint_age_bottom_cal_BP"] / 1000
        if r["final_status"] == "legacy":
            ls, lw, marker = "--", 2.1, "o"
            mfc = "white"
        elif r["sub_region"] == "transition_zone":
            ls, lw, marker = ":", 1.4, "D"
            mfc = "white"
        else:
            ls, lw, marker = "-", 2.6, "o"
            mfc = color
        ax1.plot([x1, x2], [i, i], color=color, lw=lw, ls=ls, solid_capstyle="round", zorder=2)
        ax1.plot([x1, x2], [i, i], ls="none", marker=marker, ms=3.3, mfc=mfc, mec=color, mew=0.65, zorder=3)
    else:
        ax1.plot([0.2, 0.85], [i, i], color="#888888", lw=0.8, ls=":")
        ax1.text(1.05, i, "no chronology", va="center", fontsize=5.4, color="#666666", style="italic")

ax1.text(0.0, 1.004, "Solid: unified Marine20  •  dashed: legacy",
         transform=ax1.transAxes, fontsize=5.0, color="#444444", va="bottom")

y2 = np.arange(len(fig2b))
row_bands(ax2, fig2b["sub_region"], len(fig2b))
ax2.axvspan(0.95, 1.05, color="#F2F2F2", zorder=0)
ax2.axvspan(1.45, 1.55, color="#EEEEEE", zorder=0)
for v in (0.95, 1.05, 1.45, 1.55):
    ax2.axvline(v, color="#C6C6C6", lw=0.45, ls=":", zorder=1)
ax2.set_xlim(0, 3.05)
ax2.set_ylim(len(fig2b) - 0.35, -0.65)
ax2.set_xticks(np.arange(0, 3.1, 0.5))
ax2.set_yticks(y2, fig2b["display_label"], fontsize=5.55)
ax2.tick_params(axis="y", length=0)
ax2.set_xlabel("Posterior median 95% CI width (kyr)")
ax2.set_title("b   Continuous precision summary", loc="left", fontweight="bold", pad=17)
ax2.text(0.0, 1.004, "Frozen bin boundaries shown for reference",
         transform=ax2.transAxes, fontsize=5.0, color="#444444", va="bottom")

for i, (_, r) in enumerate(fig2b.iterrows()):
    if pd.isna(r["posterior_CI_median_yr"]):
        continue
    x = r["posterior_CI_median_yr"] / 1000
    color = REGION_COLORS[r["sub_region"]]
    marker = STATUS_MARKERS[r["final_status"]]
    face = color if r["final_status"] == "precision_class_assigned" else "white"
    ax2.scatter(x, i, s=28, marker=marker, facecolor=face, edgecolor=color, linewidth=0.75, zorder=3)

context_handles = [
    Line2D([0], [0], marker="o", color="none", markerfacecolor="#666666", markeredgecolor="#444444",
           markersize=4.2, label="class-assigned"),
    Line2D([0], [0], marker="^", color="none", markerfacecolor="white", markeredgecolor="#444444",
           markersize=4.2, label="sparse-control*"),
    Line2D([0], [0], marker="s", color="none", markerfacecolor="white", markeredgecolor="#444444",
           markersize=4.2, label="legacy*"),
]
ax2.legend(handles=context_handles, loc="lower right", frameon=False, title="* numerical context only",
           title_fontsize=5.5, handletextpad=0.4, borderpad=0.1)
fig.subplots_adjust(left=0.205, right=0.99, bottom=0.075, top=0.955, wspace=0.56)
save_all(fig, "FIG2_final")


# ---------------------------------------------------------------------------
# Figure 3 — representative age-depth products

panel_specs = [
    ("A", "SO202-18-6", "full"),
    ("B", "MD01-2416", "full"),
    ("C", "LV29-114-3", "full"),
    ("D", "ODP-887B", "full"),
    ("E", "IODP-U1419", "seg3"),
    ("F", "HLY02-02-17JPC", "full"),
]


def joined_controls(core_id: str, segment: str) -> pd.DataFrame:
    cm = calmed.loc[(calmed["core_id"] == core_id) & (calmed["segment"] == segment)].copy()
    cl = clusters.loc[(clusters["core_id"] == core_id) & (clusters["segment"] == segment) &
                      (clusters["eligible_for_chronology"] == "yes")].copy()
    rr = rc.loc[(rc["core_id"] == core_id) & (rc["segment"] == segment) &
                (rc["admitted_to_model"] == "yes")].copy()
    assert len(cm) == len(cl)
    ctrl = cm.merge(cl[["cluster_id", "representative_depth_cm", "member_determinations", "member_lab_ids",
                        "calibration_role", "value_used_for_Theil_Sen_prior_centering"]],
                    left_on="depth_cm", right_on="representative_depth_cm", how="left", validate="one_to_one")

    def join_unique(s: pd.Series) -> str:
        vals = [str(v) for v in s.dropna().tolist()]
        return ";".join(dict.fromkeys(vals))

    ag = rr.groupby("dated_depth_cluster_id", dropna=False).agg(
        lab_ids=("lab_id", join_unique),
        age_14C_BP=("age_14C", lambda s: ";".join(format(float(v), ".15g") for v in s.dropna())),
        error_14C_1sigma_yr=("error_14C", lambda s: ";".join(format(float(v), ".15g") for v in s.dropna())),
        dated_material=("dated_material", join_unique),
        species=("species", join_unique),
    ).reset_index()
    ctrl = ctrl.merge(ag, left_on="cluster_id", right_on="dated_depth_cluster_id", how="left", validate="one_to_one")
    ctrl["control_note"] = (
        "Pre-calibrated calendar control median used by the frozen chronology workflow."
        if core_id == "IODP-U1419" and segment == "seg3"
        else "Existing calibrated cluster median; no new calibration or uncertainty calculation for this figure."
    )
    return ctrl


panel_models: dict[str, pd.DataFrame] = {}
panel_controls: dict[str, pd.DataFrame] = {}
manifest_rows = []

for panel, core_id, segment in panel_specs:
    am_path = age_model_path(core_id, segment)
    assert am_path.exists()
    am = pd.read_csv(am_path)
    ctrl = joined_controls(core_id, segment)
    assert len(am) == 201
    panel_models[panel] = am
    panel_controls[panel] = ctrl

    model_part = am.assign(
        row_type="age_model", calibrated_control_median_calBP=np.nan,
        dated_depth_cluster_id="", lab_ids="", age_14C_BP="", error_14C_1sigma_yr="",
        dated_material="", species="", control_note="",
    )
    control_part = pd.DataFrame({
        "core_id": core_id,
        "segment": segment,
        "depth_cm": ctrl["depth_cm"],
        "posterior_age_median_calBP": np.nan,
        "posterior_age_2.5pct_calBP": np.nan,
        "posterior_age_97.5pct_calBP": np.nan,
        "modelled_interval": "",
        "radiocarbon_bracketed_interval": "",
        "product_scope": "",
        "row_type": "admitted_control",
        "calibrated_control_median_calBP": ctrl["calibrated_median_cal_BP"],
        "dated_depth_cluster_id": ctrl["cluster_id"],
        "lab_ids": ctrl["lab_ids"],
        "age_14C_BP": ctrl["age_14C_BP"],
        "error_14C_1sigma_yr": ctrl["error_14C_1sigma_yr"],
        "dated_material": ctrl["dated_material"],
        "species": ctrl["species"],
        "control_note": ctrl["control_note"],
    })
    cols = ["row_type", "core_id", "segment", "depth_cm", "posterior_age_median_calBP",
            "posterior_age_2.5pct_calBP", "posterior_age_97.5pct_calBP", "modelled_interval",
            "radiocarbon_bracketed_interval", "product_scope", "calibrated_control_median_calBP",
            "dated_depth_cluster_id", "lab_ids", "age_14C_BP", "error_14C_1sigma_yr",
            "dated_material", "species", "control_note"]
    panel_source = pd.concat([model_part[cols], control_part[cols]], ignore_index=True)
    panel_source = panel_source.sort_values(["depth_cm", "row_type"], kind="stable")
    safe_core = re.sub(r"[^A-Za-z0-9-]+", "_", core_id)
    safe_seg = re.sub(r"[^A-Za-z0-9-]+", "_", segment)
    panel_file = f"FIG3_{panel}_{safe_core}_{safe_seg}_source.csv"
    write_csv(panel_source, panel_file)

    mm = master.loc[(master["core_id"] == core_id) & (master["segment"] == segment)].iloc[0]
    manifest_rows.append({
        "panel": panel, "core_id": core_id, "segment": segment,
        "final_status": mm["final_status"],
        "precision_class": mm["protocol_conditional_precision_class"],
        "sub_region": mm["sub_region"],
        "age_model_source": str(am_path),
        "admitted_control_source": str(RC_PATH),
        "cluster_source": str(CLUSTER_PATH),
        "calibrated_control_median_source": str(CALMED_PATH),
        "panel_source_file": panel_file,
        "age_model_rows": len(am),
        "admitted_control_clusters": len(ctrl),
        "dated_interval_top_cm": am["depth_cm"].min(),
        "dated_interval_bottom_cm": am["depth_cm"].max(),
        "control_uncertainty_display": "not plotted; no uniform frozen calibrated-control interval table available",
    })

fig3_manifest = pd.DataFrame(manifest_rows)
write_csv(fig3_manifest, "FIG3_source_manifest.csv")

fig, axes = plt.subplots(3, 2, figsize=(7.15, 9.25))
control_marker_checks = []
for ax, (panel, core_id, segment) in zip(axes.flat, panel_specs):
    am = panel_models[panel]
    ctrl = panel_controls[panel]
    mm = master.loc[(master["core_id"] == core_id) & (master["segment"] == segment)].iloc[0]
    color = REGION_COLORS[mm["sub_region"]]
    xlow = min(am["posterior_age_2.5pct_calBP"].min(), ctrl["calibrated_median_cal_BP"].min()) / 1000
    xhigh = max(am["posterior_age_97.5pct_calBP"].max(), ctrl["calibrated_median_cal_BP"].max()) / 1000
    xpad = 0.03 * (xhigh - xlow)

    ax.fill_betweenx(am["depth_cm"], am["posterior_age_2.5pct_calBP"] / 1000,
                     am["posterior_age_97.5pct_calBP"] / 1000, color=color, alpha=0.22, lw=0, zorder=1)
    ax.plot(am["posterior_age_median_calBP"] / 1000, am["depth_cm"], color="#222222", lw=1.15, zorder=2)
    marker_size = 11 if core_id == "IODP-U1419" and segment == "seg3" else 18
    control_artist = ax.scatter(ctrl["calibrated_median_cal_BP"] / 1000, ctrl["depth_cm"],
                                s=marker_size, marker="o", facecolor="white", edgecolor=color,
                                linewidth=0.75, zorder=3)

    top, bottom = am["depth_cm"].min(), am["depth_cm"].max()
    ypad = 0.03 * (bottom - top)
    ax.set_xlim(xlow - xpad, xhigh + xpad)
    ax.set_ylim(bottom + ypad, top - ypad)
    ax.grid(axis="x", color="#E7E7E7", lw=0.45, zorder=0)
    ax.set_xlabel("Calendar age (ka BP)")
    ax.set_ylabel("Depth (cm)")
    seg_text = f" {segment}" if segment != "full" else ""
    ax.set_title(f"{core_id}{seg_text}", loc="left", fontweight="bold", pad=5)
    ax.text(-0.10, 1.02, panel, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=8.2, fontweight="bold")
    if core_id == "IODP-U1419" and segment == "seg3":
        ax.text(0.98, 0.025, "pre-calibrated calendar inputs", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=5.6, color="#555555", style="italic")
    control_marker_checks.append((panel, ax, control_artist, marker_size))

legend_handles = [
    Line2D([0], [0], color="#222222", lw=1.15, label="posterior median"),
    Patch(facecolor="#8FB6CC", alpha=0.35, edgecolor="none", label="pointwise 95% interval"),
    Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor="#555555",
           markersize=4.2, label="admitted chronological control (calibrated median)"),
]
fig.legend(handles=legend_handles, loc="lower center", ncol=2, frameon=False,
           bbox_to_anchor=(0.5, 0.006), handlelength=1.6, columnspacing=1.2)
fig.subplots_adjust(left=0.10, right=0.985, bottom=0.115, top=0.975, hspace=0.34, wspace=0.24)
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
for panel, ax, artist, marker_size in control_marker_checks:
    bbox = ax.get_window_extent(renderer)
    xy_px = ax.transData.transform(artist.get_offsets())
    # Scatter s is marker area in points squared; use half the nominal diameter
    # plus the full edge linewidth as a conservative displayed half-extent.
    half_extent_px = (0.5 * np.sqrt(marker_size) + 0.75) * fig.dpi / 72
    assert np.all(xy_px[:, 0] - half_extent_px > bbox.x0), f"Panel {panel}: control clipped left"
    assert np.all(xy_px[:, 0] + half_extent_px < bbox.x1), f"Panel {panel}: control clipped right"
    assert np.all(xy_px[:, 1] - half_extent_px > bbox.y0), (
        f"Panel {panel}: control clipped bottom; min_clearance="
        f"{np.min(xy_px[:, 1] - half_extent_px - bbox.y0):.3f}px"
    )
    assert np.all(xy_px[:, 1] + half_extent_px < bbox.y1), (
        f"Panel {panel}: control clipped top; min_clearance="
        f"{np.min(bbox.y1 - xy_px[:, 1] - half_extent_px):.3f}px"
    )
save_all(fig, "FIG3_final")

print(f"Figure build complete: {OUT}")
