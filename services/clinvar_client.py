"""ClinVar lookup via free NCBI E-utilities API."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

import requests

from services.config import CLINVAR_EUTILS_BASE, CONTACT_EMAIL, NCBI_API_KEY

logger = logging.getLogger(__name__)


def _base_params() -> dict[str, str]:
    params = {"email": CONTACT_EMAIL, "tool": "BioWeave-AI"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    return params


def search_clinvar(gene: str, variant: str) -> list[str]:
    """Return ClinVar UIDs matching gene + variant term."""
    term = f"{gene}[gene] AND {variant}[variant name]"
    params = {
        **_base_params(),
        "db": "clinvar",
        "term": term,
        "retmax": "5",
        "retmode": "json",
    }
    try:
        resp = requests.get(f"{CLINVAR_EUTILS_BASE}/esearch.fcgi", params=params, timeout=10)
        resp.raise_for_status()
        ids = resp.json().get("esearchresult", {}).get("idlist", [])
        return ids
    except requests.RequestException as exc:
        logger.warning("ClinVar search failed: %s", exc)
        return []


def fetch_clinvar_summary(uid: str) -> dict[str, Any] | None:
    """Fetch ClinVar esummary for a UID."""
    params = {**_base_params(), "db": "clinvar", "id": uid, "retmode": "json"}
    try:
        resp = requests.get(f"{CLINVAR_EUTILS_BASE}/esummary.fcgi", params=params, timeout=10)
        resp.raise_for_status()
        result = resp.json().get("result", {})
        return result.get(uid)
    except requests.RequestException as exc:
        logger.warning("ClinVar summary failed for %s: %s", uid, exc)
        return None


def _parse_clinical_significance(summary: dict[str, Any]) -> str:
    desc = summary.get("clinical_significance", {}) or {}
    if isinstance(desc, dict):
        desc_list = desc.get("description", [])
        if desc_list:
            first = desc_list[0]
            return str(first.get("description", first) if isinstance(first, dict) else first)
    germline = summary.get("germline_classification")
    if isinstance(germline, dict):
        return str(germline.get("description", "Unknown"))
    if isinstance(germline, str):
        return germline
    return "Unknown"


def build_clinvar_evidence(gene: str, variant: str, step: int = 1) -> dict[str, Any] | None:
    """Build an evidence_timeline entry from live ClinVar data."""
    uids = search_clinvar(gene, variant)
    if not uids:
        uids = search_clinvar(gene, gene)
    if not uids:
        return None

    summary = fetch_clinvar_summary(uids[0])
    if not summary:
        return None

    title = summary.get("title", f"{gene} {variant}")
    significance = _parse_clinical_significance(summary)
    sig_text = significance.lower() if isinstance(significance, str) else str(significance).lower()
    accession = summary.get("accession_version") or summary.get("accession") or uids[0]
    url = f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{uids[0]}/"

    return {
        "step": step,
        "source_name": "ClinVar (NCBI E-utilities)",
        "assertion": f"Variant: {significance}",
        "evidence_id": str(accession),
        "confidence_score": 0.95 if "pathogenic" in sig_text else 0.75,
        "url": url,
        "snippet": title[:280],
        "live": True,
    }
