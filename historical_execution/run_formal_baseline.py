#!/usr/bin/env python3
import csv,hashlib,json,shutil,subprocess
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from output_discovery import discover_expected_scientific_out

H=Path(__file__).resolve().parent;RUNS=H/'formal_runs';MAN=H/'FORMAL_BASELINE_CONFIGURATION_AND_SEEDS_PREFLIGHT.csv'
R='/usr/local/bin/Rscript';RUNGS=[16000,32000,64000,128000];MAX_CALLS=328
def readcsv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
models=readcsv(MAN)

R_TEMPLATE='''suppressPackageStartupMessages(library(rbacon))
.libPaths(c(normalizePath("{local_lib}"),.libPaths()))
set.seed({seed})
core<-"{runid}";coredir<-"{parent}"
Bacon(core=core,coredir=coredir,d.min={dmin},d.max={dmax},thick={thick},d.by=0.5,add.bottom=FALSE,
 ssize={ssize},seed={seed},acc.mean={accmean},acc.shape=1.5,mem.mean=0.5,mem.strength=10,
 cc={cc},delta.R={dr},delta.STD={drstd},t.a=3,t.b=4,remember=FALSE,suggest=FALSE,
 accept.suggestions=FALSE,ask=FALSE,plot.pdf=FALSE)
rd<-file.path(coredir,core);of<-file.path(rd,paste0(core,"_",{expected_k},".out"));bf<-file.path(rd,paste0(core,"_",{expected_k},".bacon"))
if(!file.exists(of)||!file.exists(bf))stop("expected output missing")
allout<-list.files(rd,"\\\\.out$",full.names=TRUE,all.files=TRUE)
realout<-allout[!startsWith(basename(allout),"._")]
if(length(realout)!=1||normalizePath(realout)!=normalizePath(of))stop("real scientific output cardinality/path mismatch")
x<-read.table(of,header=FALSE);K<-ncol(x)-3L;if(nrow(x)!={ssize})stop("iteration mismatch")
if(K!={expected_k})stop(sprintf("K mismatch got %d expected %d",K,{expected_k}))
write.csv(data.frame(depth_cm=info$elbows),sub("\\\\.out$","_actual_elbows.csv",of),row.names=FALSE)
writeLines(c(sprintf("rbacon=%s",packageVersion("rbacon")),sprintf("rintcal=%s",packageVersion("rintcal"))),file.path(rd,"software_versions.txt"))
'''

def run_chain(m,rung,chain):
 stem=m['core_id']+'__'+m['segment'];parent=RUNS/stem/f'rung_{rung}';runid=f'{stem}__formal_stageB__rung{rung}__chain{chain}'
 rd=parent/runid
 if rd.exists():raise RuntimeError(f'refuse overwrite {rd}')
 parent.mkdir(parents=True,exist_ok=True);rd.mkdir()
 src=Path(m['input_file']);dst=rd/f'{runid}.csv';shutil.copy2(src,dst)
 if sha(dst)!=m['input_sha256']:raise RuntimeError(f'input sha mismatch {stem}')
 script=R_TEMPLATE.format(local_lib=(H/'R_stageB_library').as_posix(),seed=m[f'chain_{chain}_seed'],runid=runid,parent=parent.as_posix(),
  dmin=m['d_min_cm'],dmax=m['d_max_cm'],thick=m['proposed_thick_cm'],ssize=rung,accmean=m['theil_sen_acc_mean_yr_per_cm'],
  cc=m['cc'],dr=m['delta_R_yr'],drstd=m['delta_STD_yr'],expected_k=m['deterministic_actual_geometry_K'])
 sp=rd/'run.R';sp.write_text(script,encoding='utf-8')
 (rd/'chain_manifest.json').write_text(json.dumps({'configuration_manifest_sha256':sha(MAN),'model':stem,'rung':rung,'chain':chain,'seed':int(m[f'chain_{chain}_seed']),'input_sha256':m['input_sha256']},indent=2)+'\n')
 p=subprocess.run([R,'--vanilla',str(sp)],cwd=H,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (rd/'run.log').write_text(p.stdout,encoding='utf-8')
 if p.returncode:raise RuntimeError(f'R failure {runid}: {p.stdout[-1500:]}')
 expected_name=f"{runid}_{m['deterministic_actual_geometry_K']}.out"
 out,sidecars=discover_expected_scientific_out(rd,expected_name)
 (rd/'filesystem_metadata_sidecars.json').write_text(json.dumps({'classification':'filesystem_metadata_sidecar','files':[str(x) for x in sidecars]},indent=2)+'\n')
 return out

def postprocess(m,rung,outs):
 stem=m['core_id']+'__'+m['segment'];od=RUNS/stem/f'rung_{rung}'
 cmd=[R,'--vanilla',str(H/'stageb_postprocess_model.R'),str(H/'R_stageB_library'),str(H/'stageb_diagnostics.R'),str(od),m['proposed_thick_cm'],m['d_min_cm'],m['d_max_cm'],m['d_min_cm'],m['d_max_cm'],';'.join(map(str,outs))]
 p=subprocess.run(cmd,cwd=H,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(od/'postprocess.log').write_text(p.stdout,encoding='utf-8')
 if p.returncode:raise RuntimeError(f'postprocess failure {stem} rung {rung}: {p.stdout[-2000:]}')
 return next(csv.DictReader((od/'stageB_rung_summary.csv').open()))

def main():
 if RUNS.exists():raise RuntimeError(f'refuse overwrite {RUNS}')
 RUNS.mkdir();calls=0;results=[];ledger=[]
 for rung in RUNGS:
  pending=[m for m in models if not any(x['core_id']==m['core_id'] and x['segment']==m['segment'] and x['convergence_pass']=='TRUE' for x in results)]
  if not pending:break
  need=len(pending)*4
  if calls+need>MAX_CALLS:raise RuntimeError('formal baseline call ceiling exceeded')
  jobs={}
  with ThreadPoolExecutor(max_workers=4) as pool:
   for m in pending:
    for chain in range(1,5):jobs[pool.submit(run_chain,m,rung,chain)]=(m,chain)
   outputs={}
   for fut in as_completed(jobs):
    m,ch=jobs[fut];o=fut.result();outputs.setdefault((m['core_id'],m['segment']),{})[ch]=o;calls+=1
    ledger.append({'call':calls,'core_id':m['core_id'],'segment':m['segment'],'rung':rung,'chain':ch,'out_file':str(o)})
  for m in pending:
   oo=outputs[(m['core_id'],m['segment'])];assert set(oo)=={1,2,3,4}
   s=postprocess(m,rung,[oo[i] for i in range(1,5)]);s.update({'core_id':m['core_id'],'segment':m['segment'],'rung':rung})
   results=[x for x in results if not(x['core_id']==m['core_id'] and x['segment']==m['segment'])]+[s]
  with (H/'FORMAL_BASELINE_CALL_LEDGER.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(ledger[0]),lineterminator='\n');w.writeheader();w.writerows(ledger)
  (H/'FORMAL_BASELINE_EXECUTION_STATE.json').write_text(json.dumps({'calls':calls,'results':results,'timestamp':datetime.now(timezone.utc).isoformat()},indent=2)+'\n')
  print(json.dumps({'rung':rung,'calls':calls,'converged':sum(x['convergence_pass']=='TRUE' for x in results),'models':len(results)}),flush=True)
 print('FORMAL_BASELINE_EXECUTION_COMPLETE calls=',calls)
if __name__=='__main__':main()
