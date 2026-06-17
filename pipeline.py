"""
pipeline.py — Precision Oncology Multi-Agent Inference Pipeline
================================================================
Orchestrates Agent 1 (Molecular Detective), Agent 2 (Pathway Pathologist),
and Agent 3 (Therapeutic Matchmaker) with honest inference semantics.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from services.clinical_kb import get_profile
from services.docking import run_docking, is_vina_available
from services.evidence import enrich_all_evidence, resolve_clinical_significance
from services.hardware import detect_compute_environment
from services.hip_parallel import run_agents_parallel, get_stream_info
from services.llm_agent import enrich_therapeutic_rationale, is_llm_enabled
from services.vision import fuse_multimodal_confidence

logger = logging.getLogger(__name__)


def _build_insufficient_evidence_output(
    reason: str,
    pipeline_start: float,
    has_image: bool,
    has_text: bool,
) -> dict:
    """Return a schema-safe payload when mutation cannot be determined."""
    hw = detect_compute_environment()
    total_latency_ms = round((time.perf_counter() - pipeline_start) * 1000)
    input_type = "multimodal" if has_image and has_text else ("image" if has_image else "text")

    return {
        "analysis_status": {
            "input_type": input_type,
            "analysis_state": "insufficient_evidence",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "message": reason,
        },
        "executive_summary": {
            "mutation": "Insufficient Evidence",
            "clinical_significance": "Unknown",
            "affected_pathway": "N/A",
            "recommended_therapy": "N/A",
            "confidence": 0.0,
        },
        "metadata": {
            "patient_id": "LIVE-UNRESOLVED",
            "primary_tumor_type": "N/A",
            "mutation": {"gene": "N/A", "variant": "N/A", "family": "N/A"},
        },
        "system_metrics": {
            "gpu_hardware": hw["gpu_hardware"],
            "compute_platform": hw["compute_platform"],
            "tokens_generated": 0,
            "total_latency_ms": total_latency_ms,
            "vram_allocated_gb": hw["vram_allocated_gb"],
            "llm_enabled": is_llm_enabled(),
            "vina_enabled": is_vina_available(),
            "hip_streams": {"hip_streams_active": False},
        },
        "agent_trace": [
            {
                "agent_name": "Molecular Detective",
                "status": "failed",
                "duration_ms": total_latency_ms,
                "task": reason,
            },
            {
                "agent_name": "Pathway Pathologist",
                "status": "skipped",
                "duration_ms": 0,
                "task": "Skipped — no validated mutation signature.",
            },
            {
                "agent_name": "Therapeutic Matchmaker",
                "status": "skipped",
                "duration_ms": 0,
                "task": "Skipped — no validated mutation signature.",
            },
        ],
        "graph_data": {"nodes": [], "edges": []},
        "pathway_intervention_engine": {
            "baseline_pathway_activity_score": 0.0,
            "predicted_post_intervention_activity_score": 0.0,
            "therapeutic_rationale": reason,
        },
        "why_not_exclusion_panel": [],
        "evidence_timeline": [],
    }


def run_multi_agent_pipeline(raw_patient_report: str, uploaded_image=None) -> dict | None:
    """
    Execute the three-agent pipeline with honest multimodal semantics.

    Free-tier integrations:
    - OpenMed NER + regex (Agent 1 text)
    - owkin/phikon pathology ViT (Agent 1 visual screening)
    - ClinVar + CIViC + OncoKB public/demo APIs (Agent 3 evidence)
    """
    pipeline_start = time.perf_counter()
    has_image = uploaded_image is not None
    has_text = bool(raw_patient_report and raw_patient_report.strip())

    agent1_start = time.perf_counter()
    # Run NER + vision in parallel using HIP/CUDA streams (or thread-pool on CPU)
    text_detection, visual = run_agents_parallel(
        text=raw_patient_report if has_text else "",
        image=uploaded_image,
    )
    stream_info = get_stream_info()

    if has_image and not has_text and not visual:
        return _build_insufficient_evidence_output(
            "Pathology ViT failed to process the uploaded slide.",
            pipeline_start,
            has_image=True,
            has_text=False,
        )

    if has_image and not has_text:
        return _build_insufficient_evidence_output(
            "Image-only mutation classification is not supported. "
            "Please paste a genomic report — Phikon provides visual screening only.",
            pipeline_start,
            has_image=True,
            has_text=False,
        )

    if not text_detection:
        return _build_insufficient_evidence_output(
            "No supported oncology mutation markers were found in the genomic report. "
            "Supported profiles: BRAF V600E, EGFR Exon 19 Del, KRAS G12C, EML4-ALK Fusion.",
            pipeline_start,
            has_image=has_image,
            has_text=has_text,
        )

    profile_key = text_detection.profile_key
    confidence, fusion_method = fuse_multimodal_confidence(text_detection, visual)
    agent1_ms = round((time.perf_counter() - agent1_start) * 1000)

    agent2_start = time.perf_counter()
    kb = get_profile(profile_key)
    pathway = kb["pathway"]

    # Real docking via AutoDock Vina — gracefully falls back to curated scores
    docking = run_docking(profile_key)
    baseline_score = docking.baseline_score
    post_score = docking.post_intervention_score
    docking_method = docking.method
    docking_affinity = docking.binding_affinity_kcal_mol
    docking_fallback = docking.is_fallback

    agent2_ms = round((time.perf_counter() - agent2_start) * 1000)

    agent3_start = time.perf_counter()
    drug = kb["drug"]
    evidence, therapy_override = enrich_all_evidence(kb, list(kb["evidence"]))
    if therapy_override:
        drug = therapy_override

    rationale, tokens_generated = enrich_therapeutic_rationale(
        mutation=profile_key,
        pathway=pathway,
        drug=drug,
        report_excerpt=raw_patient_report[:500],
        base_rationale=kb["rationale"],
    )
    agent3_ms = round((time.perf_counter() - agent3_start) * 1000)

    hw = detect_compute_environment()
    total_latency_ms = round((time.perf_counter() - pipeline_start) * 1000)
    clinical_significance = resolve_clinical_significance(kb, evidence)

    visual_detail = ""
    if visual:
        visual_detail = (
            f" Phikon screened {visual.tiles_processed} tile(s) "
            f"(entropy={visual.feature_entropy})."
        )

    agent1_task = (
        f"Multimodal fusion ({fusion_method}) identified '{profile_key}' "
        f"via {text_detection.method}.{visual_detail}"
    )

    return {
        "analysis_status": {
            "input_type": "multimodal" if has_image and has_text else "text",
            "analysis_state": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "executive_summary": {
            "mutation": profile_key,
            "clinical_significance": clinical_significance,
            "affected_pathway": pathway,
            "recommended_therapy": drug,
            "confidence": confidence,
        },
        "metadata": {
            "patient_id": "LIVE-" + profile_key.replace(" ", "-"),
            "primary_tumor_type": kb["tumor_type"],
            "mutation": {
                "gene": kb["gene"],
                "variant": kb["variant"],
                "family": kb["family"],
            },
        },
        "system_metrics": {
            "gpu_hardware": hw["gpu_hardware"],
            "compute_platform": hw["compute_platform"],
            "tokens_generated": tokens_generated,
            "total_latency_ms": total_latency_ms,
            "vram_allocated_gb": hw["vram_allocated_gb"],
            "llm_enabled": is_llm_enabled(),
            "vina_enabled": is_vina_available(),
            "hip_streams": stream_info,
        },
        "agent_trace": [
            {
                "agent_name": "Molecular Detective",
                "status": "completed",
                "duration_ms": agent1_ms,
                "task": agent1_task,
            },
            {
                "agent_name": "Pathway Pathologist",
                "status": "completed",
                "duration_ms": agent2_ms,
                "task": (
                    f"Mapped hyperactivated signaling vectors down the {pathway}. "
                    f"AutoDock Vina docking ({docking_method}): "
                    f"{docking.drug_name} → {docking_affinity:.2f} kcal/mol against "
                    f"{docking.pdb_id or 'target structure'}."
                ),
            },
            {
                "agent_name": "Therapeutic Matchmaker",
                "status": "completed",
                "duration_ms": agent3_ms,
                "task": (
                    f"Queried ClinVar, CIViC, and OncoKB (free APIs) for {drug}. "
                    f"Validated therapeutic evidence and contraindications."
                ),
            },
        ],
        "graph_data": {"nodes": kb["nodes"], "edges": kb["edges"]},
        "pathway_intervention_engine": {
            "baseline_pathway_activity_score": baseline_score,
            "predicted_post_intervention_activity_score": post_score,
            "therapeutic_rationale": rationale,
            "docking": {
                "method": docking_method,
                "binding_affinity_kcal_mol": docking_affinity,
                "all_pose_scores": docking.all_pose_scores,
                "pathway_suppression": docking.pathway_suppression,
                "pdb_id": docking.pdb_id,
                "drug_name": docking.drug_name,
                "is_fallback": docking_fallback,
                "docking_time_s": docking.docking_time_s,
                "target_description": docking.meta.get("target_description", ""),
            },
        },
        "why_not_exclusion_panel": [
            {
                "drug_name": exc["drug_name"],
                "class": exc["class"],
                "status": exc["status"],
                "reasoning": exc["reasoning"],
            }
            for exc in kb["exclusions"]
        ],
        "evidence_timeline": evidence,
    }
