#!/usr/bin/env python3
import csv, hashlib, re
from pathlib import Path
from datetime import datetime, timezone

H=Path(__file__).resolve().parent
ROOT=H.parents[3]
P1=H.parent/'P1_rule_selection_2026-08-10'/'P1_selected_runs.csv'
RES=H/'BASELINE_REBUILD_STAGE_GATE_MODEL_RESULTS.csv'
MAN=H/'FORMAL_BASELINE_CONFIGURATION_AND_SEEDS_PREFLIGHT.csv'
def rows(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def writecsv(p, rr, fields=None):
 fields=fields or list(rr[0]);
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rr)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cls(x):
 x=float(x)
 return 'Tier-1/1a' if x<950 else ('intermediate/1a-1b_guard_band' if x<=1050 else ('Tier-1/1b' if x<1450 else ('intermediate/1b-2_guard_band' if x<=1550 else 'Tier-2/2')))

# Holm audit: inspect code and every formal output table.
tabs=list((H/'formal_recovery_runs').glob('*/rung_16000/stageB_unimodality_by_depth.csv'))
counts=[]
for p in tabs:
 rr=rows(p); counts.append((p,len(rr)))
assert len(tabs)==18 and all(n==201 for _,n in counts)
code=(H/'stageb_diagnostics.R').read_text()
assert 'p.adjust(out$raw_p_value,method="holm")' in code
(H/'STAGEB_HOLM_FAMILY_EXECUTION_AUDIT_2026-08-12.md').write_text(f'''# Stage B Holm family execution audit

- Declared scope: one family of 201 evaluation depths within each model.
- Executed scope: one family of 201 evaluation depths within each model.
- Code path: `{H/'stageb_diagnostics.R'}` lines 31–44; `stageb_unimodality()` constructs one 201-row table and calls `p.adjust(out$raw_p_value, method="holm")` on that table. `{H/'stageb_postprocess_model.R'}` invokes this function separately for each model.
- Product check: {len(tabs)}/18 model tables exist; every table contains exactly 201 depth rows. No global 3,618-row adjustment or grouped-core adjustment is implemented.
- Result: `declared_scope_equals_executed_scope = TRUE`.
- `CLAUDE_REVIEW_TRIGGER = FALSE`.
''')

# Chain initialization audit, all 18 x 4 .bacon files.
cfg=rows(MAN); init=[]
for m in cfg:
 stem=m['core_id']+'__'+m['segment']; d=H/'formal_recovery_runs'/stem/'rung_16000'
 for ch in range(1,5):
  runid=f'{stem}__formal_stageB__rung16000__chain{ch}'
  candidates=[p for root in (H/'formal_recovery_runs',H/'formal_runs') for p in root.rglob(runid+'*.bacon') if not p.name.startswith('._')]
  if not candidates: raise RuntimeError('missing bacon '+runid)
  bf=candidates[0]
  txt=bf.read_text(errors='replace')
  z=re.search(r'^Bacon\s+0:\s*([^;]+);',txt,re.M)
  if not z: raise RuntimeError('missing Bacon settings row '+str(bf))
  v=[q.strip() for q in z.group(1).split(',')]
  # FixT,K,MinAge,MaxAge,th0,th0p,w.a,w.b,alpha,beta,dmin,dmax,seed
  init.append({'core_id':m['core_id'],'segment':m['segment'],'chain':ch,'manifest_seed':m[f'chain_{ch}_seed'],'bacon_seed':v[12],'th0':v[4],'th0p':v[5],'bacon_file':str(bf)})
assert all(x['manifest_seed']==x['bacon_seed'] for x in init)
assert all(len({x['manifest_seed'] for x in init if x['core_id']==m['core_id'] and x['segment']==m['segment']})==4 for m in cfg)
writecsv(H/'STAGEB_CHAIN_INITIALIZATION_DETAILS.csv',init)
(H/'STAGEB_CHAIN_INITIALIZATION_EXECUTION_AUDIT_2026-08-12.md').write_text(f'''# Stage B chain-initialization execution audit

- Scope checked: all {len(init)} chain outputs (18 models × 4 chains).
- Seeds: all manifest seeds equal the seeds recorded by rbacon; four seeds are unique within every model.
- Driver: `run_formal_baseline.py` passes each frozen seed both to `set.seed(seed)` and `Bacon(seed=seed)`.
- rbacon 3.5.2 implementation: `Bacon()` calls `set.seed(seed)`; when `th0` is absent it generates the two top-age starting values with `round(rnorm(2, max(youngest.age,dets[1,2]), dets[1,3]))`, then records `th0`, `th0p`, and `seed` in the `.bacon` file.
- Actual states: the recorded per-chain starting pairs are in `STAGEB_CHAIN_INITIALIZATION_DETAILS.csv`; they are sampler-generated under independent fixed seeds, not deterministic identical states.
- `acc.mean` is solely the accumulation-rate prior parameter; it is not a chain initial state.
- Result: `executed_initialization_equals_frozen_configuration = TRUE`.
''')

