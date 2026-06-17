"""OncoKB API client for live therapeutic evidence enrichment."""

from __future__ import annotations

import logging
from typing import Any

import requests

from services.config import ONCOKB_API_TOKEN, ONCOKB_DEMO_URL, ONCOKB_PUBLIC_URL

logger = logging.getLogger(__name__)

DEMO_GENES = {"BRAF", "TP53", "ROS1"}
PRODUCTION_BASE_URL = "https://www.oncokb.org/api/v1"


def _resolve_base_url(gene: str) -> str:
    if ONCOKB_API_TOKEN:
        return PRODUCTION_BASE_URL
    if gene.upper() in DEMO_GENES:
        return ONCOKB_DEMO_URL
    return ONCOKB_PUBLIC_URL


def _auth_headers() -> dict[str, str]:
    if ONCOKB_API_TOKEN:
        return {"Authorization": f"Bearer {ONCOKB_API_TOKEN}"}
    return {}


def annotate_mutation(gene: str, alteration: str, timeout: int = 8) -> dict[str, Any] | None:
    """
    Query OncoKB for live variant annotation.

    Uses production API when ONCOKB_API_TOKEN is set, demo API for BRAF/TP53/ROS1,
    otherwise falls back to the public API (limited therapeutic data).
    """
    base_url = _resolve_base_url(gene)
    endpoint = f"{base_url}/annotate/mutations/byProteinChange"
    params = {"hugoSymbol": gene, "alteration": alteration}

    try:
        response = requests.get(
            endpoint,
            params=params,
            headers=_auth_headers(),
            timeout=timeout,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("OncoKB request failed for %s %s: %s", gene, alteration, exc)
        return None


def build_oncokb_evidence_entry(
    annotation: dict[str, Any],
    step: int,
    gene: str,
) -> dict[str, Any]:
    """Convert an OncoKB annotation payload into an evidence_timeline entry."""
    oncogenic = annotation.get("oncogenic") or "Unknown"
    sensitive_level = annotation.get("highestSensitiveLevel") or "Unknown"
    mutation_effect = annotation.get("mutationEffect") or "Unknown"

    treatments = annotation.get("treatments") or []
    treatment_names = []
    for group in treatments:
        for drug in group.get("drugs", []):
            name = drug.get("drugName")
            if name:
                treatment_names.append(name)

    therapy_text = ", ".join(treatment_names[:3]) if treatment_names else "See OncoKB"
    snippet = (
        f"OncoKB: {oncogenic} alteration with {mutation_effect} effect. "
        f"Highest sensitive level: {sensitive_level}. "
        f"Suggested therapies: {therapy_text}."
    )

    return {
        "step": step,
        "source_name": "OncoKB (Live API)",
        "assertion": f"{oncogenic} — Level {sensitive_level}",
        "evidence_id": f"OncoKB-{gene}-{annotation.get('alteration', 'variant')}",
        "confidence_score": 0.97 if sensitive_level not in ("Unknown", None) else 0.80,
        "url": f"https://www.oncokb.org/gene/{gene}",
        "snippet": snippet,
        "live": True,
    }


def enrich_evidence_with_oncokb(
    profile: dict,
    existing_evidence: list[dict],
) -> tuple[list[dict], str | None]:
    """
    Attempt to prepend a live OncoKB evidence entry.

    Returns updated evidence list and optional recommended therapy override.
    """
    gene = profile.get("gene")
    alteration = profile.get("protein_change") or profile.get("variant")
    if not gene or not alteration:
        return existing_evidence, None

    annotation = annotate_mutation(gene, alteration)
    if not annotation:
        return existing_evidence, None

    live_entry = build_oncokb_evidence_entry(annotation, step=0, gene=gene)
    merged = [live_entry] + [
        {**entry, "step": idx + 1} for idx, entry in enumerate(existing_evidence)
    ]

    therapy_override = None
    treatments = annotation.get("treatments") or []
    if treatments:
        drugs: list[str] = []
        for group in treatments:
            for drug in group.get("drugs", []):
                name = drug.get("drugName")
                if name and name not in drugs:
                    drugs.append(name)
        if drugs:
            therapy_override = " + ".join(drugs[:2])

    return merged, therapy_override
