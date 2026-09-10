#!/usr/bin/env python3
import csv, json, math
from pathlib import Path

ROOT = Path("/Volumes/UH100/paleo_data/np_terrigenous_db")
HERE = ROOT / "audit_2026-07/worklist_2026-08-01/P1_rule_selection_2026-08-10"
MANIFEST = ROOT / "audit_2026-07/worklist_2026-08-01/C1n_baseline_rebuild_2026-08-09/run_manifest_all20.json"
REPS = {"SO201-2-77KL", "SO202-18-6", "VINO19-GGC37", "MD01-2416", "ODP-887B"}
DBY = 0.5

def actual_k(depth_range, thick):
    # rbacon 3.5.2: length(seq(floor(d.min), ceiling(d.max), by=thick)).
    return math.floor(depth_range/thick + 1e-12) + 1

def target_thick(depth_range, k):
    # K=floor(D/thick)+1, so D/K < thick <= D/(K-1).
    lo=max(DBY,depth_range/k); hi=depth_range/(k-1)
    if not hi>lo: raise ValueError((depth_range,k,lo,hi))
    return (lo+hi)/2

models = [m for m in json.loads(MANIFEST.read_text())["models"] if m["core_id"] in REPS]
rows=[]
for m in models:
    span=float(m["dated_span_cm"]); n=int(m["n_dated_depth_clusters"])
    depth_range=math.ceil(float(m['d_max_cm']))-math.floor(float(m['d_min_cm']))
    rules={"R1":max(span/200,min(5,span/10)),"R2":span/(4*n),"R3":span/50}
    for rule,base in rules.items():
        base_k=actual_k(depth_range,base)
        k_hi=min(200,math.ceil(depth_range/DBY-1e-12))
        for scenario,k in (("coarse_K_endpoint",10),("baseline",base_k),("fine_K_endpoint",k_hi)):
            thick=base if scenario=="baseline" else target_thick(depth_range,k)
            rows.append(dict(core_id=m["core_id"],rule=rule,scenario=scenario,span_cm=span,
                bacon_elbow_depth_range_cm=depth_range,n_clusters=n,d_by_cm=DBY,target_actual_K=k,planned_thick_cm=thick,
                achieved_thick_multiplier_vs_baseline=thick/base,
                planned_actual_K_check=actual_k(depth_range,thick),
                actual_K="PENDING_RUN",actual_multiplier="PENDING_RUN",
                direction_measurable="yes" if k!=base_k or scenario=="baseline" else "no_baseline_at_endpoint"))
with (HERE/"P1_K_endpoint_design.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(f"rows={len(rows)} unique_cells={len(rows)} one_sided={sum(r['direction_measurable']=='no_baseline_at_endpoint' for r in rows)}")
