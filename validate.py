"""validate.py — Quick smoke-test for pipeline output schema."""
import sys
sys.path.insert(0, ".")

# ── 1. Mock profiles ──────────────────────────────────────────────────────────
from utils.data_loader import load_profile, get_available_mutations

for m in get_available_mutations():
    d = load_profile(m)
    nodes_n   = len(d["graph_data"]["nodes"])
    excl_n    = len(d["why_not_exclusion_panel"])
    evid_n    = len(d["evidence_timeline"])
    print(f"Mock OK: {m}  nodes={nodes_n}  exclusions={excl_n}  evidence={evid_n}")

# ── 2. Live pipeline (text path — no GPU required) ────────────────────────────
import pipeline as pl

REQUIRED_KEYS = [
    "executive_summary", "metadata", "system_metrics",
    "agent_trace", "graph_data", "pathway_intervention_engine",
    "why_not_exclusion_panel", "evidence_timeline",
]

REQUIRED_META = ["patient_id", "primary_tumor_type", "mutation"]

tests = [
    ("EGFR text NER",   "EGFR L858R exon 19 deletion detected",      "EGFR L858R"),
    ("BRAF text NER",   "Patient shows BRAF V600E mutation melanoma", "BRAF V600E"),
    ("KRAS G12C regex", "Variant G12C confirmed in RAS pathway",      "KRAS G12C"),
    ("ALK fusion regex","EML4-ALK fusion rearrangement detected",     "ALK Fusion"),
    ("Fallback",        "unrelated text with no known markers",       "BRAF V600E"),
]

all_ok = True
for label, report, expected_mut in tests:
    result = pl.run_multi_agent_pipeline(report)

    missing_keys  = [k for k in REQUIRED_KEYS if k not in result]
    missing_meta  = [k for k in REQUIRED_META if k not in result.get("metadata", {})]
    actual_mut    = result["executive_summary"]["mutation"]
    patient_id    = result["metadata"].get("patient_id", "MISSING")
    latency_ms    = result["system_metrics"]["total_latency_ms"]
    nodes_n       = len(result["graph_data"]["nodes"])
    excl_n        = len(result["why_not_exclusion_panel"])
    evid_n        = len(result["evidence_timeline"])
    agents        = [a["agent_name"] for a in result["agent_trace"]]
    suppress_pct  = round((
        result["pathway_intervention_engine"]["baseline_pathway_activity_score"] -
        result["pathway_intervention_engine"]["predicted_post_intervention_activity_score"]
    ) / result["pathway_intervention_engine"]["baseline_pathway_activity_score"] * 100)

    status = "PASS" if (not missing_keys and not missing_meta and actual_mut == expected_mut) else "FAIL"
    if status == "FAIL":
        all_ok = False

    print(f"\n[{status}] {label}")
    print(f"  Mutation   : {actual_mut} (expected: {expected_mut})")
    print(f"  Patient ID : {patient_id}")
    print(f"  Latency    : {latency_ms} ms  (real measured)")
    print(f"  Nodes/Excl/Evid: {nodes_n}/{excl_n}/{evid_n}")
    print(f"  Suppression: {suppress_pct}% cascade reduction")
    print(f"  Agents     : {agents}")
    if missing_keys:  print(f"  MISSING KEYS: {missing_keys}")
    if missing_meta:  print(f"  MISSING META: {missing_meta}")

print("\n" + ("=" * 50))
print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
