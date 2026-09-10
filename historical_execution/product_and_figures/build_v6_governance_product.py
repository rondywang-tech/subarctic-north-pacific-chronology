#!/usr/bin/env python3
"""Governance-only v5 -> v6 product rebuild. Performs no scientific computation."""
import csv
import hashlib
import json
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WL = ROOT / "audit_2026-07" / "worklist_2026-08-01"
HERE = Path(__file__).resolve().parent
OLD_HANDOFF = WL / "CHATGPT_MANUSCRIPT_V4_FINAL_HANDOFF_2026-08-13"
V5 = OLD_HANDOFF / "canonical_product" / "master_inventory_v5.csv"
OLD_PKG = WL / "V1_FINAL_PRODUCT_BUILD_B_2026-08-12" / "PANGAEA_v1_release_candidate"
NEW_PKG = WL / "V1_FINAL_PRODUCT_BUILD_B_2026-08-12" / "PANGAEA_v1_release_candidate_v2"
NEW_HANDOFF = WL / "CHATGPT_MANUSCRIPT_V4_GOVERNANCE_FINAL_HANDOFF_2026-08-13"
NEW_HANDOFF_ZIP = WL / "CHATGPT_MANUSCRIPT_V4_GOVERNANCE_FINAL_HANDOFF_2026-08-13.zip"
AUDIT = WL / "FULL_PROTOCOL_AUDIT_2026-08-13"
STAGEB_AUDIT = WL / "STAGEB_FINAL_DECLARED_EXECUTED_AUDIT_2026-08-13"
CHANGELOG = HERE / "CHANGELOG_v5_to_v6_GOVERNANCE_2026-08-13.md"
V6 = ROOT / "master_inventory_v6.csv"
EXPECTED_V5_SHA = "8d22ddf6b964ebbdd4bdb1ef1a9af867cbaa1ae1b0d37e0a3401dd05d888d04d"
TS = datetime.now(timezone.utc).astimezone().isoformat()


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def remove_sidecars(root):
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file() and (path.name.startswith("._") or path.name == ".DS_Store"):
            path.unlink()
        elif path.is_dir() and path.name == "__MACOSX":
            shutil.rmtree(path)


