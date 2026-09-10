#!/usr/bin/env python3
import csv, json, hashlib, shutil, zipfile, os
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parents[2]
AUD=ROOT/'audit_2026-07'; WL=AUD/'worklist_2026-08-01'
FV=WL/'formal_baseline_rebuild_2026-08-12'; OUT=WL/'V1_FINAL_PRODUCT_BUILD_B_2026-08-12'
PKG=OUT/'PANGAEA_v1_release_candidate'
V4=ROOT/'master_inventory_v4.csv'; BRES=FV/'BASELINE_REBUILD_STAGE_GATE_MODEL_RESULTS.csv'; CFG=FV/'FORMAL_BASELINE_CONFIGURATION_AND_SEEDS_PREFLIGHT.csv'
RC=WL/'P6_P8_2026-08-10/P7_package_audit/radiocarbon_constraints_restructured.csv'
P4=FV/'P4_RUN_TO_RUN_REPRODUCIBILITY.csv'
TS=datetime.now(timezone.utc).isoformat()
def rd(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def wc(p,rows,fields=None):
 p.parent.mkdir(parents=True,exist_ok=True); fields=fields or list(rows[0])
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def yn(v):return 'yes' if v else 'no'
def clean(s):return str(s or '').strip()
if OUT.exists():raise RuntimeError('refuse overwrite '+str(OUT))
for d in [OUT,PKG/'classification',PKG/'radiocarbon',PKG/'clusters',PKG/'age_models',PKG/'201_point_diagnostics',PKG/'lipd',PKG/'metadata',PKG/'proxy_availability',PKG/'proxy_demonstration',PKG/'provenance',PKG/'audit/superseded_old_protocol'] :d.mkdir(parents=True,exist_ok=True)

v4=rd(V4); br=rd(BRES); cfg=rd(CFG); p4=rd(P4); rc=rd(RC)
B={(x['core_id'],x['segment']):x for x in br}; C={(x['core_id'],x['segment']):x for x in cfg}; P={x['core_id']:x for x in p4}
deprecated={'recommended_use','quality_tier','CI_is_data_dominated','posterior_CI_med','empirical_prior_only_CI_med','conditional_CI_contraction_ratio','prior_perturbation_CI_min','prior_perturbation_CI_max','prior_perturbation_span_ratio','acc_prior_posterior_overlap','acc_prior_posterior_overlap_usage','ESS','z','CI_median_yr','CI_max_yr','tier','tier_sub'}
base_keep=['core_id','segment','lat','lon','sub_region','water_depth_m','n_14C','n_dated_depth_clusters','age_top_cal_BP','age_bottom_cal_BP','deltaR_basis','deltaR_local_observation','deltaR_evidence_class','absolute_age_status','cal_curve','primary_ref','data_doi','model_available','chronology_input_valid','constraint_suitability_pass','constraint_suitability_note','control_density_gate','multi_species_planktic']
new_fields=base_keep+['posterior_CI_median_yr','posterior_CI_max_yr','protocol_conditional_precision_class','final_status','actual_acc_mean_yr_per_cm','acc_mean_derivation','acc_mean_derivation_provenance','eligible_cluster_count','thick_cm','thick_rule','thick_rule_empirically_validated','P1_selector_status','mem_mean','mem_strength','mem_strength_basis','delta_R_yr','delta_STD_yr','cc','stageB_status','actual_iterations_per_chain','max_Rhat','min_bulk_ESS','min_tail_ESS','dip_rejection_count_raw','dip_rejection_count_Holm','unimodality_test_status','structural_integrity_status','p4_tested','p4_realization_count','p4_max_abs_deviation_from_canonical_yr','p4_total_range_yr','run_to_run_variation_within_50yr','schema_version','record_release_status']
master=[]
for old in v4:
 k=(old['core_id'],old['segment']); o={f:old.get(f,'') for f in base_keep}; o.update({f:'' for f in new_fields if f not in o})
 o['schema_version']='ESSD_v1.0_master_inventory_v5';o['record_release_status']='live_scientific_release'
 if k in B:
  b=B[k];c=C[k];n=int(b['n_dated_depth_clusters']); ci=float(b['CI_median_yr'])
  o.update({'posterior_CI_median_yr':b['CI_median_yr'],'posterior_CI_max_yr':b['CI_max_yr'],'actual_acc_mean_yr_per_cm':c['theil_sen_acc_mean_yr_per_cm'],'acc_mean_derivation':'data_informed_theil_sen_prior_center','acc_mean_derivation_provenance':'Theil-Sen slope from eligible dated-depth clusters; FORMAL_BASELINE_CONFIGURATION_AND_SEEDS_PREFLIGHT.csv','eligible_cluster_count':n,'thick_cm':c['proposed_thick_cm'],'thick_rule':'R1_external_anchored_engineering_fallback','thick_rule_empirically_validated':'no','P1_selector_status':'closed_failed_selector','mem_mean':'0.5','mem_strength':'10','mem_strength_basis':'rbacon_documented_default_replacing_untraceable_inherited_setting','delta_R_yr':c['delta_R_yr'],'delta_STD_yr':c['delta_STD_yr'],'cc':c['cc'],'stageB_status':'no_preregistered_convergence_failure_detected','actual_iterations_per_chain':b['stopping_rung_per_chain'],'max_Rhat':b['max_Rhat'],'min_bulk_ESS':b['min_bulk_ESS'],'min_tail_ESS':b['min_tail_ESS'],'unimodality_test_status':'no_preregistered_unimodality_rejection_detected','structural_integrity_status':'pass'})
  rung=FV/'formal_recovery_runs'/(old['core_id']+'__'+old['segment'])/'rung_16000'; uni=rd(rung/'stageB_unimodality_by_depth.csv')
  o['dip_rejection_count_raw']=sum(float(x['raw_p_value'])<0.05 for x in uni);o['dip_rejection_count_Holm']=sum(x['reject_unimodality']=='TRUE' for x in uni)
  if old['core_id'] in P:
   q=P[old['core_id']];o.update({'p4_tested':'yes','p4_realization_count':'3','p4_max_abs_deviation_from_canonical_yr':q['max_abs_deviation_from_canonical_yr'],'p4_total_range_yr':q['range_CI_yr'],'run_to_run_variation_within_50yr':'yes' if q['run_to_run_variation_within_guard_halfwidth']=='TRUE' else 'no'})
  else:o.update({'p4_tested':'no','p4_realization_count':'','p4_max_abs_deviation_from_canonical_yr':'','p4_total_range_yr':'','run_to_run_variation_within_50yr':''})
  if old['model_status']=='legacy' or old['quality_tier']=='legacy':o['protocol_conditional_precision_class']='NA';o['final_status']='legacy'
  elif n<4:o['protocol_conditional_precision_class']='NA';o['final_status']='not_ranked_sparse_control'
  elif ci<950:o['protocol_conditional_precision_class']='Tier-1a';o['final_status']='precision_class_assigned'
  elif ci<=1050:o['protocol_conditional_precision_class']='1a-1b_intermediate';o['final_status']='precision_class_assigned'
  elif ci<1450:o['protocol_conditional_precision_class']='Tier-1b';o['final_status']='precision_class_assigned'
  elif ci<=1550:o['protocol_conditional_precision_class']='1b-2_intermediate';o['final_status']='precision_class_assigned'
  else:o['protocol_conditional_precision_class']='Tier-2';o['final_status']='precision_class_assigned'
 elif old['core_id']=='IODP-U1419' and old['segment']=='seg2':o['protocol_conditional_precision_class']='NA';o['final_status']='excluded_no_chronology';o['p4_tested']='no'
 else:o['protocol_conditional_precision_class']='NA';o['final_status']='excluded_transition_zone';o['p4_tested']='no'
 master.append(o)
candidate=OUT/'master_inventory_v5_candidate.csv';wc(candidate,master,new_fields)

# Count summaries, mechanically from v5 candidate.
main=[x for x in master if x['final_status']!='excluded_transition_zone']; allr=master
def summary(rows):
 c=Counter(x['final_status'] for x in rows); pc=Counter(x['protocol_conditional_precision_class'] for x in rows)
 labels=[('row_total',len(rows)),('Tier-1_total',pc['Tier-1a']+pc['Tier-1b']),('Tier-1a',pc['Tier-1a']),('Tier-1b',pc['Tier-1b']),('Tier-2',pc['Tier-2']),('1a-1b_intermediate',pc['1a-1b_intermediate']),('1b-2_intermediate',pc['1b-2_intermediate']),('not_ranked_sparse_control',c['not_ranked_sparse_control']),('legacy',c['legacy']),('not_ranked_model_adequacy',c['not_ranked_model_adequacy']),('excluded_no_chronology',c['excluded_no_chronology']),('excluded_transition_zone',c['excluded_transition_zone']),('excluded_total',c['excluded_no_chronology']+c['excluded_transition_zone'])]
 return [{'category':a,'count':b} for a,b in labels]
wc(OUT/'main_database_count_summary.csv',summary(main));wc(OUT/'all_adjudicated_count_summary.csv',summary(allr))

# Full radiocarbon table, unchanged values/rows, plus exact requested ordering.
rc_fields=['core_id','segment','lab_id','depth_cm','age_14C','error_14C','dated_material','species','constraint_role','admitted_to_model','exclusion_reason','audit_date','dated_depth_cluster_id','input_audit_status','source_ref','source_doi']
wc(PKG/'radiocarbon/radiocarbon_input_table_v1.csv',rc,rc_fields)

# Cluster table: one row per dated-depth cluster, including transition-zone model clusters, with members explicit.
groups=defaultdict(list)
for x in rc:
 if x['admitted_to_model']=='yes' and x['dated_depth_cluster_id']:groups[(x['core_id'],x['segment'],x['dated_depth_cluster_id'])].append(x)
clusters=[]
for (core,seg,cid),g in sorted(groups.items()):
 depths={float(x['depth_cm']) for x in g}; assert len(depths)==1
 clusters.append({'core_id':core,'segment':seg,'cluster_id':cid,'representative_depth_cm':next(iter(depths)),'member_determinations':len(g),'member_lab_ids':'|'.join(x['lab_id'] for x in g),'clustering_rule':'same reported dated depth grouped as one eligible independent dated-depth cluster','eligible_for_chronology':'yes','calibration_role':g[0]['constraint_role'],'value_used_for_Theil_Sen_prior_centering':'representative calibrated cluster median; see formal configuration derivation'})
wc(PKG/'clusters/dated_depth_cluster_table_v1.csv',clusters)

# Age and 201-point diagnostic products from canonical outputs only.
for k,b in B.items():
 core,seg=k; stem=core+'__'+seg; rung=FV/'formal_recovery_runs'/stem/'rung_16000'; ages=rd(rung/'age_model_201_depths.csv'); conv=rd(rung/'stageB_convergence_by_depth.csv'); uni=rd(rung/'stageB_unimodality_by_depth.csv'); assert len(ages)==len(conv)==len(uni)==201
 first=min(float(x['depth_cm']) for x in rc if x['core_id']==core and x['segment']==seg and x['admitted_to_model']=='yes'); last=max(float(x['depth_cm']) for x in rc if x['core_id']==core and x['segment']==seg and x['admitted_to_model']=='yes')
 ageout=[];diag=[]
 for a,c,u in zip(ages,conv,uni):
  d=float(a['depth_cm']); interval='radiocarbon_bracketed_interval' if first<=d<=last else 'derived_extrapolated_product'
  ageout.append({'core_id':core,'segment':seg,'depth_cm':a['depth_cm'],'posterior_age_median_calBP':a['median_cal_BP'],'posterior_age_2.5pct_calBP':a['ci_lower_95'],'posterior_age_97.5pct_calBP':a['ci_upper_95'],'modelled_interval':'yes','radiocarbon_bracketed_interval':'yes' if first<=d<=last else 'no','product_scope':interval})
  diag.append({'core_id':core,'segment':seg,'evaluation_depth_cm':a['depth_cm'],'posterior_median_age':a['median_cal_BP'],'lower_95':a['ci_lower_95'],'upper_95':a['ci_upper_95'],'CI_width':a['ci_width_95'],'Rhat':c['rhat'],'bulk_ESS':c['bulk_ESS'],'tail_ESS':c['tail_ESS'],'dip_statistic':u['dip_statistic'],'dip_raw_p':u['raw_p_value'],'dip_Holm_adjusted_p':u['holm_p_value'],'dip_rejection':u['reject_unimodality'],'structural_integrity':'pass'})
 wc(PKG/'age_models'/(stem+'.csv'),ageout);wc(PKG/'201_point_diagnostics'/(stem+'.csv'),diag)

# Classification history.
hist=[]
for seg,oldst,basis,newcl in [('seg1','not_ranked_model_adequacy','706.1 cm bimodality failure under superseded Stage B implementation','Tier-1b'),('seg3','not_ranked_model_adequacy','ESS=13 convergence failure under superseded terminal-Us diagnostic','Tier-1a')]:
 hist.append({'core':'IODP-U1419','segment':seg,'old_status':oldst,'old_diagnostic_basis':basis,'new_status':'precision_class_assigned/'+newcl,'new_protocol':'revised preregistered four-chain Stage B protocol','change_date':'2026-08-12','audit_reference':'BASELINE_REBUILD_STAGE_GATE_REPORT_2026-08-12.md','change_statement':'classification changed under revised preregistered Stage B protocol'})
wc(PKG/'provenance/SUPERSEDED_BASELINE_CLASSIFICATION_HISTORY.csv',hist)

# Fresh LiPD archives generated solely from v5 and current products (19 main rows).
for x in main:
 stem=x['core_id']+'__'+x['segment']; lp=PKG/'lipd'/(stem+'.lpd'); meta={'dataSetName':stem,'archiveType':'marine sediment','schemaVersion':'ESSD_v1.0','core_id':x['core_id'],'segment':x['segment'],'geo':{'latitude':x['lat'],'longitude':x['lon'],'waterDepth_m':x['water_depth_m'],'subRegion':x['sub_region']},'chronology':{'final_status':x['final_status'],'protocol_conditional_precision_class':x['protocol_conditional_precision_class'],'posterior_CI_median_yr':x['posterior_CI_median_yr'] or None,'delta_R_yr':x['delta_R_yr'] or None,'delta_STD_yr':x['delta_STD_yr'] or None,'cc':x['cc'] or None,'acc_mean':x['actual_acc_mean_yr_per_cm'] or None,'acc_mean_derivation':x['acc_mean_derivation'] or None,'thick_cm':x['thick_cm'] or None,'thick_rule':x['thick_rule'] or None,'mem_mean':x['mem_mean'] or None,'mem_strength':x['mem_strength'] or None,'stageB_status':x['stageB_status'] or None},'prohibitedFieldsAbsent':['recommended_use','CI_is_data_dominated']}
 with zipfile.ZipFile(lp,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('metadata.jsonld',json.dumps(meta,indent=2)+'\n')
  ap=PKG/'age_models'/(stem+'.csv');dp=PKG/'201_point_diagnostics'/(stem+'.csv')
  if ap.exists():z.write(ap,'tables/age_model.csv');z.write(dp,'tables/201_point_diagnostics.csv')

# Metadata/proxy copies (traceable source snapshots, not chronology calculations).
shutil.copy2(ROOT/'data_availability_table.csv',PKG/'proxy_availability/data_availability_table.csv')
s0=WL/'P6_P8_2026-08-10/P6_S0_release/S0_184_core_survey_release.csv';shutil.copy2(s0,PKG/'proxy_availability/S0_184_core_survey_release.csv')
proxy=AUD/'pangaea_submission_ready_baseline_final_2026-07-31/proxy_demonstration'
for p in proxy.iterdir():
 if p.is_file() and not p.name.startswith('._'):shutil.copy2(p,PKG/'proxy_demonstration'/p.name)

# Classification and final-validation evidence copies.
wc(PKG/'classification/master_inventory_v5_candidate.csv',master,new_fields)
for p in [OUT/'main_database_count_summary.csv',OUT/'all_adjudicated_count_summary.csv',FV/'P4_RUN_TO_RUN_REPRODUCIBILITY.csv',FV/'STAGEB_RESULT_INTERPRETATION_NOTE_2026-08-12.md'] :shutil.copy2(p,PKG/'classification'/p.name)
for p in [FV/'SUPERSEDED_OLD_PROTOCOL_SENSITIVITY_INVENTORY_2026-08-12.csv',FV/'OLD_PROTOCOL_SENSITIVITY_CLAIM_INVENTORY_2026-08-12.csv'] :shutil.copy2(p,PKG/'audit/superseded_old_protocol'/p.name)
(PKG/'audit/superseded_old_protocol/README.md').write_text('# Superseded old-protocol audit\n\nThese inventories are retained for provenance and are **not part of ESSD v1.0 scientific release results**. Their listed scientific products are excluded from the live release.\n')

# Dictionary (all live-master and product-specific fields).
defs={
'posterior_CI_median_yr':('Median width of the pointwise 95% posterior age interval across the dated interval','yr','number','primary continuous precision metric','Must not be interpreted as absolute age accuracy or universal reliability'),
'protocol_conditional_precision_class':('Categorical summary derived from posterior_CI_median_yr under frozen thresholds','1','string','derived categorical summary','Must not be interpreted as recommended use, reliability, or guaranteed event-resolution scale'),
'acc_mean_derivation':('Method used to center accumulation-rate prior','1','string','a deterministic, data-informed rule for centering the accumulation-rate prior','Not MCMC initialization or an uncertainty-weighted sedimentation estimate'),
'stageB_status':('Outcome of preregistered four-chain convergence monitoring','1','string','no preregistered convergence failure detected','Does not prove convergence'),
'unimodality_test_status':('Outcome of n=400 dip tests with within-model Holm correction','1','string','no preregistered unimodality rejection detected','Non-rejection does not prove unimodality')}
dictionary=[]
for f in new_fields:
 d=defs.get(f,(f.replace('_',' '),'see field name','string','release metadata or scientific value','Do not extend beyond README product boundaries'))
 dictionary.append({'table':'master_inventory_v5','field_name':f,'definition':d[0],'units':d[1],'type':d[2],'allowed_values':'see README/control vocabulary','source':'master v4 metadata and/or formal baseline/P4 products','derivation':d[3],'scientific_interpretation':d[3],'prohibited_interpretation':d[4],'nullable':'yes' if f not in ['core_id','segment','final_status'] else 'no','release_status':'live'})
extra=[('radiocarbon_input_table_v1','admitted_to_model','Whether this determination entered the formal model','1','string','yes|no'),('dated_depth_cluster_table_v1','cluster_id','Eligible independent dated-depth cluster identifier','1','string','unique within core/segment'),('age_models','product_scope','Whether value is bracketed or extrapolated','1','string','radiocarbon_bracketed_interval|derived_extrapolated_product'),('201_point_diagnostics','dip_Holm_adjusted_p','Within-model Holm-adjusted dip-test p-value','1','number','0..1')]
for t,f,d,u,ty,av in extra:dictionary.append({'table':t,'field_name':f,'definition':d,'units':u,'type':ty,'allowed_values':av,'source':'formal audit/baseline product','derivation':'direct or mechanically derived','scientific_interpretation':'traceability/reproducibility evidence','prohibited_interpretation':'Do not infer claims outside README boundaries','nullable':'no','release_status':'live'})
wc(PKG/'DATA_DICTIONARY_v1.csv',dictionary)

(PKG/'README.md').write_text('''# North Pacific chronology framework — ESSD v1.0 release candidate

This staging product provides traceable radiocarbon inputs; uniformly reconstructed Marine20/Bacon chronologies; frozen-model-protocol posterior age uncertainty; protocol-conditional precision classes; and full Stage A/B/C/D decision evidence.

The product does **not** claim absolute age accuracy, predictive calibration, data dominance, universal reliability, a guaranteed event-resolution scale, or correctness of deglacial ΔR.

`posterior_CI_median_yr` is the primary continuous product. `protocol_conditional_precision_class` is a derived convenience summary of that continuous metric. P1 did not empirically validate R1; `thick_rule=R1_external_anchored_engineering_fallback` is a software-default-anchored engineering fallback after the failed selector. Accumulation-rate prior centering is a deterministic, data-informed rule based on eligible dated-depth clusters.

Directories contain the 21-row master inventory; all 555 audited radiocarbon determinations (including excluded records); dated-depth clusters; 18 canonical age models; 18 complete 201-point diagnostics; 19 freshly generated LiPD archives; proxy availability and demonstration data; provenance; and checksums. This is a staging candidate and has not been uploaded or released.
''')

# Manuscript evidence packet, facts only.
mi=summary(main);ai=summary(allr); report=['# Manuscript v4 evidence packet','', '## Final counts','', 'See `main_database_count_summary.csv` (19 rows) and `all_adjudicated_count_summary.csv` (21 rows).','', '## Per-model final table','', '| Core/segment | Class | Status | CI median | CI max | n clusters | Stage B |','|---|---|---|---:|---:|---:|---|']
for x in master:report.append(f"| {x['core_id']} / {x['segment']} | {x['protocol_conditional_precision_class']} | {x['final_status']} | {x['posterior_CI_median_yr'] or 'NA'} | {x['posterior_CI_max_yr'] or 'NA'} | {x['n_dated_depth_clusters']} | {x['stageB_status'] or 'NA'} |")
report += ['','## Must-delete old claims','','- IODP-U1419 seg1 bimodality failure as a live classification basis.','- IODP-U1419 seg3 ESS=13, Bacon-unsuitable, or OxCal v1.1 re-treatment requirement.','- SO201-2-85KL as fixed Tier-2.','- Reliability grading or intended-use mappings.','- Old-protocol ΔR robustness, P1, or prior-sensitivity claims.','- “Initialization heuristic” terminology for acc.mean.','','## Final allowable claims','','- The main database contains 19 adjudicated rows and the all-record scope contains 21 rows.','- `posterior_CI_median_yr` is the primary continuous frozen-protocol precision metric.','- Precision classes are derived protocol-conditional summaries.','- No formal baseline model failed a preregistered Stage B adequacy criterion at the initial 16k/chain rung.','- P4 deviations for four prespecified records were within 50 yr; no inference is made for untested records.']
(OUT/'MANUSCRIPT_V4_EVIDENCE_PACKET_2026-08-12.md').write_text('\n'.join(report)+'\n')
print(json.dumps({'out':str(OUT),'candidate_rows':len(master),'radiocarbon_rows':len(rc),'misused_excluded':sum(x['input_audit_status']=='misused_input' and x['admitted_to_model']=='no' for x in rc),'clusters':len(clusters),'age_models':len(list((PKG/'age_models').glob('*.csv'))),'diagnostics':len(list((PKG/'201_point_diagnostics').glob('*.csv'))),'lipd':len(list((PKG/'lipd').glob('*.lpd')))},indent=2))
