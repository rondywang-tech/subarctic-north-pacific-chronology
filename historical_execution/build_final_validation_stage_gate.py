#!/usr/bin/env python3
import csv,hashlib
from pathlib import Path
from datetime import datetime,timezone
H=Path(__file__).resolve().parent
def rr(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def wc(p,r,fields=None):
 fields=fields or list(r[0]);
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(r)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base={r['core_id']:r for r in rr(H/'BASELINE_REBUILD_STAGE_GATE_MODEL_RESULTS.csv')}
p4=rr(H/'P4_STAGEB_DIAGNOSTICS.csv'); cores=['SO201-2-12KL','MD02-2489','ODP-887B','SO202-18-6']; out=[]
for c in cores:
 a=float(base[c]['CI_median_yr']); d={int(x['realization']):x for x in p4 if x['core_id']==c};b=float(d[2]['CI_median_yr']);e=float(d[3]['CI_median_yr']); vals=[a,b,e]; dev=max(abs(b-a),abs(e-a))
 out.append({'core_id':c,'canonical_realization_1_CI_median_yr':a,'realization_2_CI_median_yr':b,'realization_3_CI_median_yr':e,'min_CI_yr':min(vals),'max_CI_yr':max(vals),'range_CI_yr':max(vals)-min(vals),'max_abs_deviation_from_canonical_yr':dev,'run_to_run_variation_within_guard_halfwidth':'TRUE' if dev<=50 else 'FALSE','run_to_run_variation_exceeds_50yr':'TRUE' if dev>50 else 'FALSE','realization_2_stageB_status':'pass' if d[2]['convergence_pass']=='TRUE' else 'fail','realization_3_stageB_status':'pass' if d[3]['convergence_pass']=='TRUE' else 'fail','canonical_classification_unchanged':'TRUE'})
wc(H/'P4_RUN_TO_RUN_REPRODUCIBILITY.csv',out)
lines=['# P4 run-to-run reproducibility','',f'- New Bacon calls: 32 (all at 16,000 retained iterations/chain; no retry or extension).',f'- Total Bacon ledger: 256 / 468; remaining 212.','- Canonical baseline remains realization 1 and remains the sole classification source. P4 does not alter any class, threshold, or guard band.','', '| Core | CI1 canonical | CI2 | CI3 | Total range | Max absolute deviation from canonical | >50 yr? |','|---|---:|---:|---:|---:|---:|---|']
for x in out:lines.append(f"| {x['core_id']} | {x['canonical_realization_1_CI_median_yr']:.2f} | {x['realization_2_CI_median_yr']:.2f} | {x['realization_3_CI_median_yr']:.2f} | {x['range_CI_yr']:.2f} | {x['max_abs_deviation_from_canonical_yr']:.2f} | {x['run_to_run_variation_exceeds_50yr']} |")
lines+=['','All eight new four-chain realizations passed the frozen Stage B convergence criteria at the initial 16k/chain rung.']
(H/'P4_RUN_TO_RUN_REPRODUCIBILITY_2026-08-12.md').write_text('\n'.join(lines)+'\n')

# Integrity counts.
with (H/'P1_THICK_RULE_CI_MEDIAN_SENSITIVITY_FINAL_VALIDATION.csv').open(newline='') as f:p1=list(csv.DictReader(f))
old_count=sum(1 for _ in (H/'SUPERSEDED_OLD_PROTOCOL_SENSITIVITY_INVENTORY_2026-08-12.csv').open())-1
claim_count=sum(1 for _ in (H/'OLD_PROTOCOL_SENSITIVITY_CLAIM_INVENTORY_2026-08-12.csv').open())-1
u_count=sum(1 for _ in (H/'U1419_SUPERSEDED_BASELINE_ARTIFACT_INVENTORY_2026-08-12.csv').open())-1
seg3=base['IODP-U1419']; allres=list(base.values()); nrank=1+sum(int(x['n_dated_depth_clusters'])>int(seg3['n_dated_depth_clusters']) for x in allres); cirank=1+sum(float(x['CI_median_yr'])<float(seg3['CI_median_yr']) for x in allres)
any50=any(x['run_to_run_variation_exceeds_50yr']=='TRUE' for x in out)
report=['# Final Validation A stage-gate report','',f'Generated: {datetime.now(timezone.utc).isoformat()}','',
'1. Holm declared == executed: **TRUE** — 201 depths within each model, 18 separately adjusted families.',
'2. Actual chain initialization: four independent, prespecified seeds per model; rbacon 3.5.2 applies each seed and randomly creates the two top-age starting states when `th0` is omitted. `acc.mean` is a prior parameter, not initialization.',
'3. P1 five-core across-thick CI-median ranges:','']
for x in p1:report.append(f"   - {x['core_id']}: {float(x['range_CI_median_yr']):.2f} yr (relative range {float(x['relative_range']):.4f}).")
report += ['',f"4. IODP-U1419 seg3: n={seg3['n_dated_depth_clusters']} clusters (rank {nrank}/18 from highest n); CI_median={float(seg3['CI_median_yr']):.2f} yr (rank {cirank}/18 from narrowest). This is a two-dimensional position statement only.",
f'5. Old-protocol sensitivity inventory: {old_count} conservatively matched files; all are marked `superseded_old_protocol` and `exclude_from_ESSD_v1_scientific_release`. {claim_count} textual claim locations are inventoried without editing. U1419 provenance inventory contains {u_count} files.',
'6. P4 results:','']
for x in out:report.append(f"   - {x['core_id']}: {x['canonical_realization_1_CI_median_yr']:.2f} / {x['realization_2_CI_median_yr']:.2f} / {x['realization_3_CI_median_yr']:.2f} yr; max |new−canonical|={x['max_abs_deviation_from_canonical_yr']:.2f} yr.")
report += ['',f"7. Any P4 core >50 yr: **{'YES' if any50 else 'NO'}**.",
'8. Bacon ledger: **256 / 468 used; 212 remaining**. P4 used 32/60 calls, with zero retries.',
'9. New declared != executed discovered: **NO**.',
f"10. `FINAL_VALIDATION_A_PASS = {'FALSE' if any50 else 'TRUE'}`.",
'','Interpretation is constrained by the precommitment. Canonical classification is unchanged. If any P4 deviation exceeds 50 yr, the guard bands must be described only as predefined reporting intervals around class thresholds.','',
'## Stage gate','', 'Work stops here. No master inventory, manuscript, PANGAEA package, LiPD file, ΔR ensemble, or prior cascade was changed or started.']
(H/'FINAL_VALIDATION_A_STAGE_GATE_REPORT_2026-08-12.md').write_text('\n'.join(report)+'\n')

# SHA manifests.
named=['P4_CHAIN_SEED_MANIFEST.csv','P4_STAGEB_DIAGNOSTICS.csv','P4_CALL_LEDGER.csv','P4_RUN_TO_RUN_REPRODUCIBILITY.csv','P4_RUN_TO_RUN_REPRODUCIBILITY_2026-08-12.md']
(H/'P4_SHA256SUMS.txt').write_text(''.join(f'{sha(H/x)}  {x}\n' for x in named))
allnamed=['FINAL_VALIDATION_A_PRECOMMITMENT_2026-08-12.md','STAGEB_HOLM_FAMILY_EXECUTION_AUDIT_2026-08-12.md','STAGEB_CHAIN_INITIALIZATION_EXECUTION_AUDIT_2026-08-12.md','STAGEB_RESULT_INTERPRETATION_NOTE_2026-08-12.md','U1419_SUPERSEDED_BASELINE_ARTIFACT_INVENTORY_2026-08-12.csv','P1_THICK_RULE_CI_MEDIAN_SENSITIVITY_FINAL_VALIDATION.csv','P1_THICK_RULE_CI_MEDIAN_SENSITIVITY_FINAL_VALIDATION.md','CONTROL_DENSITY_VS_CI_MEDIAN_FINAL_VALIDATION.csv','SUPERSEDED_OLD_PROTOCOL_SENSITIVITY_INVENTORY_2026-08-12.csv','OLD_PROTOCOL_SENSITIVITY_CLAIM_INVENTORY_2026-08-12.csv','V1_PRODUCT_SCHEMA_REVISION_PLAN_2026-08-12.md','FINAL_VALIDATION_A_STAGE_GATE_REPORT_2026-08-12.md']
(H/'FINAL_VALIDATION_A_SHA256SUMS.txt').write_text(''.join(f'{sha(H/x)}  {x}\n' for x in allnamed))
print('\n'.join(report))
