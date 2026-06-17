"""Unit tests for genomic NER (regex path — no ML model required)."""
import pytest
from services.ner import extract_mutation_from_text, MutationDetection


class TestRegexNER:
    def test_braf_v600e_explicit(self):
        r = extract_mutation_from_text("BRAF V600E mutation detected in melanoma")
        assert r is not None
        assert r.profile_key == "BRAF V600E"
        assert r.gene == "BRAF"
        assert r.confidence >= 0.90

    def test_egfr_exon19_del(self):
        r = extract_mutation_from_text("EGFR exon 19 deletion confirmed in NSCLC")
        assert r is not None
        assert r.profile_key == "EGFR Exon 19 Del"
        assert r.gene == "EGFR"

    def test_egfr_l858r_alias(self):
        """L858R maps to the EGFR Exon 19 Del profile."""
        r = extract_mutation_from_text("EGFR L858R activating mutation")
        assert r is not None
        assert r.profile_key == "EGFR Exon 19 Del"

    def test_kras_g12c(self):
        r = extract_mutation_from_text("KRAS G12C confirmed variant")
        assert r is not None
        assert r.profile_key == "KRAS G12C"
        assert r.gene == "KRAS"

    def test_alk_fusion_full(self):
        r = extract_mutation_from_text("EML4-ALK fusion rearrangement detected by FISH")
        assert r is not None
        assert r.profile_key == "EML4-ALK Fusion"
        assert r.gene == "ALK"

    def test_alk_fusion_short(self):
        r = extract_mutation_from_text("ALK fusion positive NSCLC")
        assert r is not None
        assert r.profile_key == "EML4-ALK Fusion"

    def test_no_mutation_returns_none(self):
        r = extract_mutation_from_text("Routine blood panel, no abnormalities")
        assert r is None

    def test_empty_string_returns_none(self):
        assert extract_mutation_from_text("") is None

    def test_whitespace_returns_none(self):
        assert extract_mutation_from_text("   ") is None

    def test_returns_mutation_detection_dataclass(self):
        r = extract_mutation_from_text("BRAF V600E")
        assert isinstance(r, MutationDetection)
        assert r.profile_key
        assert r.gene
        assert r.variant
        assert 0.0 < r.confidence <= 1.0
        assert r.method

    def test_gene_only_low_confidence(self):
        """Gene-only mention resolves but with lower confidence."""
        r = extract_mutation_from_text("BRAF gene analysis pending")
        assert r is not None
        assert r.profile_key == "BRAF V600E"
        assert r.confidence < 0.85

    def test_case_insensitive(self):
        r = extract_mutation_from_text("braf v600e positive melanoma")
        assert r is not None
        assert r.profile_key == "BRAF V600E"

    def test_v600e_without_braf(self):
        """V600E alone still resolves to BRAF."""
        r = extract_mutation_from_text("V600E substitution confirmed")
        assert r is not None
        assert r.profile_key == "BRAF V600E"
