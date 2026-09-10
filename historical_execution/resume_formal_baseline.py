#!/usr/bin/env python3
import csv, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import run_formal_baseline as base

H = Path(__file__).resolve().parent
ORIGINAL = H / "formal_runs"
RECOVERY = H / "formal_recovery_runs"
AUDIT = H / "FORMAL_BASELINE_20_ATTEMPT_SALVAGE_AUDIT.csv"
INITIAL_USED = 160
INCREMENTAL_CAP = 308
base.RUNS = RECOVERY

def readcsv(path):
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))

models = base.models
audit = readcsv(AUDIT)
salvaged = {(r["core_id"], r["segment"], int(r["chain_id"])): Path(r["expected_out_path"])
             for r in audit if r["salvage_status"] == "salvaged_complete"}
prior_attempted = {(r["core_id"], r["segment"], int(r["chain_id"])): r for r in audit}

def current_rung_outputs(model, calls, ledger):
    keybase = (model["core_id"], model["segment"])
    outputs = {}
    jobs = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for chain in range(1, 5):
            key = keybase + (chain,)
            if key in salvaged:
                outputs[chain] = salvaged[key]
                ledger.append({"recovery_call": "", "total_used_after_call": "", "core_id": model["core_id"],
                    "segment": model["segment"], "rung": 16000, "chain": chain,
                    "disposition": "salvaged_complete_prior_attempt", "out_file": str(outputs[chain]),
                    "supersedes_attempt_id": ""})
            else:
                jobs[pool.submit(base.run_chain, model, 16000, chain)] = chain
        for future in as_completed(jobs):
            chain = jobs[future]; out = future.result(); calls += 1
            prior = prior_attempted.get(keybase + (chain,))
            disposition = "rerun_same_seed_same_config" if prior else "first_attempt_current_rung"
            rd = out.parent
            (rd / "runtime_recovery_lineage.json").write_text(json.dumps({
                "disposition": disposition,
                "supersedes_attempt_id": prior["attempt_id"] if prior else None,
                "superseded_run_directory": prior["run_directory"] if prior else None,
                "scientific_configuration_changed": False,
                "seed_changed": False}, indent=2) + "\n", encoding="utf-8")
            outputs[chain] = out
            ledger.append({"recovery_call": calls, "total_used_after_call": INITIAL_USED + calls,
                "core_id": model["core_id"], "segment": model["segment"], "rung": 16000,
                "chain": chain, "disposition": disposition, "out_file": str(out),
                "supersedes_attempt_id": prior["attempt_id"] if prior else ""})
    return calls, outputs

def write_state(calls, results, ledger):
    fields = ["recovery_call","total_used_after_call","core_id","segment","rung","chain","disposition","out_file","supersedes_attempt_id"]
    with (H / "FORMAL_BASELINE_RECOVERY_CALL_LEDGER.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(ledger)
    (H / "FORMAL_BASELINE_RECOVERY_EXECUTION_STATE.json").write_text(json.dumps({
        "prior_used": INITIAL_USED, "recovery_calls": calls, "total_used": INITIAL_USED + calls,
        "results": results, "timestamp": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n", encoding="utf-8")

def main():
    if RECOVERY.exists(): raise RuntimeError(f"refuse overwrite {RECOVERY}")
    RECOVERY.mkdir(); calls = 0; results = []; ledger = []
    # Complete the interrupted 16k rung, salvaging only audited-complete chains.
    for model in models:
        calls, outputs = current_rung_outputs(model, calls, ledger)
        if calls > INCREMENTAL_CAP: raise RuntimeError("formal hard cap exceeded")
        (RECOVERY / (model["core_id"]+"__"+model["segment"]) / "rung_16000").mkdir(parents=True, exist_ok=True)
        summary = base.postprocess(model, 16000, [outputs[i] for i in range(1,5)])
        summary.update({"core_id": model["core_id"], "segment": model["segment"], "rung": 16000})
        results.append(summary); write_state(calls, results, ledger)
        print(json.dumps({"rung":16000,"model":model["core_id"]+"__"+model["segment"],
                          "recovery_calls":calls,"convergence_pass":summary["convergence_pass"]}), flush=True)
    # Frozen adaptive ladder: only models not yet passing all-depth convergence advance.
    for rung in (32000, 64000, 128000):
        pending = [m for m in models if next(x for x in results if x["core_id"]==m["core_id"] and x["segment"]==m["segment"])["convergence_pass"] != "TRUE"]
        if not pending: break
        if calls + len(pending)*4 > INCREMENTAL_CAP: raise RuntimeError("formal hard cap exceeded")
        jobs = {}; outputs = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for model in pending:
                for chain in range(1,5): jobs[pool.submit(base.run_chain,model,rung,chain)] = (model,chain)
            for future in as_completed(jobs):
                model,chain=jobs[future];out=future.result();calls+=1
                outputs.setdefault((model["core_id"],model["segment"]),{})[chain]=out
                ledger.append({"recovery_call":calls,"total_used_after_call":INITIAL_USED+calls,
                    "core_id":model["core_id"],"segment":model["segment"],"rung":rung,"chain":chain,
                    "disposition":"adaptive_ladder_fresh_rung","out_file":str(out),"supersedes_attempt_id":""})
        for model in pending:
            oo=outputs[(model["core_id"],model["segment"])]
            summary=base.postprocess(model,rung,[oo[i] for i in range(1,5)])
            summary.update({"core_id":model["core_id"],"segment":model["segment"],"rung":rung})
            results=[x for x in results if not(x["core_id"]==model["core_id"] and x["segment"]==model["segment"])]+[summary]
        write_state(calls,results,ledger)
        print(json.dumps({"rung":rung,"recovery_calls":calls,"converged":sum(x["convergence_pass"]=="TRUE" for x in results)}),flush=True)
    print(f"FORMAL_BASELINE_RECOVERY_COMPLETE recovery_calls={calls} total_used={INITIAL_USED+calls}")

if __name__ == "__main__": main()
