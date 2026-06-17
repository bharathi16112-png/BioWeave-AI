"""Integration tests for the three-agent pipeline."""
import pytest

REQUIRED_TOP_KEYS = [
    "analysis_status", "executive_summary", "metadata",
    "system_metrics", "agent_trace", "graph_data",
    "pathway_intervention_engine", "why_not_exclusion_panel",
    "evidence_timeline",
]

REQUIRED_DOCKING_KEYS = [
    "method", "binding_affinity_kcal_mol",
    "pathway_suppression", "is_fallback",
]


class TestPipelineSchema:
    def test_braf_has_all_top_keys(self, pipeline_braf):
        missing = [k for k in REQUIRED_TOP_KEYS if k not in pipeline_braf]
        assert not missing, f"Missing top-level keys: {missing}"

    def test_braf_analysis_completed(self, pipeline_braf):
        assert pipeline_braf["analysis_status"]["analysis_state"] == "completed"

    def test_braf_mutation_identified(self, pipeline_braf):
        assert pipeline_braf["executive_summary"]["mutation"] == "BRAF V600E"

    def test_braf_confidence_range(self, pipeline_braf):
        c = pipeline_braf["executive_summary"]["confidence"]
        assert 0.0 < c <= 1.0, f"Confidence {c} out of range"

    def test_braf_has_graph_nodes(self, pipeline_braf):
        nodes = pipeline_braf["graph_data"]["nodes"]
        assert len(nodes) >= 5, "Expected at least 5 pathway nodes"

    def test_braf_has_edges(self, pipeline_braf):
        edges = pipeline_braf["graph_data"]["edges"]
        assert len(edges) >= 4

    def test_braf_agent_trace_has_three_agents(self, pipeline_braf):
        agents = [a["agent_name"] for a in pipeline_braf["agent_trace"]]
        assert "Molecular Detective" in agents
        assert "Pathway Pathologist" in agents
        assert "Therapeutic Matchmaker" in agents

    def test_braf_all_agents_completed(self, pipeline_braf):
        for agent in pipeline_braf["agent_trace"]:
            assert agent["status"] == "completed", f"{agent['agent_name']} not completed"

    def test_braf_patient_id_format(self, pipeline_braf):
        pid = pipeline_braf["metadata"]["patient_id"]
        assert pid.startswith("LIVE-"), f"Unexpected patient_id: {pid}"

    def test_braf_has_exclusions(self, pipeline_braf):
        excl = pipeline_braf["why_not_exclusion_panel"]
        assert len(excl) >= 1

    def test_braf_has_evidence(self, pipeline_braf):
        evid = pipeline_braf["evidence_timeline"]
        assert len(evid) >= 1

    def test_braf_docking_subkey_present(self, pipeline_braf):
        pie = pipeline_braf["pathway_intervention_engine"]
        assert "docking" in pie, "pathway_intervention_engine missing 'docking' key"

    def test_braf_docking_keys_complete(self, pipeline_braf):
        docking = pipeline_braf["pathway_intervention_engine"]["docking"]
        missing = [k for k in REQUIRED_DOCKING_KEYS if k not in docking]
        assert not missing, f"Missing docking keys: {missing}"

    def test_braf_docking_affinity_negative(self, pipeline_braf):
        affinity = pipeline_braf["pathway_intervention_engine"]["docking"]["binding_affinity_kcal_mol"]
        assert affinity < 0, f"Binding affinity should be negative, got {affinity}"

    def test_braf_suppression_range(self, pipeline_braf):
        s = pipeline_braf["pathway_intervention_engine"]["docking"]["pathway_suppression"]
        assert 0.0 < s < 1.0, f"Suppression {s} out of range"

    def test_braf_baseline_exceeds_post(self, pipeline_braf):
        pie = pipeline_braf["pathway_intervention_engine"]
        baseline = pie["baseline_pathway_activity_score"]
        post = pie["predicted_post_intervention_activity_score"]
        assert baseline > post, "Baseline should exceed post-intervention score"

    def test_braf_system_metrics_keys(self, pipeline_braf):
        sm = pipeline_braf["system_metrics"]
        for key in ("gpu_hardware", "compute_platform", "total_latency_ms", "vina_enabled"):
            assert key in sm, f"system_metrics missing '{key}'"

    def test_braf_latency_positive(self, pipeline_braf):
        ms = pipeline_braf["system_metrics"]["total_latency_ms"]
        assert ms >= 0

    def test_egfr_mutation_identified(self, pipeline_egfr):
        assert pipeline_egfr["executive_summary"]["mutation"] == "EGFR Exon 19 Del"

    def test_egfr_drug_assigned(self, pipeline_egfr):
        drug = pipeline_egfr["executive_summary"]["recommended_therapy"]
        assert drug and drug != "N/A"


class TestInsufficientEvidence:
    def test_unknown_text_returns_insufficient(self):
        from pipeline import run_multi_agent_pipeline
        result = run_multi_agent_pipeline("Patient is healthy. No known mutations.")
        assert result["analysis_status"]["analysis_state"] == "insufficient_evidence"

    def test_insufficient_mutation_label(self):
        from pipeline import run_multi_agent_pipeline
        result = run_multi_agent_pipeline("unrelated text")
        assert result["executive_summary"]["mutation"] == "Insufficient Evidence"

    def test_image_only_blocked(self):
        from pipeline import run_multi_agent_pipeline
        result = run_multi_agent_pipeline("", uploaded_image=object())
        assert result["analysis_status"]["analysis_state"] == "insufficient_evidence"

    def test_insufficient_still_has_agent_trace(self):
        from pipeline import run_multi_agent_pipeline
        result = run_multi_agent_pipeline("no markers here")
        assert len(result["agent_trace"]) == 3


class TestAllMutations:
    @pytest.mark.parametrize("report,expected_key", [
        ("BRAF V600E confirmed melanoma", "BRAF V600E"),
        ("EGFR exon 19 deletion NSCLC", "EGFR Exon 19 Del"),
        ("KRAS G12C mutation RAS pathway", "KRAS G12C"),
        ("EML4-ALK fusion rearrangement", "EML4-ALK Fusion"),
    ])
    def test_mutation_detection(self, report, expected_key):
        from pipeline import run_multi_agent_pipeline
        result = run_multi_agent_pipeline(report)
        assert result["executive_summary"]["mutation"] == expected_key
