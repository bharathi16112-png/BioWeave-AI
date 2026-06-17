"""Unit tests for the clinical knowledge base and docking fallback."""
import pytest
from services.clinical_kb import get_profile, resolve_profile_key, MUTATION_PROFILES


class TestClinicalKB:
    def test_all_profiles_have_required_keys(self, all_mutations):
        required = [
            "gene", "variant", "family", "tumor_type", "pathway",
            "drug", "baseline", "post", "rationale", "nodes",
            "edges", "exclusions", "evidence",
        ]
        for key in all_mutations:
            profile = get_profile(key)
            missing = [k for k in required if k not in profile]
            assert not missing, f"{key} missing: {missing}"

    def test_baseline_gt_post_for_all(self, all_mutations):
        for key in all_mutations:
            p = get_profile(key)
            assert p["baseline"] > p["post"], f"{key}: baseline should exceed post"

    def test_scores_in_range(self, all_mutations):
        for key in all_mutations:
            p = get_profile(key)
            assert 0.0 < p["baseline"] <= 1.0
            assert 0.0 < p["post"] < p["baseline"]

    def test_alias_resolution_l858r(self):
        assert resolve_profile_key("EGFR L858R") == "EGFR Exon 19 Del"

    def test_alias_resolution_alk(self):
        assert resolve_profile_key("ALK Fusion") == "EML4-ALK Fusion"

    def test_canonical_key_unchanged(self):
        assert resolve_profile_key("BRAF V600E") == "BRAF V600E"

    def test_unknown_key_raises(self):
        with pytest.raises(KeyError):
            get_profile("NONEXISTENT_MUTATION_XYZ")

    def test_each_profile_has_nodes_and_edges(self, all_mutations):
        for key in all_mutations:
            p = get_profile(key)
            assert len(p["nodes"]) >= 4, f"{key} has too few nodes"
            assert len(p["edges"]) >= 3, f"{key} has too few edges"

    def test_evidence_steps_numbered(self, all_mutations):
        for key in all_mutations:
            p = get_profile(key)
            for i, ev in enumerate(p["evidence"], start=1):
                assert ev["step"] == i, f"{key} evidence step mismatch at index {i}"


class TestDockingFallback:
    def test_fallback_result_valid(self, all_mutations):
        from services.docking import _fallback_result
        for key in all_mutations:
            r = _fallback_result(key, "test")
            assert r.is_fallback
            assert r.binding_affinity_kcal_mol < 0
            assert 0.0 < r.pathway_suppression < 1.0
            assert r.baseline_score > r.post_intervention_score

    def test_sigmoid_monotone(self):
        from services.docking import _sigmoid_suppression
        scores = [-12.0, -10.0, -8.0, -6.0]
        suppressions = [_sigmoid_suppression(s) for s in scores]
        # More negative = stronger binding = higher suppression
        assert suppressions == sorted(suppressions, reverse=True), \
            "Suppression should increase as affinity becomes more negative"

    def test_sigmoid_bounds(self):
        from services.docking import _sigmoid_suppression
        for score in [-15.0, -12.0, -9.0, -6.0, -3.0]:
            s = _sigmoid_suppression(score)
            assert 0.0 <= s <= 1.0, f"Suppression {s} out of [0,1] for score {score}"

    def test_run_docking_returns_result_without_vina(self, all_mutations):
        """run_docking should always return a DockingResult, even without Vina."""
        from services.docking import run_docking, DockingResult
        for key in all_mutations:
            result = run_docking(key)
            assert isinstance(result, DockingResult)
            assert result.binding_affinity_kcal_mol < 0
            # Without Vina installed, must be a fallback
            assert result.method in ("autodock_vina", "static_fallback")
