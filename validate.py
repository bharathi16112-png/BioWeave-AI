"""validate.py — Quick smoke-test for pipeline output schema."""
import os
import sys

os.environ.setdefault("BIOWEAVE_DISABLE_ML", "true")

sys.path.insert(0, ".")

# ── 1. Demo profiles ──────────────────────────────────────────────────────────
from utils.data_loader import load_profile, get_available_mutations

for m in get_available_mutations():
    d = load_profile(m)
    nodes_n = len(d["graph_data"]["nodes"])
    excl_n = len(d["why_not_exclusion_panel"])
    evid_n = len(d["evidence_timeline"])
    print(f"Demo OK: {m}  nodes={nodes_n}  exclusions={excl_n}  evidence={evid_n}")

# ── 2. Docking module check ───────────────────────────────────────────────────
print("\n[Docking availability check]")
from services.docking import is_vina_available, is_meeko_available, _fallback_result

vina_ok = is_vina_available()
meeko_ok = is_meeko_available()
print(f"  AutoDock Vina : {'available' if vina_ok else 'not installed (pip install vina)'}")
print(f"  meeko         : {'available' if meeko_ok else 'not installed (pip install meeko rdkit)'}")

# Smoke test fallback (always works without Vina)
fallback = _fallback_result("BRAF V600E", "test fallback")
assert fallback.is_fallback, "Expected is_fallback=True"
assert fallback.binding_affinity_kcal_mol < 0, "Expected negative affinity"
assert 0.0 < fallback.pathway_suppression < 1.0, "Suppression out of range"
assert fallback.baseline_score > fallback.post_intervention_score, "Baseline should exceed post"
print(f"  Fallback test : OK  affinity={fallback.binding_affinity_kcal_mol} kcal/mol  "
      f"suppression={fallback.pathway_suppression}  "
      f"baseline={fallback.baseline_score} -> post={fallback.post_intervention_score}")

# ── 3. Live pipeline (text path — no GPU required) ────────────────────────────
import pipeline as pl

REQUIRED_KEYS = [
    "analysis_status",
    "executive_summary",
    "metadata",
    "system_metrics",
    "agent_trace",
    "graph_data",
    "pathway_intervention_engine",
    "why_not_exclusion_panel",
    "evidence_timeline",
]

REQUIRED_META = ["patient_id", "primary_tumor_type", "mutation"]
REQUIRED_DOCKING = ["method", "binding_affinity_kcal_mol", "pathway_suppression", "is_fallback"]

tests = [
    ("EGFR exon 19 del", "EGFR exon 19 deletion detected in biopsy", "EGFR Exon 19 Del", "completed"),
    ("BRAF text NER", "Patient shows BRAF V600E mutation melanoma", "BRAF V600E", "completed"),
    ("KRAS G12C regex", "Variant KRAS G12C confirmed in RAS pathway", "KRAS G12C", "completed"),
    ("ALK fusion regex", "EML4-ALK fusion rearrangement detected", "EML4-ALK Fusion", "completed"),
    ("Multimodal text only", "EGFR L858R activating mutation NSCLC", "EGFR Exon 19 Del", "completed"),
    ("Insufficient evidence", "unrelated text with no known markers", "Insufficient Evidence", "insufficient_evidence"),
    ("Image-only blocked", "", "Insufficient Evidence", "insufficient_evidence", True),
]

all_ok = True
for case in tests:
    if len(case) == 5:
        label, report, expected_mut, expected_state, image_only = case
        result = pl.run_multi_agent_pipeline(report, uploaded_image=object())
    else:
        label, report, expected_mut, expected_state = case
        result = pl.run_multi_agent_pipeline(report)

    missing_keys = [k for k in REQUIRED_KEYS if k not in result]
    missing_meta = [k for k in REQUIRED_META if k not in result.get("metadata", {})]
    actual_mut = result["executive_summary"]["mutation"]
    actual_state = result.get("analysis_status", {}).get("analysis_state")
    patient_id = result["metadata"].get("patient_id", "MISSING")
    latency_ms = result["system_metrics"]["total_latency_ms"]
    gpu = result["system_metrics"]["gpu_hardware"]
    nodes_n = len(result["graph_data"]["nodes"])
    agents = [a["agent_name"] for a in result["agent_trace"]]
    vina_enabled = result["system_metrics"].get("vina_enabled", False)

    # Docking sub-key checks (only for completed analyses)
    docking_ok = True
    missing_docking = []
    if actual_state == "completed":
        pie = result.get("pathway_intervention_engine", {})
        docking_data = pie.get("docking", {})
        missing_docking = [k for k in REQUIRED_DOCKING if k not in docking_data]
        if missing_docking:
            docking_ok = False

    mutation_ok = actual_mut == expected_mut
    state_ok = actual_state == expected_state
    status = "PASS" if (not missing_keys and not missing_meta and mutation_ok and state_ok and docking_ok) else "FAIL"
    if status == "FAIL":
        all_ok = False

    docking_method = result.get("pathway_intervention_engine", {}).get("docking", {}).get("method", "N/A")
    docking_affinity = result.get("pathway_intervention_engine", {}).get("docking", {}).get("binding_affinity_kcal_mol", "N/A")

    print(f"\n[{status}] {label}")
    print(f"  State         : {actual_state} (expected: {expected_state})")
    print(f"  Mutation      : {actual_mut} (expected: {expected_mut})")
    print(f"  Patient ID    : {patient_id}")
    print(f"  Latency       : {latency_ms} ms")
    print(f"  GPU           : {gpu}")
    print(f"  Nodes         : {nodes_n}")
    print(f"  Agents        : {agents}")
    print(f"  Vina enabled  : {vina_enabled}")
    print(f"  Docking method: {docking_method}  affinity={docking_affinity}")
    if missing_keys:
        print(f"  MISSING KEYS     : {missing_keys}")
    if missing_meta:
        print(f"  MISSING META     : {missing_meta}")
    if missing_docking:
        print(f"  MISSING DOCKING  : {missing_docking}")

print("\n" + ("=" * 50))
print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
