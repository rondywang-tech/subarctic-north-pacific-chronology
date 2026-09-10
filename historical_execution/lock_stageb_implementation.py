#!/usr/bin/env python3
import csv,hashlib,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
H=Path(__file__).resolve().parent;ts=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=(H/'STAGEB_R_ENVIRONMENT_BEFORE_DEPENDENCY_INSTALL_2026-08-12.txt').read_text()
after=(H/'STAGEB_R_ENVIRONMENT_AFTER_DEPENDENCY_INSTALL_2026-08-12.txt').read_text()
for key in ['R.version.string','rbacon_version','rintcal_version']:
 a=re.search(rf'^{re.escape(key)}=(.*)$',before,re.M).group(1);b=re.search(rf'^{re.escape(key)}=(.*)$',after,re.M).group(1)
 if a!=b:raise RuntimeError(f'{key} changed {a} -> {b}')
local=[]
p=subprocess.run(['/usr/local/bin/Rscript','--vanilla','-e',f'.libPaths(c(normalizePath("{H/"R_stageB_library"}"),.libPaths()));x<-installed.packages(lib.loc=normalizePath("{H/"R_stageB_library"}"));write.table(x[,c("Package","Version")],row.names=FALSE,col.names=FALSE,quote=FALSE)'],capture_output=True,text=True,check=True)
for line in p.stdout.splitlines():
 z=line.split();
 if len(z)>=2:local.append((z[0],z[1]))
soft=H/'STAGEB_DIAGNOSTIC_SOFTWARE_LOCK_2026-08-12.md'
soft.write_text('# Stage B diagnostic software lock — 2026-08-12\n\n'+f'**Timestamp:** {ts}  \n**CRAN repository:** https://cloud.r-project.org  \n**Local library:** `{H/"R_stageB_library"}`\n\n'+
 'Installed official releases and required dependencies:\n\n'+'\n'.join(f'- `{a} {b}`' for a,b in sorted(local))+'\n\n'+
 '- R: unchanged (`R version 4.1.2 (2021-11-01)`)\n- rbacon: unchanged (`3.5.2`)\n- rintcal: unchanged (`1.1.0`)\n- `.libPaths()` places the project-local library first in every diagnostic script.\n',encoding='utf-8')
files=['stageb_diagnostics.R','stageb_postprocess_model.R','run_formal_baseline.py','STAGEB_DIAGNOSTIC_IMPLEMENTATION_SMOKE_TEST_2026-08-12.R','STAGEB_DIAGNOSTIC_IMPLEMENTATION_SMOKE_TEST_2026-08-12.md','STAGEB_400_DRAW_PROVENANCE_SMOKE_TEST.csv','STAGEB_201_DEPTH_SHAPE_SMOKE_TEST.csv','FORMAL_BASELINE_CONFIGURATION_AND_SEEDS_PREFLIGHT.csv']
lock=H/'STAGEB_IMPLEMENTATION_LOCK_2026-08-12.md'
lock.write_text(f'''# Stage B implementation lock — 2026-08-12

**Timestamp:** {ts}  
`STAGE_B_IMPLEMENTATION_READY = TRUE`  
`CLAUDE_REVIEW_TRIGGER_RESOLUTION = resolved_as_software_dependency_only`

The historical stop report is retained unchanged. Official CRAN dependencies were added locally without altering R, rbacon, rintcal, thresholds, or the Stage B preregistration.

- Rhat: `posterior::rhat(x)`; x is retained iterations × four independent chains; threshold `<1.01`.
- bulk ESS: `posterior::ess_bulk(x)`; threshold `>=400`.
- tail ESS: `posterior::ess_tail(x)`; threshold `>=400`.
- Dip: `diptest::dip.test(x, simulate.p.value=FALSE)`.
- Holm: `p.adjust(p_values, method="holm")`, 201 values, alpha 0.05.
- Evaluation: exactly 201 ordered dated-interval depths.
- Balanced dip sample: exactly 100 deterministic equally spaced retained indices per chain, merged in chain order 1–4; no random sampling.
- Diagnostic order: convergence first; dip/Holm only following all-depth convergence.

Smoke tests passed for good versus shifted four-chain matrices, deterministic dip output, 201-value Holm cardinality/order, the complete 201-depth convergence wrapper, and the balanced 400-draw pipeline. No threshold was derived from the smoke tests.

## Frozen file hashes

'''+''.join(f'- `{x}`: `{sha(H/x)}`\n' for x in files)+f'- Stage B preregistration: `{sha(H.parent/"StageB_redesign_2026-08-11"/"STAGE_B_PREREGISTRATION_2026-08-11.md")}`\n',encoding='utf-8')
checks=H/'STAGEB_DEPENDENCY_AND_IMPLEMENTATION_SHA256SUMS.txt'
with checks.open('w') as f:
 for p in [H/'STAGEB_R_ENVIRONMENT_BEFORE_DEPENDENCY_INSTALL_2026-08-12.txt',H/'STAGEB_R_ENVIRONMENT_AFTER_DEPENDENCY_INSTALL_2026-08-12.txt',soft,lock]+[H/x for x in files]:f.write(f'{sha(p)}  {p.name}\n')
print('IMPLEMENTATION_LOCKED',len(local),'local packages')
