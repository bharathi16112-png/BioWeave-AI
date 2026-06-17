"""Aggregate live evidence from free public APIs."""

from __future__ import annotations

import logging

from services.civic_client import fetch_civic_evidence
from services.clinvar_client import build_clinvar_evidence
from services.oncokb_client import enrich_evidence_with_oncokb

logger = logging.getLogger(__name__)


def enrich_all_evidence(profile: dict, base_evidence: list[dict]) -> tuple[list[dict], str | None]:
    """
    Merge curated KB evidence with live free-tier API results.

    Priority: ClinVar → CIViC → OncoKB (demo/public) → curated fallback.
    Individual API failures are logged and skipped gracefully.
    """
    gene = profile.get("gene", "")
    variant = profile.get("variant") or profile.get("protein_change", "")
    live_entries: list[dict] = []
    therapy_override = None

    try:
        clinvar = build_clinvar_evidence(gene, variant)
        if clinvar:
            live_entries.append(clinvar)
            if "pathogenic" in clinvar.get("assertion", "").lower():
                profile["_clinical_significance"] = "Pathogenic"
    except Exception as exc:
        logger.warning("ClinVar enrichment skipped: %s", exc)

    try:
        civic_entries, civic_therapy = fetch_civic_evidence(gene, variant)
        live_entries.extend(civic_entries)
        if civic_therapy:
            therapy_override = civic_therapy
    except Exception as exc:
        logger.warning("CIViC enrichment skipped: %s", exc)

    merged = list(base_evidence)
    try:
        evidence, oncokb_therapy = enrich_evidence_with_oncokb(profile, merged)
        if oncokb_therapy and not therapy_override:
            therapy_override = oncokb_therapy
    except Exception as exc:
        logger.warning("OncoKB enrichment skipped: %s", exc)
        evidence = merged

    combined = live_entries + [e for e in evidence if not e.get("live")]
    for idx, entry in enumerate(combined):
        entry["step"] = idx + 1

    return combined, therapy_override


def resolve_clinical_significance(profile: dict, evidence: list[dict]) -> str:
    if profile.get("_clinical_significance"):
        return profile["_clinical_significance"]
    for entry in evidence:
        assertion = entry.get("assertion", "")
        if "pathogenic" in assertion.lower():
            return "Pathogenic"
        if entry.get("live") and "oncogenic" in assertion.lower():
            return "Oncogenic"
    return "Pathogenic"
