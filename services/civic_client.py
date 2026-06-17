"""CIViC GraphQL client — free open-access therapeutic evidence."""

from __future__ import annotations

import logging
from typing import Any

import requests

from services.config import CIVIC_GRAPHQL_URL

logger = logging.getLogger(__name__)

MOLECULAR_PROFILE_QUERY = """
query MolecularProfile($name: String!) {
  molecularProfiles(name: $name) {
    nodes {
      id
      name
      evidenceItems {
        nodes {
          id
          description
          evidenceLevel
          significance
          evidenceType
          therapies {
            name
          }
        }
      }
    }
  }
}
"""


def _graphql(query: str, variables: dict[str, Any]) -> dict[str, Any] | None:
    try:
        resp = requests.post(
            CIVIC_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            timeout=12,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("errors"):
            logger.warning("CIViC GraphQL errors: %s", payload["errors"])
            return None
        return payload.get("data")
    except requests.RequestException as exc:
        logger.warning("CIViC request failed: %s", exc)
        return None


def _profile_search_names(gene: str, variant: str) -> list[str]:
    """Build candidate CIViC molecular profile names to query."""
    names = []
    if variant and variant.lower() not in ("detected", "fusion"):
        names.append(f"{gene} {variant}")
    if "V600" in variant.upper():
        names.append(f"{gene} V600E")
    if "exon" in variant.lower():
        names.append(f"{gene} Exon 19 Deletion")
        names.append("EGFR Exon 19 Deletion")
    if "fusion" in variant.lower() or gene == "ALK":
        names.append("EML4-ALK Fusion")
        names.append(f"{gene} Fusion")
    names.append(gene)
    # Deduplicate preserving order
    seen = set()
    unique = []
    for n in names:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    return unique


def fetch_civic_evidence(gene: str, variant: str) -> tuple[list[dict[str, Any]], str | None]:
    """
    Query CIViC for therapeutic evidence via free GraphQL API.

    Returns (evidence_entries, optional_therapy_override).
    """
    evidence_entries: list[dict[str, Any]] = []
    therapies: list[str] = []

    for profile_name in _profile_search_names(gene, variant):
        data = _graphql(MOLECULAR_PROFILE_QUERY, {"name": profile_name})
        if not data:
            continue

        nodes = (data.get("molecularProfiles") or {}).get("nodes") or []
        if not nodes:
            continue

        for profile in nodes:
            items = (profile.get("evidenceItems") or {}).get("nodes") or []
            for item in items[:4]:
                if item.get("significance") not in (
                    "SENSITIVITYRESPONSE",
                    "POSITIVE",
                    None,
                ) and not item.get("therapies"):
                    continue

                item_therapies = [
                    t["name"] for t in (item.get("therapies") or []) if t.get("name")
                ]
                therapies.extend(item_therapies)
                evidence_entries.append(
                    {
                        "step": 0,
                        "source_name": "CIViC (GraphQL API)",
                        "assertion": (
                            f"{item.get('significance', 'N/A')} — "
                            f"Level {item.get('evidenceLevel', 'N/A')}"
                        ),
                        "evidence_id": f"CIViC-{item.get('id', 'unknown')}",
                        "confidence_score": 0.92,
                        "url": f"https://civicdb.org/links/molecular_profile/{profile.get('id', '')}",
                        "snippet": (item.get("description") or profile.get("name", ""))[:280],
                        "live": True,
                    }
                )

        if evidence_entries:
            break

    therapy_override = None
    if therapies:
        unique = []
        for t in therapies:
            if t not in unique:
                unique.append(t)
        therapy_override = " + ".join(unique[:2])

    return evidence_entries[:4], therapy_override
