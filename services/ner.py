"""Genomic text entity extraction — regex fast path + optional free OpenMed NER."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from services.config import DISABLE_ML, ML_NER_MODEL, USE_ML_NER

logger = logging.getLogger(__name__)


@dataclass
class MutationDetection:
    profile_key: str
    gene: str
    variant: str
    confidence: float
    method: str
    matched_text: str | None = None


_GENE_TO_PROFILE = {
    "BRAF": "BRAF V600E",
    "EGFR": "EGFR Exon 19 Del",
    "KRAS": "KRAS G12C",
    "ALK": "EML4-ALK Fusion",
    "EML4": "EML4-ALK Fusion",
}

_VARIANT_PATTERNS: list[tuple[re.Pattern, str, str, str, float]] = [
    (
        re.compile(r"EML4[\s\-]?ALK|ALK\s+fusion|ALK\s+rearrangement", re.I),
        "EML4-ALK Fusion", "ALK", "EML4-ALK Fusion", 0.96,
    ),
    (
        re.compile(r"exon\s*19\s*(?:del(?:etion)?|deletion)", re.I),
        "EGFR Exon 19 Del", "EGFR", "Exon 19 Deletion", 0.95,
    ),
    (
        re.compile(r"\bBRAF\b.*\bV600E\b|\bV600E\b.*\bBRAF\b", re.I),
        "BRAF V600E", "BRAF", "V600E", 0.94,
    ),
    (
        re.compile(r"\bKRAS\b.*\bG12C\b|\bG12C\b.*\bKRAS\b", re.I),
        "KRAS G12C", "KRAS", "G12C", 0.94,
    ),
    (
        re.compile(r"\bEGFR\b.*\bL858R\b|\bL858R\b.*\bEGFR\b", re.I),
        "EGFR Exon 19 Del", "EGFR", "L858R", 0.92,
    ),
    (
        re.compile(r"\bV600E\b|\bV600K\b", re.I),
        "BRAF V600E", "BRAF", "V600E", 0.88,
    ),
    (
        re.compile(r"\bG12C\b|\bG12D\b|\bG12V\b", re.I),
        "KRAS G12C", "KRAS", "G12C", 0.86,
    ),
    (
        re.compile(r"\bBRAF\b", re.I),
        "BRAF V600E", "BRAF", "V600E", 0.72,
    ),
    (
        re.compile(r"\bEGFR\b", re.I),
        "EGFR Exon 19 Del", "EGFR", "Exon 19 Deletion", 0.70,
    ),
    (
        re.compile(r"\bKRAS\b|\bNRAS\b", re.I),
        "KRAS G12C", "KRAS", "G12C", 0.68,
    ),
    (
        re.compile(r"\bALK\b|\bMET\b", re.I),
        "EML4-ALK Fusion", "ALK", "Fusion", 0.65,
    ),
]


def _extract_regex(text: str) -> MutationDetection | None:
    for pattern, profile_key, gene, variant, confidence in _VARIANT_PATTERNS:
        match = pattern.search(text)
        if match:
            return MutationDetection(
                profile_key=profile_key,
                gene=gene,
                variant=variant,
                confidence=confidence,
                method="regex_ner",
                matched_text=match.group(0),
            )
    return None


@lru_cache(maxsize=1)
def _load_ml_ner_pipeline():
    from transformers import pipeline

    return pipeline(
        "token-classification",
        model=ML_NER_MODEL,
        aggregation_strategy="simple",
    )


def _extract_ml_ner(text: str) -> MutationDetection | None:
    if DISABLE_ML or not USE_ML_NER:
        return None
    try:
        ner = _load_ml_ner_pipeline()
        entities = ner(text[:1500])
    except Exception as exc:
        logger.warning("ML NER unavailable, using regex only: %s", exc)
        return None

    genes_found: list[str] = []
    for ent in entities:
        label = (ent.get("entity_group") or ent.get("entity") or "").upper()
        word = ent.get("word", "").replace("##", "").strip()
        if not word:
            continue
        if "GENE" in label or label in ("B-GENE", "I-GENE"):
            genes_found.append(word.upper())

    text_upper = text.upper()
    for pattern, profile_key, gene, variant, confidence in _VARIANT_PATTERNS:
        if pattern.search(text):
            return MutationDetection(
                profile_key=profile_key,
                gene=gene,
                variant=variant,
                confidence=min(0.98, confidence + 0.03),
                method="openmed_ner+regex",
                matched_text=pattern.search(text).group(0),
            )

    for g in genes_found:
        if g in _GENE_TO_PROFILE:
            return MutationDetection(
                profile_key=_GENE_TO_PROFILE[g],
                gene=g,
                variant="detected",
                confidence=0.68,
                method="openmed_ner",
                matched_text=g,
            )

    return None


def extract_mutation_from_text(text: str) -> MutationDetection | None:
    """Extract mutation using ML NER (if available) with regex fallback."""
    if not text or not text.strip():
        return None

    ml_result = _extract_ml_ner(text)
    regex_result = _extract_regex(text)

    if ml_result and regex_result:
        if ml_result.profile_key == regex_result.profile_key:
            return MutationDetection(
                profile_key=ml_result.profile_key,
                gene=ml_result.gene,
                variant=regex_result.variant,
                confidence=min(0.98, max(ml_result.confidence, regex_result.confidence) + 0.04),
                method="openmed_ner+regex_consensus",
                matched_text=regex_result.matched_text,
            )
        if regex_result.confidence >= ml_result.confidence:
            return regex_result
        return ml_result

    return regex_result or ml_result