def zip_tree(source, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            rel = path.relative_to(source.parent)
            if path.is_file() and not path.name.startswith("._") and path.name != ".DS_Store" and "__MACOSX" not in path.parts:
                archive.write(path, rel)


for required in [V5, OLD_PKG, OLD_HANDOFF, CHANGELOG, AUDIT, STAGEB_AUDIT]:
    if not required.exists():
        raise RuntimeError(f"missing required source: {required}")
if sha(V5) != EXPECTED_V5_SHA:
    raise RuntimeError(f"v5 SHA mismatch: {sha(V5)}")
for forbidden in [V6, NEW_PKG, NEW_HANDOFF, NEW_HANDOFF_ZIP, HERE / "master_inventory_v6.csv"]:
    if forbidden.exists():
        raise RuntimeError(f"refuse overwrite: {forbidden}")

# Preserve immutable v5 before creating any v6 live product.
history = HERE / "audit_history"
history.mkdir(parents=True, exist_ok=True)
copy_file(V5, history / "master_inventory_v5.csv")
(history / "master_inventory_v5_SUPERSESSION.md").write_text(
    "# master_inventory_v5 supersession record\n\n"
    f"Recorded: {TS}\n\n"
    f"SHA-256: `{EXPECTED_V5_SHA}`\n\n"
    "- status: `superseded_by_v6_governance_revision`\n"
    "- scientific posterior: `unchanged`\n"
    "- reason: Stage-B unimodality governance withdrawal and structural-integrity post-audit determination.\n",
    encoding="utf-8",
)

v5_rows = read_csv(V5)
if len(v5_rows) != 21:
    raise RuntimeError(f"expected 21 v5 rows, found {len(v5_rows)}")
formal_keys = {
    (row["core_id"], row["segment"])
    for row in v5_rows
    if row["actual_iterations_per_chain"].strip()
}
if len(formal_keys) != 18:
    raise RuntimeError(f"expected 18 formal models, found {len(formal_keys)}")

# Retain all non-governance v5 columns, rename executed diagnostic counts, and
# replace ambiguous Stage-B fields with controlled governance fields.
remove_fields = {
    "dip_rejection_count_raw",
    "dip_rejection_count_Holm",
    "unimodality_test_status",
    "structural_integrity_status",
}
base_fields = [f for f in v5_rows[0] if f not in remove_fields]
insert_at = base_fields.index("stageB_status") + 1
governance_fields = [
    "stageB_sampling_adequacy_status",
    "stageB_unimodality_formal_status",
    "stageB_structural_integrity_status",
    "unimodality_formal_adjudication_available",
    "unimodality_formal_adjudication_status",
    "executed_dip_diagnostic_status",
    "executed_dip_preregistered_adjudication",
    "executed_dip_rejection_count_raw",
    "executed_dip_rejection_count_Holm",
    "structural_integrity_executed_result",
    "structural_integrity_preregistered_procedure_executed_as_specified",
    "structural_integrity_frozen_outcome",
    "structural_integrity_outcome_determined_post_audit",
    "structural_integrity_tolerance_dominance",
    "structural_integrity_executed_tolerance_yr",
    "structural_integrity_frozen_tolerance_min_yr",
    "structural_integrity_minimum_dominance_ratio",
    "structural_integrity_comparisons_executed_tolerance_looser",
    "unimodality_audit_history",
    "unique_double_unimodality_adjudication_withdrawal",
    "governance_note",
    "posterior_CI_median_release_role",
    "posterior_CI_max_release_role",
    "precision_class_release_role",
]
v6_fields = base_fields[:insert_at] + governance_fields + base_fields[insert_at:]
v6_rows = []
for old in v5_rows:
    row = {field: old.get(field, "") for field in base_fields}
    key = (old["core_id"], old["segment"])
    row["acc_mean_derivation"] = (
        "data_informed_theil_sen_prior_center" if old["acc_mean_derivation"] else ""
    )
    row["schema_version"] = "ESSD_v1.0_master_inventory_v6"
    row["record_release_status"] = "live_scientific_release_governance_final"
    row["posterior_CI_median_release_role"] = "primary_continuous_product" if key in formal_keys else "not_applicable"
    row["posterior_CI_max_release_role"] = "secondary_continuous_product" if key in formal_keys else "not_applicable"
    row["precision_class_release_role"] = "derived_convenience_bin" if old["protocol_conditional_precision_class"] != "NA" else "not_applicable"
    if key in formal_keys:
        row.update({
            "stageB_status": "deprecated_aggregate_field",
            "stageB_sampling_adequacy_status": "no_preregistered_sampling_adequacy_failure_detected",
            "stageB_unimodality_formal_status": "formal_adjudication_unavailable",
            "stageB_structural_integrity_status": "frozen_outcome_pass_determined_post_audit",
            "unimodality_formal_adjudication_available": "FALSE",
            "unimodality_formal_adjudication_status": "withdrawn_due_to_preregistration_and_execution_mismatch",
            "executed_dip_diagnostic_status": "descriptive_only",
            "executed_dip_preregistered_adjudication": "no",
            "executed_dip_rejection_count_raw": old["dip_rejection_count_raw"],
            "executed_dip_rejection_count_Holm": old["dip_rejection_count_Holm"],
            "structural_integrity_executed_result": "pass",
            "structural_integrity_preregistered_procedure_executed_as_specified": "FALSE",
            "structural_integrity_frozen_outcome": "pass_deductively_determined_post_audit",
            "structural_integrity_outcome_determined_post_audit": "TRUE",
            "structural_integrity_tolerance_dominance": "TRUE",
            "structural_integrity_executed_tolerance_yr": "1e-8",
            "structural_integrity_frozen_tolerance_min_yr": "6.12715405e-8",
            "structural_integrity_minimum_dominance_ratio": "6.12715405",
            "structural_integrity_comparisons_executed_tolerance_looser": "0",
            "unimodality_audit_history": "none",
            "unique_double_unimodality_adjudication_withdrawal": "FALSE",
            "governance_note": "Formal unimodality adjudication is unavailable globally; executed dip statistics are descriptive only; structural frozen outcome was determined post-audit.",
        })
        if key == ("IODP-U1419", "seg1"):
            row["unimodality_audit_history"] = "double_withdrawal"
            row["unique_double_unimodality_adjudication_withdrawal"] = "TRUE"
            row["governance_note"] = (
                "Earlier KDE criterion flagged this segment and was withdrawn before formal rebuild because of undeclared tuning parameters; "
                "the replacement preregistered dip adjudication was withdrawn globally because declared and executed implementations did not match; "
                "the current derived precision class is assigned without formal unimodality adjudication, identically to all other records."
            )
    else:
        row.update({
            "stageB_status": "not_applicable",
            "stageB_sampling_adequacy_status": "not_applicable_no_formal_stageB_model",
            "stageB_unimodality_formal_status": "not_applicable_no_formal_stageB_model",
            "stageB_structural_integrity_status": "not_applicable_no_formal_stageB_model",
            "unimodality_formal_adjudication_available": "not_applicable",
            "unimodality_formal_adjudication_status": "not_applicable",
            "executed_dip_diagnostic_status": "not_applicable",
            "executed_dip_preregistered_adjudication": "not_applicable",
            "executed_dip_rejection_count_raw": "",
            "executed_dip_rejection_count_Holm": "",
            "structural_integrity_executed_result": "not_applicable",
            "structural_integrity_preregistered_procedure_executed_as_specified": "not_applicable",
            "structural_integrity_frozen_outcome": "not_applicable",
            "structural_integrity_outcome_determined_post_audit": "not_applicable",
            "structural_integrity_tolerance_dominance": "not_applicable",
            "structural_integrity_executed_tolerance_yr": "",
            "structural_integrity_frozen_tolerance_min_yr": "",
            "structural_integrity_minimum_dominance_ratio": "",
            "structural_integrity_comparisons_executed_tolerance_looser": "",
            "unimodality_audit_history": "none",
            "unique_double_unimodality_adjudication_withdrawal": "FALSE",
            "governance_note": "No formal Stage B posterior product in the release scope.",
        })
    v6_rows.append(row)

write_csv(HERE / "master_inventory_v6.csv", v6_rows, v6_fields)
copy_file(HERE / "master_inventory_v6.csv", V6)

# Build PANGAEA governance candidate v2 from authoritative inputs and canonical
# products. The v1 directory is never opened for writing.
for sub in [
    "classification", "radiocarbon", "clusters", "age_models",
    "201_point_diagnostics", "lipd", "proxy_availability",
    "proxy_demonstration", "provenance", "audit/governance",
    "audit/superseded_old_protocol",
]:
    (NEW_PKG / sub).mkdir(parents=True, exist_ok=True)

for sub in ["radiocarbon", "clusters", "proxy_availability", "proxy_demonstration", "provenance", "audit/superseded_old_protocol"]:
    src_dir = OLD_PKG / sub
    if src_dir.exists():
        for source in sorted(src_dir.rglob("*")):
            if source.is_file() and not source.name.startswith("._") and source.name != ".DS_Store":
                copy_file(source, NEW_PKG / sub / source.relative_to(src_dir))

for source in sorted((OLD_PKG / "age_models").glob("*.csv")):
    if not source.name.startswith("._"):
        copy_file(source, NEW_PKG / "age_models" / source.name)

# Preserve executed diagnostic values and append explicit governance metadata.
diagnostic_files = []
for source in sorted((OLD_PKG / "201_point_diagnostics").glob("*.csv")):
    if source.name.startswith("._"):
        continue
    rows = read_csv(source)
    fields = list(rows[0]) + ["diagnostic_role", "formal_preregistered_adjudication"]
    for row in rows:
        row["diagnostic_role"] = "descriptive_only"
        row["formal_preregistered_adjudication"] = "unavailable"
    target = NEW_PKG / "201_point_diagnostics" / source.name
    write_csv(target, rows, fields)
    diagnostic_files.append(target)

copy_file(HERE / "master_inventory_v6.csv", NEW_PKG / "classification" / "master_inventory_v6.csv")
for name in ["main_database_count_summary.csv", "all_adjudicated_count_summary.csv", "P4_RUN_TO_RUN_REPRODUCIBILITY.csv", "STAGEB_RESULT_INTERPRETATION_NOTE_2026-08-12.md"]:
    candidates = [OLD_PKG / "classification" / name, WL / "V1_FINAL_PRODUCT_BUILD_B_2026-08-12" / name]
    source = next((p for p in candidates if p.exists()), None)
    if source:
        copy_file(source, NEW_PKG / "classification" / name)

# Audit/governance release package, including all required crosswalks.
audit_names = [
    "FULL_PROTOCOL_DECLARED_EXECUTED_CROSSWALK_2026-08-13.csv",
    "FULL_PROTOCOL_POSTAUDIT_RECOVERABILITY_CROSSWALK_2026-08-13.csv",
    "DIP19_TO_FULL91_CROSSWALK_MAPPING_2026-08-13.csv",
    "FULL_PROTOCOL_AUDIT_ITEM_COUNT_BY_COMPONENT_2026-08-13.csv",
    "STRUCTURAL_INTEGRITY_FINAL_GOVERNANCE_AUDIT_2026-08-13.md",
    "STRUCTURAL_INTEGRITY_TOLERANCE_DOMINANCE.csv",
    "U1419_UNIMODALITY_AUDIT_HISTORY_2026-08-13.md",
    "FULL_PROTOCOL_DECLARED_EXECUTED_AUDIT_2026-08-13.md",
    "FULL_PROTOCOL_AUDIT_GOVERNANCE_RULE_2026-08-13.md",
    "POST_AUDIT_OUTCOME_DETERMINATION_RULE_2026-08-13.md",
]
for name in audit_names:
    copy_file(AUDIT / name, NEW_PKG / "audit" / "governance" / name)
copy_file(
    STAGEB_AUDIT / "STAGEB_FINAL_DECLARED_EXECUTED_AUDIT_2026-08-13.md",
    NEW_PKG / "audit" / "governance" / "STAGEB_FINAL_DECLARED_EXECUTED_AUDIT_2026-08-13.md",
)
copy_file(CHANGELOG, NEW_PKG / CHANGELOG.name)

(NEW_PKG / "audit" / "governance" / "README.md").write_text(
    "# Governance audit package\n\n"
    "A 91-item declared-versus-executed crosswalk was completed before submission: 85 MATCH and 6 MISMATCH (G1=1, G2=5, G0=0, G3=0). "
    "The package does not hide the G1/G2 findings. Severity vocabulary: G0 = no discrepancy; G1 = metadata/schema semantics discrepancy; "
    "G2 = method implementation discrepancy whose product implication is separately adjudicated; G3 = posterior-affecting unrecoverable discrepancy. "
    "Crosswalk granularity differs by component; the accompanying item-count table reports the exact counts, and unimodality/dip has finer-grained items.\n",
    encoding="utf-8",
)

# Fresh LiPD archives generated from v6 metadata and v2 canonical product tables.
main_rows = [row for row in v6_rows if row["final_status"] != "excluded_transition_zone"]
for row in main_rows:
    stem = f"{row['core_id']}__{row['segment']}"
    age_path = NEW_PKG / "age_models" / f"{stem}.csv"
    diag_path = NEW_PKG / "201_point_diagnostics" / f"{stem}.csv"
    metadata = {
        "dataSetName": stem,
        "archiveType": "marine sediment",
        "schemaVersion": "ESSD_v1.0_governance_v6",
        "core_id": row["core_id"],
        "segment": row["segment"],
        "geo": {
            "latitude": row["lat"],
            "longitude": row["lon"],
            "waterDepth_m": row["water_depth_m"],
            "subRegion": row["sub_region"],
        },
        "chronology": {
            "final_status": row["final_status"],
            "protocol_conditional_precision_class": row["protocol_conditional_precision_class"],
            "precision_class_release_role": row["precision_class_release_role"],
            "posterior_CI_median_yr": row["posterior_CI_median_yr"] or None,
            "posterior_CI_median_release_role": row["posterior_CI_median_release_role"],
            "posterior_CI_max_yr": row["posterior_CI_max_yr"] or None,
            "posterior_CI_max_release_role": row["posterior_CI_max_release_role"],
            "delta_R_yr": row["delta_R_yr"] or None,
            "delta_STD_yr": row["delta_STD_yr"] or None,
            "cc": row["cc"] or None,
            "acc_mean": row["actual_acc_mean_yr_per_cm"] or None,
            "acc_mean_derivation": row["acc_mean_derivation"] or None,
            "thick_cm": row["thick_cm"] or None,
            "mem_mean": row["mem_mean"] or None,
            "mem_strength": row["mem_strength"] or None,
        },
        "stageB_governance": {
            "sampling_adequacy_status": row["stageB_sampling_adequacy_status"],
            "unimodality_formal_status": row["stageB_unimodality_formal_status"],
            "executed_dip_diagnostic_status": row["executed_dip_diagnostic_status"],
            "executed_dip_preregistered_adjudication": row["executed_dip_preregistered_adjudication"],
            "structural_integrity_status": row["stageB_structural_integrity_status"],
            "structural_integrity_preregistered_procedure_executed_as_specified": row["structural_integrity_preregistered_procedure_executed_as_specified"],
            "unimodality_audit_history": row["unimodality_audit_history"],
            "unique_double_unimodality_adjudication_withdrawal": row["unique_double_unimodality_adjudication_withdrawal"],
        },
    }
    target = NEW_PKG / "lipd" / f"{stem}.lpd"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("metadata.jsonld", json.dumps(metadata, indent=2) + "\n")
        if age_path.exists():
            archive.write(age_path, "tables/age_model.csv")
        if diag_path.exists():
            archive.write(diag_path, "tables/201_point_diagnostics.csv")

# README: self-contained product positioning and governance interpretation.
(NEW_PKG / "README.md").write_text(
    "# North Pacific chronology framework — ESSD v1.0 governance release candidate v2\n\n"
    "This staging package provides audited radiocarbon inputs, 18 uniformly reconstructed canonical chronologies, 201-point posterior age products, continuous posterior uncertainty, and protocol-conditional precision classes. It has not been uploaded.\n\n"
    "## Primary and derived precision products\n\n"
    "`posterior_CI_median_yr` is the primary continuous precision product. `posterior_CI_max_yr` is secondary. `protocol_conditional_precision_class` is a derived convenience bin under frozen Stage D thresholds; it is not a reliability tier, quality tier, fitness-for-use rating, or recommended-use mapping.\n\n"
    "## Stage B positioning\n\n"
    "Stage B is a model-output diagnostic and integrity stage, not a quality gate that excluded models in v1.0; its exclusion contribution is zero. It contains (1) rank-normalized/folded split-Rhat, bulk-ESS, and tail-ESS sampling-adequacy diagnostics; (2) descriptive dip-test outputs whose formal hard unimodality adjudication was withdrawn globally; and (3) a structural pipeline-integrity assertion whose frozen outcome was determined post-audit by tolerance dominance. The preregistered structural procedure itself was not executed as specified. Non-rejection by the descriptive dip test is not proof of unimodality.\n\n"
    "No model failed the preregistered Rhat/ESS criteria at the initial rung. Hard formal unimodality adjudication is unavailable for all 18 formal models. Structural frozen outcome is pass for all 18, deductively determined post-audit.\n\n"
    "## Accumulation-rate prior center\n\n"
    "`acc.mean` uses a deterministic, data-informed rule for centering the accumulation-rate prior. It is not an MCMC initialization heuristic and is not an uncertainty-weighted estimate. This terminology correction does not change any posterior.\n\n"
    "## Audit transparency\n\n"
    "A 91-item declared-versus-executed crosswalk was performed before submission: 85 MATCH and 6 MISMATCH (G1=1, G2=5, G3=0). Posterior-affecting core components matched. Full crosswalks, severity definitions, structural governance, and the U1419 unimodality history are provided under `audit/governance/`. Item counts document that audit granularity was not identical across components.\n\n"
    "## Contents\n\n"
    "- `classification/`: master inventory v6 and frozen count summaries.\n"
    "- `radiocarbon/` and `clusters/`: audited determinations and eligible dated-depth clusters.\n"
    "- `age_models/`: 18 unchanged canonical 201-point posterior age tables.\n"
    "- `201_point_diagnostics/`: sampling diagnostics and retained descriptive dip statistics.\n"
    "- `lipd/`: 19 freshly rebuilt LiPD archives (18 models plus the no-chronology main record).\n"
    "- `proxy_availability/` and `proxy_demonstration/`: proxy census and demonstration subset.\n"
    "- `audit/governance/`: final governance evidence.\n"
    "- `DATA_DICTIONARY_v2.csv`: field definitions and controlled interpretation.\n\n"
    "Scientific computation is closed. Bacon ledger: 256 / 468.\n",
    encoding="utf-8",
)

# Complete dictionary coverage for canonical CSVs, with explicit controlled
# governance definitions and release roles.
definitions = {
    "posterior_CI_median_yr": ("Median width of pointwise 95% posterior age intervals across the dated interval", "yr", "number", "primary_continuous_product", "Not absolute age accuracy or universal reliability"),
    "posterior_CI_max_yr": ("Maximum width of pointwise 95% posterior age intervals across the dated interval", "yr", "number", "secondary_continuous_product", "Not absolute age accuracy or universal reliability"),
    "protocol_conditional_precision_class": ("Convenience bin derived mechanically from posterior_CI_median_yr under frozen Stage D thresholds", "1", "string", "derived_convenience_bin", "Not a reliability tier, quality tier, fitness-for-use tier, or recommended-use mapping"),
    "acc_mean_derivation": ("A deterministic, data-informed rule for centering the accumulation-rate prior", "1", "string", "data_informed_theil_sen_prior_center", "Not MCMC initialization or an uncertainty-weighted estimate"),
    "stageB_status": ("Deprecated aggregate Stage B compatibility field", "1", "string", "deprecated_aggregate_field", "Must not be used for scientific interpretation"),
    "stageB_sampling_adequacy_status": ("Outcome status for preregistered Rhat, bulk-ESS, and tail-ESS sampling-adequacy diagnostics", "1", "string", "model_output_diagnostic", "Does not prove convergence"),
    "stageB_unimodality_formal_status": ("Availability of formal preregistered hard unimodality adjudication", "1", "string", "formal_adjudication_unavailable", "Executed dip non-rejection is not proof of unimodality"),
    "stageB_structural_integrity_status": ("Frozen structural-integrity outcome status", "1", "string", "post_audit_integrity_assertion", "Does not imply the preregistered procedure was executed as specified"),
    "executed_dip_diagnostic_status": ("Scientific role of retained executed dip-test outputs", "1", "string", "descriptive_only", "Not formal classification evidence"),
    "executed_dip_preregistered_adjudication": ("Whether executed dip output is the preregistered adjudication", "1", "string", "no", "Must not be represented as a preregistered pass"),
    "structural_integrity_frozen_outcome": ("Frozen structural-integrity conclusion after governance audit", "1", "string", "pass_deductively_determined_post_audit", "Procedure itself was not executed as specified"),
    "diagnostic_role": ("Scientific role of retained executed dip diagnostic columns", "1", "string", "descriptive_only", "Not a formal unimodality adjudication"),
    "formal_preregistered_adjudication": ("Availability of a matching formal preregistered unimodality adjudication", "1", "string", "unavailable", "No pass/fail inference"),
}
table_paths = {
    "master_inventory_v6": NEW_PKG / "classification" / "master_inventory_v6.csv",
    "radiocarbon_input_table_v1": NEW_PKG / "radiocarbon" / "radiocarbon_input_table_v1.csv",
    "dated_depth_cluster_table_v1": NEW_PKG / "clusters" / "dated_depth_cluster_table_v1.csv",
    "age_models": next(iter(sorted(p for p in (NEW_PKG / "age_models").glob("*.csv") if not p.name.startswith("._")))),
    "201_point_diagnostics": next(iter(sorted(p for p in (NEW_PKG / "201_point_diagnostics").glob("*.csv") if not p.name.startswith("._")))),
}
dictionary = []
for table, path in table_paths.items():
    fields = next(csv.reader(path.open(encoding="utf-8-sig")))
    for field in fields:
        definition, unit, dtype, role, prohibited = definitions.get(
            field,
            (
                field.replace("_", " "),
                "cal yr BP" if "age" in field.lower() and "depth" not in field.lower() else ("cm" if "depth" in field.lower() else ("yr" if field.endswith("_yr") or "CI_" in field else "1")),
                "number" if any(token in field.lower() for token in ["depth", "age", "error", "rhat", "ess", "ci_", "count", "strength", "mean", "thick", "delta", "tolerance", "ratio"]) else "string",
                "traceable value or release metadata",
                "Do not extend beyond README product boundaries",
            ),
        )
        dictionary.append({
            "table": table,
            "field_name": field,
            "definition": definition,
            "units": unit,
            "type": dtype,
            "release_role": role,
            "allowed_values": "see README and controlled vocabulary",
            "source": "v5 scientific value, canonical posterior product, audited constraint table, or governance crosswalk",
            "scientific_interpretation": role,
            "prohibited_interpretation": prohibited,
            "nullable": "yes",
            "release_status": "live",
        })
write_csv(NEW_PKG / "DATA_DICTIONARY_v2.csv", dictionary)

# Frozen counts and manuscript evidence.
main_counter = Counter(row["final_status"] for row in main_rows)
class_counter = Counter(row["protocol_conditional_precision_class"] for row in main_rows)
counts = {
    "main_rows": len(main_rows),
    "Tier-1": class_counter["Tier-1a"] + class_counter["Tier-1b"],
    "Tier-1a": class_counter["Tier-1a"],
    "Tier-1b": class_counter["Tier-1b"],
    "Tier-2": class_counter["Tier-2"],
    "1b-2_intermediate": class_counter["1b-2_intermediate"],
    "sparse": main_counter["not_ranked_sparse_control"],
    "legacy": main_counter["legacy"],
    "no_chronology": main_counter["excluded_no_chronology"],
    "transition_zone_outside_main": sum(row["final_status"] == "excluded_transition_zone" for row in v6_rows),
}
evidence = HERE / "MANUSCRIPT_V4_GOVERNANCE_FINAL_EVIDENCE_PACKET_2026-08-13.md"
evidence.write_text(
    "# Manuscript v4 governance-final evidence packet\n\n"
    "## Product counts\n\n"
    f"Main 19: Tier-1={counts['Tier-1']} (1a={counts['Tier-1a']}, 1b={counts['Tier-1b']}), Tier-2={counts['Tier-2']}, "
    f"1b–2 intermediate={counts['1b-2_intermediate']}, sparse={counts['sparse']}, legacy={counts['legacy']}, no chronology={counts['no_chronology']}. "
    f"Two transition-zone records remain outside the main database.\n\n"
    "## Stage B wording\n\n"
    "Sampling adequacy: No model failed the preregistered Rhat/ESS criteria at the initial rung.\n\n"
    "Unimodality: Hard formal adjudication was withdrawn globally. Executed dip outputs are descriptive only.\n\n"
    "Structural integrity: The frozen outcome is PASS for all models, determined post-audit by tolerance dominance; the preregistered procedure itself was not executed as specified.\n\n"
    "## Full audit\n\n"
    "The declared-versus-executed crosswalk contains 91 items: 85 MATCH and 6 MISMATCH (G1=1, G2=5, G3=0). Posterior-affecting core components all MATCH.\n\n"
    "## U1419\n\n"
    "IODP-U1419 segment 1 uniquely carries a double-withdrawal audit history: an earlier KDE criterion was withdrawn because tuning parameters were undeclared, and the later preregistered dip adjudication was withdrawn globally after a declared/executed mismatch. Its continuous CI and derived class are retained under the same no-formal-unimodality-adjudication governance applied to every model. Segment 3 does not carry this double-withdrawal history.\n\n"
    "## Prohibited claims\n\n"
    "- all Stage B criteria were executed as preregistered\n"
    "- all models passed preregistered unimodality\n"
    "- all posteriors are unimodal\n"
    "- structural preregistration was executed as specified\n"
    "- reliability grading or quality-tier language\n"
    "- recommended-use mapping\n",
    encoding="utf-8",
)

# Canonical manifest is written before the package checksum and records the two
# immutable scientific-lineage inventories.
manifest_path = HERE / "CANONICAL_V1_GOVERNANCE_FINAL_MANIFEST_2026-08-13.json"
manifest = {
    "creation_timestamp": TS,
    "canonical_master_v5": str(V5),
    "v5_sha256": EXPECTED_V5_SHA,
    "canonical_master_v6": str(V6),
    "v6_sha256": sha(V6),
    "posterior_unchanged": True,
    "age_outputs_unchanged": True,
    "CI_values_unchanged": True,
    "derived_classes_unchanged": True,
    "governance_schema_revision": True,
    "formal_models": 18,
    "LiPD_archives": 19,
    "Bacon_calls_this_revision": 0,
    "Bacon_ledger": "256/468 frozen",
}
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
copy_file(manifest_path, NEW_PKG / manifest_path.name)

# Supersession markers are siblings, so old candidate/handoff bytes remain untouched.
(OLD_PKG.parent / "PANGAEA_v1_release_candidate_SUPERSEDED_BY_GOVERNANCE_V2.md").write_text(
    "# Supersession marker\n\n`PANGAEA_v1_release_candidate/` is superseded by `PANGAEA_v1_release_candidate_v2/`. The old directory was not overwritten.\n",
    encoding="utf-8",
)
(OLD_HANDOFF.parent / "CHATGPT_MANUSCRIPT_V4_FINAL_HANDOFF_2026-08-13_SUPERSEDED_BY_GOVERNANCE_HANDOFF_V2.md").write_text(
    "# Supersession marker\n\nThe original handoff and ZIP are superseded by the governance-final handoff v2. Original bytes were not overwritten.\n",
    encoding="utf-8",
)

# Build handoff v2 (no raw chains).
for sub in ["current_manuscript", "canonical_product", "final_reports", "audit_governance", "rewrite_materials"]:
    (NEW_HANDOFF / sub).mkdir(parents=True, exist_ok=True)
copy_file(OLD_HANDOFF / "current_manuscript" / "ESSD_manuscript_v3_5.md", NEW_HANDOFF / "current_manuscript" / "ESSD_manuscript_v3_5.md")
for src, dst in [
    (V6, NEW_HANDOFF / "canonical_product" / "master_inventory_v6.csv"),
    (NEW_PKG / "DATA_DICTIONARY_v2.csv", NEW_HANDOFF / "canonical_product" / "DATA_DICTIONARY_v2.csv"),
    (NEW_PKG / "README.md", NEW_HANDOFF / "canonical_product" / "PANGAEA_RELEASE_CANDIDATE_V2_README.md"),
    (NEW_PKG / "classification" / "main_database_count_summary.csv", NEW_HANDOFF / "canonical_product" / "main_database_count_summary.csv"),
    (NEW_PKG / "classification" / "all_adjudicated_count_summary.csv", NEW_HANDOFF / "canonical_product" / "all_adjudicated_count_summary.csv"),
    (evidence, NEW_HANDOFF / "final_reports" / evidence.name),
    (manifest_path, NEW_HANDOFF / "final_reports" / manifest_path.name),
    (CHANGELOG, NEW_HANDOFF / "final_reports" / CHANGELOG.name),
    (AUDIT / "FULL_PROTOCOL_DECLARED_EXECUTED_CROSSWALK_2026-08-13.csv", NEW_HANDOFF / "audit_governance" / "FULL_PROTOCOL_DECLARED_EXECUTED_CROSSWALK_2026-08-13.csv"),
    (AUDIT / "FULL_PROTOCOL_POSTAUDIT_RECOVERABILITY_CROSSWALK_2026-08-13.csv", NEW_HANDOFF / "audit_governance" / "FULL_PROTOCOL_POSTAUDIT_RECOVERABILITY_CROSSWALK_2026-08-13.csv"),
    (AUDIT / "U1419_UNIMODALITY_AUDIT_HISTORY_2026-08-13.md", NEW_HANDOFF / "audit_governance" / "U1419_UNIMODALITY_AUDIT_HISTORY_2026-08-13.md"),
    (AUDIT / "STRUCTURAL_INTEGRITY_FINAL_GOVERNANCE_AUDIT_2026-08-13.md", NEW_HANDOFF / "audit_governance" / "STRUCTURAL_INTEGRITY_FINAL_GOVERNANCE_AUDIT_2026-08-13.md"),
    (OLD_HANDOFF / "rewrite_materials" / "REFERENCES_STATUS_FOR_V4.csv", NEW_HANDOFF / "rewrite_materials" / "REFERENCES_STATUS_FOR_V4.csv"),
    (OLD_HANDOFF / "rewrite_materials" / "MANUSCRIPT_V4_REWRITE_BRIEF_2026-08-13.md", NEW_HANDOFF / "rewrite_materials" / "MANUSCRIPT_V4_REWRITE_BRIEF_2026-08-13.md"),
]:
    copy_file(src, dst)

# Remove filesystem metadata before checksums and QA.
remove_sidecars(NEW_PKG)
remove_sidecars(NEW_HANDOFF)
remove_sidecars(HERE)

# QA gates (exactly 21 user-specified checks).
qa = []
def check(number, name, passed, detail):
    qa.append({"check_number": number, "qa_check": name, "status": "PASS" if passed else "FAIL", "detail": detail})

v6_by_key = {(r["core_id"], r["segment"]): r for r in v6_rows}
v5_by_key = {(r["core_id"], r["segment"]): r for r in v5_rows}
check(1, "v6_row_count", len(v6_rows) == 21, f"{len(v6_rows)} rows")
check(2, "v5_to_v6_posterior_CI_median_exact_equality", all(v6_by_key[k]["posterior_CI_median_yr"] == v["posterior_CI_median_yr"] for k, v in v5_by_key.items()), "all 21 strings exact")
check(3, "v5_to_v6_posterior_CI_max_exact_equality", all(v6_by_key[k]["posterior_CI_max_yr"] == v["posterior_CI_max_yr"] for k, v in v5_by_key.items()), "all 21 strings exact")
old_ages = {p.name: sha(p) for p in (OLD_PKG / "age_models").glob("*.csv") if not p.name.startswith("._")}
new_ages = {p.name: sha(p) for p in (NEW_PKG / "age_models").glob("*.csv") if not p.name.startswith("._")}
check(4, "canonical_age_tables_exact_equality", old_ages == new_ages and len(new_ages) == 18, "18/18 byte-identical")
check(5, "derived_precision_classes_exact_equality", all(v6_by_key[k]["protocol_conditional_precision_class"] == v["protocol_conditional_precision_class"] for k, v in v5_by_key.items()), "all 21 exact")
formal_rows = [v6_by_key[k] for k in formal_keys]
check(6, "unimodality_formal_unavailable", len(formal_rows) == 18 and all(r["unimodality_formal_adjudication_available"] == "FALSE" and r["stageB_unimodality_formal_status"] == "formal_adjudication_unavailable" for r in formal_rows), "18/18")
check(7, "structural_frozen_outcome_postaudit_pass", all(r["structural_integrity_frozen_outcome"] == "pass_deductively_determined_post_audit" for r in formal_rows), "18/18")
check(8, "sampling_adequacy_field", all(r["stageB_sampling_adequacy_status"] == "no_preregistered_sampling_adequacy_failure_detected" for r in formal_rows), "18/18")
master_headers = set(v6_fields)
forbidden_formal = {"unimodality_pass", "preregistered_unimodality_pass", "StageB_unimodality_gate_pass"}
check(9, "no_formal_unimodality_pass_field", not (master_headers & forbidden_formal), "no forbidden live master field")
check(10, "no_recommended_use", "recommended_use" not in master_headers and all("recommended_use" not in json.loads(zipfile.ZipFile(p).read("metadata.jsonld")) for p in (NEW_PKG / "lipd").glob("*.lpd")), "absent from live schema")
check(11, "no_quality_tier", "quality_tier" not in master_headers, "absent")
check(12, "no_CI_is_data_dominated", "CI_is_data_dominated" not in master_headers, "absent")
seg1 = v6_by_key[("IODP-U1419", "seg1")]
seg3 = v6_by_key[("IODP-U1419", "seg3")]
check(13, "U1419_seg1_double_history", seg1["unimodality_audit_history"] == "double_withdrawal" and seg1["unique_double_unimodality_adjudication_withdrawal"] == "TRUE", "unique audit attribute present")
check(14, "U1419_seg3_not_double_history", seg3["unimodality_audit_history"] != "double_withdrawal" and seg3["unique_double_unimodality_adjudication_withdrawal"] == "FALSE", "not double withdrawal")
check(15, "acc_mean_terminology_corrected", all(r["acc_mean_derivation"] == "data_informed_theil_sen_prior_center" for r in formal_rows), "18/18")
lipds = [p for p in (NEW_PKG / "lipd").glob("*.lpd") if not p.name.startswith("._")]
lipd_ok = len(lipds) == 19
for path in lipds:
    with zipfile.ZipFile(path) as archive:
        meta = json.loads(archive.read("metadata.jsonld"))
        blob = json.dumps(meta)
        lipd_ok = lipd_ok and "recommended_use" not in blob and "quality_tier" not in blob and "CI_is_data_dominated" not in blob and "preregistered_unimodality_pass" not in blob
check(16, "LiPD_consistency", lipd_ok, f"{len(lipds)}/19 fresh archives")
check(17, "PANGAEA_staging_consistency", (NEW_PKG / "classification" / "master_inventory_v6.csv").read_bytes() == V6.read_bytes() and len(diagnostic_files) == 18, "master exact; 18 diagnostic tables")
required_audit = [NEW_PKG / "audit" / "governance" / name for name in audit_names[:6]]
check(18, "full_audit_package_included", all(p.exists() for p in required_audit), f"{sum(p.exists() for p in required_audit)}/{len(required_audit)} required files")
all_product_files = list(NEW_PKG.rglob("*")) + list(NEW_HANDOFF.rglob("*")) + list(HERE.rglob("*"))
check(19, "AppleDouble_zero", not any(p.is_file() and p.name.startswith("._") for p in all_product_files), "0")
check(20, "DS_Store_zero", not any(p.is_file() and p.name == ".DS_Store" for p in all_product_files), "0")

# Package and handoff checksums, then handoff ZIP.
pkg_sum = NEW_PKG / "SHA256SUMS.txt"
pkg_files = sorted(p for p in NEW_PKG.rglob("*") if p.is_file() and p != pkg_sum and not p.name.startswith("._"))
pkg_sum.write_text("".join(f"{sha(p)}  {p.relative_to(NEW_PKG)}\n" for p in pkg_files), encoding="utf-8")
handoff_sum = NEW_HANDOFF / "SHA256SUMS.txt"
handoff_files = sorted(p for p in NEW_HANDOFF.rglob("*") if p.is_file() and p != handoff_sum and not p.name.startswith("._"))
handoff_sum.write_text("".join(f"{sha(p)}  {p.relative_to(NEW_HANDOFF)}\n" for p in handoff_files), encoding="utf-8")
zip_tree(NEW_HANDOFF, NEW_HANDOFF_ZIP)

def sums_valid(root, sum_path):
    entries = [line.split("  ", 1) for line in sum_path.read_text(encoding="utf-8").splitlines()]
    return all((root / rel).exists() and sha(root / rel) == digest for digest, rel in entries)

check(21, "SHA_complete", sums_valid(NEW_PKG, pkg_sum) and sums_valid(NEW_HANDOFF, handoff_sum), f"package={len(pkg_files)} files; handoff={len(handoff_files)} files")
write_csv(HERE / "V6_GOVERNANCE_IMPLEMENTATION_QA.csv", qa)
failures = [row for row in qa if row["status"] == "FAIL"]

stage_gate = HERE / "V6_GOVERNANCE_IMPLEMENTATION_STAGE_GATE_REPORT_2026-08-13.md"
stage_gate.write_text(
    "# V6 governance implementation stage gate\n\n"
    f"- v5 SHA-256: `{EXPECTED_V5_SHA}`\n"
    f"- v6 SHA-256: `{sha(V6)}`\n"
    f"- v5→v6 CI median exact equality: `{qa[1]['status']}`\n"
    f"- v5→v6 CI max exact equality: `{qa[2]['status']}`\n"
    f"- derived precision class exact equality: `{qa[4]['status']}`\n"
    f"- final counts: `{json.dumps(counts, sort_keys=True)}`\n"
    f"- unimodality formal unavailable: `18/18`\n"
    f"- structural post-audit PASS: `18/18`\n"
    f"- G1 live schema issue cleared: `{qa[8]['status']}`\n"
    f"- LiPD rebuild: `{qa[15]['status']}`\n"
    f"- PANGAEA staging v2: `{qa[16]['status']}`\n"
    f"- QA: `{len(qa) - len(failures)}/{len(qa)} PASS; failures={len(failures)}`\n"
    f"- final handoff v2 ZIP: `{NEW_HANDOFF_ZIP}`\n"
    f"- final handoff v2 ZIP SHA-256: `{sha(NEW_HANDOFF_ZIP)}`\n"
    f"- Bacon calls in this revision: `0`; ledger remains `256 / 468`\n"
    f"- `V6_GOVERNANCE_IMPLEMENTATION_PASS = {'TRUE' if not failures else 'FALSE'}`\n\n"
    "Stopped at the required stage gate. No manuscript editing, upload, correspondence, new audit, or scientific computation was performed.\n",
    encoding="utf-8",
)

result = {
    "v6_sha256": sha(V6),
    "counts": counts,
    "qa_total": len(qa),
    "qa_failures": len(failures),
    "handoff_zip": str(NEW_HANDOFF_ZIP),
    "handoff_zip_sha256": sha(NEW_HANDOFF_ZIP),
    "PANGAEA_v2": str(NEW_PKG),
    "pass": not failures,
}
(HERE / "V6_GOVERNANCE_IMPLEMENTATION_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
if failures:
    raise SystemExit(2)
