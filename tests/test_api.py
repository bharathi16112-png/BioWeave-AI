"""FastAPI endpoint tests using httpx TestClient."""
import pytest

pytest.importorskip("fastapi", reason="fastapi not installed")
pytest.importorskip("httpx", reason="httpx not installed")

from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_ok(self, client):
        data = resp = client.get("/health").json()
        assert data.get("status") == "ok"

    def test_health_has_compute_key(self, client):
        data = client.get("/health").json()
        assert "compute" in data
        assert "gpu_hardware" in data["compute"]


class TestDemoProfiles:
    def test_list_profiles_200(self, client):
        resp = client.get("/demo-profiles")
        assert resp.status_code == 200

    def test_list_profiles_has_profiles_key(self, client):
        data = client.get("/demo-profiles").json()
        assert "profiles" in data
        assert len(data["profiles"]) >= 4

    def test_get_profile_braf(self, client):
        resp = client.get("/demo-profiles/BRAF V600E")
        assert resp.status_code == 200
        data = resp.json()
        assert "executive_summary" in data

    def test_get_profile_404(self, client):
        resp = client.get("/demo-profiles/NONEXISTENT_XYZ")
        assert resp.status_code == 404


class TestAnalyzeText:
    def test_braf_text_returns_200(self, client):
        resp = client.post(
            "/analyze/text",
            json={"genomic_report": "BRAF V600E mutation detected in melanoma"},
        )
        assert resp.status_code == 200

    def test_braf_mutation_in_response(self, client):
        resp = client.post(
            "/analyze/text",
            json={"genomic_report": "BRAF V600E confirmed"},
        )
        data = resp.json()
        assert data["executive_summary"]["mutation"] == "BRAF V600E"

    def test_insufficient_returns_200_not_500(self, client):
        """Unknown report is valid — returns insufficient_evidence, not a 500."""
        resp = client.post(
            "/analyze/text",
            json={"genomic_report": "Routine blood test, all normal"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analysis_status"]["analysis_state"] == "insufficient_evidence"

    def test_empty_report_returns_422(self, client):
        """Empty string fails Pydantic min_length=1 validation."""
        resp = client.post("/analyze/text", json={"genomic_report": ""})
        assert resp.status_code == 422

    def test_all_four_mutations(self, client):
        cases = [
            ("BRAF V600E melanoma", "BRAF V600E"),
            ("EGFR exon 19 deletion NSCLC", "EGFR Exon 19 Del"),
            ("KRAS G12C confirmed", "KRAS G12C"),
            ("EML4-ALK fusion positive", "EML4-ALK Fusion"),
        ]
        for report, expected in cases:
            resp = client.post("/analyze/text", json={"genomic_report": report})
            assert resp.status_code == 200
            assert resp.json()["executive_summary"]["mutation"] == expected

    def test_response_has_docking_key(self, client):
        resp = client.post(
            "/analyze/text",
            json={"genomic_report": "KRAS G12C mutation"},
        )
        data = resp.json()
        pie = data.get("pathway_intervention_engine", {})
        assert "docking" in pie


class TestAnalyzeMultimodal:
    def test_text_only_multimodal(self, client):
        resp = client.post(
            "/analyze/multimodal",
            data={"genomic_report": "EGFR exon 19 deletion confirmed"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["executive_summary"]["mutation"] == "EGFR Exon 19 Del"