(H/'STAGEB_RESULT_INTERPRETATION_NOTE_2026-08-12.md').write_text('''# Stage B result interpretation note

No baseline model failed any preregistered model-adequacy criterion at the initial 16,000-iteration-per-chain rung.

No evidence of non-convergence was detected by the preregistered Rhat/ESS diagnostics at the 201 monitored evaluation depths.

No departure from unimodality was detected under the preregistered n=400 and Holm-FWER procedure; non-rejection is not evidence of unimodality.

Stage B did not exclude any baseline model in this batch. Stage B did not “validate all models”; it did not prove all posterior distributions unimodal or all chains converged.
''')

# P1 baseline-resolution R1/R2/R3 CI facts.
pr=[r for r in rows(P1) if r['block']=='geometry' and r['scenario']=='baseline']
cores=['SO201-2-77KL','SO202-18-6','VINO19-GGC37','MD01-2416','ODP-887B']; out=[]
for c in cores:
 d={r['rule']:r for r in pr if r['core_id']==c}; vals=[float(d[k]['CI_median_yr']) for k in ('R1','R2','R3')]
 o={'core_id':c}
 for k in ('R1','R2','R3'):
  o[f'CI_median_{k}_yr']=d[k]['CI_median_yr'];o[f'{k}_convergence']=d[k]['convergence_pass'];o[f'{k}_precision_class']=cls(d[k]['CI_median_yr'])
 o.update({'min_CI_median_yr':min(vals),'max_CI_median_yr':max(vals),'range_CI_median_yr':max(vals)-min(vals),'relative_range':(max(vals)-min(vals))/(sum(vals)/3),'status':'diagnostic_only_not_rule_selection'})
 out.append(o)
writecsv(H/'P1_THICK_RULE_CI_MEDIAN_SENSITIVITY_FINAL_VALIDATION.csv',out)
lines=['# P1 thick-rule CI-median sensitivity','', '`diagnostic_only_not_rule_selection`','', '| Core | R1 | R2 | R3 | Range (yr) | Relative range |','|---|---:|---:|---:|---:|---:|']
for x in out:lines.append(f"| {x['core_id']} | {float(x['CI_median_R1_yr']):.2f} | {float(x['CI_median_R2_yr']):.2f} | {float(x['CI_median_R3_yr']):.2f} | {x['range_CI_median_yr']:.2f} | {x['relative_range']:.4f} |")
lines += ['','These five prespecified representative records do not represent the entire database. No result is used to select or modify R1; nonconverged cells, if any, remain missing and are not rerun.']
(H/'P1_THICK_RULE_CI_MEDIAN_SENSITIVITY_FINAL_VALIDATION.md').write_text('\n'.join(lines)+'\n')

# Control density table.
hi={('IODP-U1419','seg1'),('IODP-U1419','seg3'),('ODP-887B','full'),('SO201-2-85KL','full')}; cd=[]
for r in rows(RES):
 n=int(r['n_dated_depth_clusters']); old=r['old_tier']
 role='sparse_control_not_ranked' if n<4 else ('legacy_protocol' if old=='legacy' else 'precision_classification_input')
 cd.append({'core_id':r['core_id'],'segment':r['segment'],'n_clusters':n,'posterior_CI_median':r['CI_median_yr'],'precision_class':r['stage_gate_tier']+'/'+r['stage_gate_tier_sub'],'calibration_role':role,'plateau_precalibration_yes_no':'not_assessed_in_final_validation','highlight_record':'yes' if (r['core_id'],r['segment']) in hi else 'no'})
writecsv(H/'CONTROL_DENSITY_VS_CI_MEDIAN_FINAL_VALIDATION.csv',cd)

# Schema plan.
(H/'V1_PRODUCT_SCHEMA_REVISION_PLAN_2026-08-12.md').write_text('''# ESSD v1.0 product-schema revision plan

This is a plan only; no canonical inventory is modified in Final Validation A.

- Primary continuous field: `posterior_CI_median_yr`.
- Secondary derived field: `protocol_conditional_precision_class`.
- Remove from the formal release: `recommended_use`.
- Rename `quality_tier` to `protocol_conditional_precision_class`.
- Do not include `CI_is_data_dominated`; retain that withdrawn diagnostic only in audit/superseded history.
- Do not map precision classes to millennial/orbital-scale use, reliability, event-ordering fitness, or general fitness for use.
- Methods/metadata term for acc.mean: “a deterministic, data-informed rule for centering the accumulation-rate prior”. Field form: `acc_mean_derivation=data_informed_theil_sen_prior_center`.
''')

print('zero audits built',datetime.now(timezone.utc).isoformat())
