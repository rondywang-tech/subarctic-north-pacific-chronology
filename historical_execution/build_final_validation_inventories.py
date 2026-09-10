#!/usr/bin/env python3
import csv,hashlib,re
from pathlib import Path
H=Path(__file__).resolve().parent; AUD=H.parents[2]
def sha(p):
 try:return hashlib.sha256(p.read_bytes()).hexdigest()
 except:return ''
def wcsv(p,rr,fields):
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rr)

# U1419 superseded baseline evidence, deliberately excluding current four-chain formal outputs.
u=[]
for p in AUD.rglob('*'):
 if not p.is_file() or p.name.startswith('._') or H in p.parents:continue
 s=str(p).lower()
 if 'u1419' not in s:continue
 if p.suffix.lower() not in {'.out','.bacon','.csv','.md','.txt','.json'}:continue
 typ='old_single_chain_output' if p.suffix=='.out' else ('old_bacon_settings' if p.suffix=='.bacon' else ('diagnostic_table' if p.suffix=='.csv' else 'report_or_metadata'))
 seg='seg1' if 'seg1' in s else ('seg3' if 'seg3' in s else 'unspecified')
 u.append({'path':str(p.resolve()),'artifact_type':typ,'segment':seg,'bytes':p.stat().st_size,'sha256':sha(p),'scientific_status':'superseded_baseline_provenance_only','four_chain_recomputability':'new_four_chain_stageB_not_recomputable_on_old_single_chain_outputs' if p.suffix in {'.out','.bacon'} else 'not_applicable'})
wcsv(H/'U1419_SUPERSEDED_BASELINE_ARTIFACT_INVENTORY_2026-08-12.csv',u,['path','artifact_type','segment','bytes','sha256','scientific_status','four_chain_recomputability'])

# Old-protocol sensitivity products: files in explicitly named historical sensitivity/scenario subtrees.
keys=('dr_sensitivity','deltar','reservoir','butzin','sarnthein','time_variable','time-variable','prior_sensitivity','acc_sensitivity','sensitivity_2026')
products=[]
for p in AUD.rglob('*'):
 if not p.is_file() or p.name.startswith('._') or H in p.parents:continue
 s=str(p).lower()
 if not any(k in s for k in keys):continue
 # Limit to artifacts in analysis/audit sensitivity contexts, not incidental field mentions.
 if p.suffix.lower() not in {'.csv','.md','.txt','.json','.out','.bacon','.png','.pdf','.r','.py'}:continue
 if '90' in s or 'ensemble' in s:typ='90_member_deltaR_ensemble'
 elif 'time' in s or 'sarnthein' in s:typ='time_variable_deltaR_scenario'
 elif 'migrat' in s or 'database' in s or 'butzin' in s:typ='migrated_database_robustness'
 elif 'prior' in s or 'acc' in s or 'thick' in s or 'mem' in s:typ='old_acc_thick_mem4_sensitivity'
 else:typ='old_deltaR_or_reservoir_sensitivity'
 products.append({'path':str(p.resolve()),'product_type':typ,'protocol_version':'pre_formal_baseline_old_protocol','scientific_status':'superseded_old_protocol','release_status':'exclude_from_ESSD_v1_scientific_release','superseded_reason':'generated under superseded baseline and/or old deltaR/acc.mean/thick/mem=4 protocol'})
wcsv(H/'SUPERSEDED_OLD_PROTOCOL_SENSITIVITY_INVENTORY_2026-08-12.csv',products,['path','product_type','protocol_version','scientific_status','release_status','superseded_reason'])

# Claim locations in manuscript/readme/release-manifest-like files only.
claims=[]; pat=re.compile(r'(90[- ]member|time[- ]variable|ΔR|delta\.?R|reservoir|Butzin|Sarnthein|sensitivity)',re.I)
for p in AUD.rglob('*'):
 if not p.is_file() or p.name.startswith('._') or H in p.parents:continue
 nm=p.name.lower(); s=str(p).lower()
 if p.suffix.lower() not in {'.md','.txt','.csv'}:continue
 if not (('readme' in nm) or ('manifest' in nm) or ('manuscript' in s) or ('submission' in s) or ('release' in s)):continue
 try: lines=p.read_text(errors='replace').splitlines()
 except:continue
 for no,line in enumerate(lines,1):
  if pat.search(line):claims.append({'file':str(p.resolve()),'section_line':str(no),'claim':line[:2000]})
wcsv(H/'OLD_PROTOCOL_SENSITIVITY_CLAIM_INVENTORY_2026-08-12.csv',claims,['file','section_line','claim'])
print('U1419',len(u),'old products',len(products),'claims',len(claims))
