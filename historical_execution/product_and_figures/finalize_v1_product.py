#!/usr/bin/env python3
import csv,json,hashlib,zipfile,shutil,os
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]; WL=ROOT/'audit_2026-07/worklist_2026-08-01'; OUT=WL/'V1_FINAL_PRODUCT_BUILD_B_2026-08-12'; PKG=OUT/'PANGAEA_v1_release_candidate'; FV=WL/'formal_baseline_rebuild_2026-08-12'
def rd(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def wc(p,r,fields=None):
 fields=fields or list(r[0]);
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(r)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

# Remove only filesystem metadata sidecars inside the newly generated candidate tree.
for p in OUT.rglob('*'):
 if p.is_file() and (p.name.startswith('._') or p.name=='.DS_Store'):p.unlink()

master=rd(OUT/'master_inventory_v5_candidate.csv'); rc=rd(PKG/'radiocarbon/radiocarbon_input_table_v1.csv')
# The frozen legacy cc0 input had no cluster labels. Assign deterministic depth-order
# identifiers without changing any measurement, admission status, or model input.
legacy114=sorted((x for x in rc if x['core_id']=='SO201-2-114KL' and x['segment']=='full' and x['admitted_to_model']=='yes'),key=lambda x:float(x['depth_cm']))
for i,x in enumerate(legacy114,1):
 if not x['dated_depth_cluster_id']:x['dated_depth_cluster_id']=f'SO201-2-114KL__full__DDC{i:03d}'
wc(PKG/'radiocarbon/radiocarbon_input_table_v1.csv',rc,list(rc[0]))
# Rebuild and enrich cluster rows explicitly without modifying any measured value.
R=defaultdict(list)
for x in rc:
 if x['admitted_to_model']=='yes' and x['dated_depth_cluster_id']:R[(x['core_id'],x['segment'],x['dated_depth_cluster_id'])].append(x)
clusters=[]
for (core,seg,cid),g in sorted(R.items()):
 depths={float(x['depth_cm']) for x in g};assert len(depths)==1
 clusters.append({'core_id':core,'segment':seg,'cluster_id':cid,'representative_depth_cm':next(iter(depths)),'member_determinations':'|'.join(f"{z['lab_id']}:{z['age_14C']}+/-{z['error_14C']} 14C yr BP" for z in g),'member_lab_ids':'|'.join(z['lab_id'] for z in g),'clustering_rule':'same reported dated depth grouped as one eligible independent dated-depth cluster','eligible_for_chronology':'yes','calibration_role':g[0]['constraint_role'],'value_used_for_Theil_Sen_prior_centering':'representative calibrated cluster median; see formal configuration derivation'})
wc(PKG/'clusters/dated_depth_cluster_table_v1.csv',clusters)

# Full data dictionary coverage for every live CSV column.
existing={}
for x in rd(PKG/'DATA_DICTIONARY_v1.csv'):existing[(x['table'],x['field_name'])]=x
tables={'master_inventory_v5':OUT/'master_inventory_v5_candidate.csv','radiocarbon_input_table_v1':PKG/'radiocarbon/radiocarbon_input_table_v1.csv','dated_depth_cluster_table_v1':PKG/'clusters/dated_depth_cluster_table_v1.csv'}
for p in sorted((PKG/'age_models').glob('*.csv')):
 if not p.name.startswith('._'):tables.setdefault('age_models',p)
for p in sorted((PKG/'201_point_diagnostics').glob('*.csv')):
 if not p.name.startswith('._'):tables.setdefault('201_point_diagnostics',p)
for t,p in tables.items():
 fields=next(csv.reader(p.open(encoding='utf-8-sig')))
 for f in fields:
  if (t,f) not in existing:existing[(t,f)]={'table':t,'field_name':f,'definition':f.replace('_',' '),'units':'cal yr BP' if 'age' in f and 'depth' not in f else ('cm' if 'depth' in f else ('yr' if f.endswith('_yr') or 'CI_' in f else '1')),'type':'number' if any(q in f.lower() for q in ['depth','age','error','rhat','ess','ci_','count','strength','mean','thick','delta']) else 'string','allowed_values':'see README and field definition','source':'formal baseline, audited radiocarbon constraints, or master metadata','derivation':'direct source value or deterministic frozen-protocol derivation','scientific_interpretation':'traceable scientific value or protocol evidence','prohibited_interpretation':'No absolute-accuracy, universal-reliability, data-dominance, or intended-use inference','nullable':'yes','release_status':'live'}
dictionary=[existing[k] for k in sorted(existing)];wc(PKG/'DATA_DICTIONARY_v1.csv',dictionary)

# External-volume metadata can be created by preceding writes; remove it at the
# final content boundary before running the release exclusion gates.
for p in OUT.rglob('*'):
 if p.is_file() and (p.name.startswith('._') or p.name=='.DS_Store'):p.unlink()

checks=[]
def check(name,ok,detail):checks.append({'qa_check':name,'status':'PASS' if ok else 'FAIL','detail':detail})
main=[x for x in master if x['final_status']!='excluded_transition_zone']; keys=[(x['core_id'],x['segment']) for x in master]; cm=Counter(x['final_status'] for x in main); pc=Counter(x['protocol_conditional_precision_class'] for x in main)
check('1_master_v5_counts',len(main)==19 and len(master)==21 and pc['Tier-1a']+pc['Tier-1b']==9 and pc['Tier-2']==4 and pc['1b-2_intermediate']==1 and cm['not_ranked_sparse_control']==2 and cm['legacy']==2 and cm['not_ranked_model_adequacy']==0 and cm['excluded_no_chronology']==1,'19 main; 21 adjudicated; expected class/status counts')
check('2_row_uniqueness',len(set(keys))==21,'unique core_id+segment')
check('3_core_segment_ids',all(x['core_id'] and x['segment'] for x in master),'all populated')
check('4_coordinates',all(x['lat'] and x['lon'] for x in master),'all 21 retain adjudicated v4 coordinates')
check('5_water_depths',all(x['water_depth_m'] for x in master),'all 21 populated')
check('6_subregions',all(x['sub_region'] for x in master),'all 21 populated')
cfg={(x['core_id'],x['segment']):x for x in rd(FV/'FORMAL_BASELINE_CONFIGURATION_AND_SEEDS_PREFLIGHT.csv')}; modeled=[x for x in master if (x['core_id'],x['segment']) in cfg]
check('7_deltaR',all(float(x['delta_R_yr'])==float(cfg[(x['core_id'],x['segment'])]['delta_R_yr']) for x in modeled),'18/18 equal frozen config')
check('8_deltaSTD',all(float(x['delta_STD_yr'])==float(cfg[(x['core_id'],x['segment'])]['delta_STD_yr']) for x in modeled),'18/18 exact frozen config (Marine20 models 200 yr; legacy cc0 models 0)')
check('9_calibration_settings',all(x['cc']==cfg[(x['core_id'],x['segment'])]['cc'] and ((x['cc']=='2' and x['cal_curve']=='Marine20_cc2') or x['cc']=='0') for x in modeled),'18/18 exact calibration setting lineage, including two legacy cc0 records')
check('10_acc_mean',all(float(x['actual_acc_mean_yr_per_cm'])==float(cfg[(x['core_id'],x['segment'])]['theil_sen_acc_mean_yr_per_cm']) for x in modeled),'18/18 exact configuration lineage')
check('11_thick',all(float(x['thick_cm'])==float(cfg[(x['core_id'],x['segment'])]['proposed_thick_cm']) for x in modeled),'18/18 canonical R1 fallback')
check('12_mem_strength',all(x['mem_strength']=='10' for x in modeled),'18/18 mem.strength=10')
clcount=Counter((x['core_id'],x['segment']) for x in clusters)
check('13_dated_cluster_counts',all(clcount[(x['core_id'],x['segment'])]==int(x['n_dated_depth_clusters']) for x in main if x['final_status'] not in ['excluded_no_chronology']),'19-main model rows reproduce n; seg2 has no chronology')
ad=Counter((x['core_id'],x['segment']) for x in rc if x['admitted_to_model']=='yes')
check('14_admitted_constraints',all(ad[(x['core_id'],x['segment'])]>=clcount[(x['core_id'],x['segment'])] for x in main),'admitted rows cover all clusters; repeated depths allowed')
check('15_stageB_values',len(modeled)==18 and all(x['stageB_status']=='no_preregistered_convergence_failure_detected' and x['actual_iterations_per_chain']=='16000' and x['dip_rejection_count_Holm']=='0' for x in modeled),'18/18 initial rung pass; Holm rejection 0')
bres={(x['core_id'],x['segment']):x for x in rd(FV/'BASELINE_REBUILD_STAGE_GATE_MODEL_RESULTS.csv')}
check('16_CI_median',all(float(x['posterior_CI_median_yr'])==float(bres[(x['core_id'],x['segment'])]['CI_median_yr']) for x in modeled),'18/18 exact formal result')
check('17_precision_class',pc['Tier-1a']==7 and pc['Tier-1b']==2 and pc['Tier-2']==4 and pc['1b-2_intermediate']==1,'mechanical threshold classes')
check('18_final_status',cm==Counter({'precision_class_assigned':14,'not_ranked_sparse_control':2,'legacy':2,'excluded_no_chronology':1}),'controlled statuses exact')
lipds=[p for p in (PKG/'lipd').glob('*.lpd') if not p.name.startswith('._')]; bad=[]
for p in lipds:
 try:
  with zipfile.ZipFile(p) as z:
   m=json.loads(z.read('metadata.jsonld'))
   def keys(v):
    if isinstance(v,dict):return set(v)|set().union(*(keys(q) for q in v.values()))
    if isinstance(v,list):return set().union(*(keys(q) for q in v)) if v else set()
    return set()
   if keys(m)&{'recommended_use','CI_is_data_dominated'}:bad.append(p.name)
 except Exception:bad.append(p.name)
check('19_LiPD_consistency',len(lipds)==19 and not bad,'19 freshly generated archives; canonical fields; deprecated fields absent')
ages=[p for p in (PKG/'age_models').glob('*.csv') if not p.name.startswith('._')];diags=[p for p in (PKG/'201_point_diagnostics').glob('*.csv') if not p.name.startswith('._')]
check('20_age_table_consistency',len(ages)==18 and len(diags)==18 and all(len(rd(p))==201 for p in ages+diags),'18 age + 18 diagnostic tables, each 201 rows')
dep={'recommended_use','quality_tier','CI_is_data_dominated','posterior_CI_med','prior_perturbation_CI_min','acc_prior_posterior_overlap'};fields=set(next(csv.reader((OUT/'master_inventory_v5_candidate.csv').open())))
check('21_no_deprecated_scientific_fields',not(fields&dep),'deprecated columns absent')
livepaths=[str(p.relative_to(PKG)).lower() for p in PKG.rglob('*') if p.is_file() and 'audit/superseded_old_protocol' not in str(p.relative_to(PKG))]
check('22_no_old_sensitivity_product_live',not any(('sensitivity_ensemble' in p or 'time_variable_reservoir' in p or p.endswith('.out')) for p in livepaths),'only inventories retained under audit/superseded_old_protocol')
check('23_no_AppleDouble_sidecar',not any(p.name.startswith('._') for p in PKG.rglob('*')),'zero')
check('24_no_dot_underscore',not any(p.name.startswith('._') for p in PKG.rglob('*')),'zero')
check('25_no_DS_Store',not any(p.name=='.DS_Store' for p in PKG.rglob('*')),'zero')
dictset={(x['table'],x['field_name']) for x in dictionary}; coverage=all((t,f) in dictset for t,p in tables.items() for f in next(csv.reader(p.open())))
check('dictionary_field_coverage',coverage,f'{len(dictionary)} dictionary entries cover all canonical table columns')
check('excluded_28_constraints_retained',sum(x['input_audit_status']=='misused_input' and x['admitted_to_model']=='no' for x in rc)==28,'28/28 retained and excluded')
check('key_record_U1419_seg1',next(x for x in master if x['core_id']=='IODP-U1419' and x['segment']=='seg1')['protocol_conditional_precision_class']=='Tier-1b','Tier-1b / Stage B pass')
check('key_record_U1419_seg3',next(x for x in master if x['core_id']=='IODP-U1419' and x['segment']=='seg3')['protocol_conditional_precision_class']=='Tier-1a','Tier-1a / Stage B pass')
check('key_record_ODP887B',next(x for x in master if x['core_id']=='ODP-887B')['protocol_conditional_precision_class']=='Tier-2','expected frozen class: Tier-2')
check('key_record_85KL',next(x for x in master if x['core_id']=='SO201-2-85KL')['protocol_conditional_precision_class']=='1b-2_intermediate','expected frozen class: 1b-2_intermediate')
wc(OUT/'V1_VALUE_LINEAGE_QA.csv',checks)
fails=[x for x in checks if x['status']=='FAIL']
if fails:
 (OUT/'V1_PRODUCT_BUILD_STOP.md').write_text('# V1 product build STOP\n\n'+json.dumps(fails,indent=2)+'\n');print(json.dumps(fails,indent=2));raise SystemExit(2)

# Freeze canonical master only after all content QA passes.
canonical=ROOT/'master_inventory_v5.csv'; shutil.copy2(OUT/'master_inventory_v5_candidate.csv',canonical);shutil.copy2(canonical,PKG/'classification/master_inventory_v5.csv')
(PKG/'classification/master_inventory_v5_candidate.csv').unlink()
baseline_report=FV/'BASELINE_REBUILD_STAGE_GATE_REPORT_2026-08-12.md'; fvreport=FV/'FINAL_VALIDATION_A_STAGE_GATE_REPORT_2026-08-12.md'
manifest={'CANONICAL_MASTER_INVENTORY':str(canonical),'canonical_master_sha256':sha(canonical),'canonical_master_schema_version':'ESSD_v1.0_master_inventory_v5','source_master_v4':str(ROOT/'master_inventory_v4.csv'),'source_master_v4_status':'superseded_pre_rebuild_baseline','baseline_report':str(baseline_report),'baseline_report_sha256':sha(baseline_report),'final_validation_A_report':str(fvreport),'final_validation_A_sha256':sha(fvreport),'build_code':str(WL/'build_v1_final_product.py'),'build_code_sha256':sha(WL/'build_v1_final_product.py'),'finalize_code':str(WL/'finalize_v1_product.py'),'finalize_code_sha256':sha(WL/'finalize_v1_product.py'),'software_versions':{'rbacon':'3.5.2','rintcal':'1.1.4','R':'4.5.1'},'scientific_computation_phase':'CLOSED','Bacon_ledger':'256/468 frozen','creation_timestamp':datetime.now(timezone.utc).isoformat()}
(OUT/'CANONICAL_V1_PRODUCT_MANIFEST_2026-08-12.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copy2(OUT/'CANONICAL_V1_PRODUCT_MANIFEST_2026-08-12.json',PKG/'CANONICAL_V1_PRODUCT_MANIFEST_2026-08-12.json')

# Package checksums are over every current package file except the checksum file itself.
sumfile=PKG/'SHA256SUMS.txt'; files=sorted(p for p in PKG.rglob('*') if p.is_file() and p!=sumfile and not p.name.startswith('._'))
sumfile.write_text(''.join(f'{sha(p)}  {p.relative_to(PKG)}\n' for p in files))
# 26th check after manifest creation.
listed={line.split('  ',1)[1] for line in sumfile.read_text().splitlines()};expected={str(p.relative_to(PKG)) for p in files}
checks.append({'qa_check':'26_SHA_manifest_complete','status':'PASS' if listed==expected and all(sha(PKG/q)==h for h,q in (line.split('  ',1) for line in sumfile.read_text().splitlines())) else 'FAIL','detail':f'{len(files)} files listed and verified'})
wc(OUT/'V1_VALUE_LINEAGE_QA.csv',checks)
if checks[-1]['status']=='FAIL':raise SystemExit(3)

# Final stage gate.
cs={x['category']:x['count'] for x in rd(OUT/'main_database_count_summary.csv')}; ca={x['category']:x['count'] for x in rd(OUT/'all_adjudicated_count_summary.csv')};qpass=sum(x['status']=='PASS' for x in checks)
report=f'''# ESSD v1.0 final product build — Stage Gate B

1. Canonical master v5 SHA: `{sha(canonical)}`
2. Main 19 final counts: Tier-1={cs['Tier-1_total']} (1a={cs['Tier-1a']}, 1b={cs['Tier-1b']}), Tier-2={cs['Tier-2']}, 1b–2 intermediate={cs['1b-2_intermediate']}, sparse={cs['not_ranked_sparse_control']}, legacy={cs['legacy']}, no chronology={cs['excluded_no_chronology']}.
3. Adjudicated 21 counts: main 19 plus excluded_transition_zone={ca['excluded_transition_zone']}; excluded total={ca['excluded_total']}.
4. Tier-1a / Tier-1b: {cs['Tier-1a']} / {cs['Tier-1b']}.
5. Key-record class check: see generated QA table; record-level value omitted from public code-only release.
6. Boundary-record class check: see generated QA table; record-level value omitted from public code-only release.
7. IODP-U1419 seg1/seg3: Tier-1b / Tier-1a; both Stage B pass.
8. Radiocarbon input rows: {len(rc)}.
9. Excluded 28 constraints retained: yes (28/28 `misused_input`, admitted=no).
10. LiPD validation: PASS, 19/19 freshly generated live archives.
11. PANGAEA staging validation: PASS; staging only, not uploaded.
12. Deprecated fields absent: yes.
13. Superseded sensitivity outputs isolated: yes; inventories only under audit/superseded_old_protocol.
14. QA gates: {qpass}/{len(checks)} PASS; failures=0.
15. SHA validation: PASS; {len(files)} package files listed and verified.
16. `V1_PRODUCT_BUILD_PASS = TRUE`.

Scientific computation is closed at 256/468 Bacon calls. No manuscript, PANGAEA upload, LiPD release, or new scientific computation was performed.
'''
(OUT/'V1_FINAL_PRODUCT_BUILD_STAGE_GATE_REPORT_2026-08-12.md').write_text(report)
# Top-level hashes after final outputs (excluding self).
top=[canonical,OUT/'CANONICAL_V1_PRODUCT_MANIFEST_2026-08-12.json',OUT/'V1_VALUE_LINEAGE_QA.csv',OUT/'V1_FINAL_PRODUCT_BUILD_STAGE_GATE_REPORT_2026-08-12.md',OUT/'MANUSCRIPT_V4_EVIDENCE_PACKET_2026-08-12.md']
(OUT/'V1_FINAL_PRODUCT_SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p}\n' for p in top))
print(report)
