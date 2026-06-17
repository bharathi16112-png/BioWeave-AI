"""
pytest configuration and shared fixtures for BioWeave-AI.

Sets BIOWEAVE_DISABLE_ML=true globally so tests run fast without
downloading HuggingFace models. Individual tests that need ML can
override this via the `enable_ml` fixture.
"""
import os
import sys

# Disable ML model loading for fast unit tests
os.environ.setdefault("BIOWEAVE_DISABLE_ML", "true")
os.environ.setdefault("BIOWEAVE_CONTACT_EMAIL", "test@bioweave.test")

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(scope="session")
def braf_report():
    return "Patient biopsy confirms BRAF V600E mutation. Melanoma stage III."


@pytest.fixture(scope="session")
def egfr_report():
    return "EGFR exon 19 deletion detected in NSCLC tissue sample."


@pytest.fixture(scope="session")
def kras_report():
    return "Variant KRAS G12C confirmed in RAS pathway analysis."


@pytest.fixture(scope="session")
def alk_report():
    return "EML4-ALK fusion rearrangement detected by FISH."


@pytest.fixture(scope="session")
def unknown_report():
    return "Routine bloodwork. No known oncology markers."


@pytest.fixture(scope="session")
def all_mutations():
    return ["BRAF V600E", "EGFR Exon 19 Del", "KRAS G12C", "EML4-ALK Fusion"]


@pytest.fixture(scope="session")
def pipeline_braf(braf_report):
    """Run the pipeline once for BRAF and cache result."""
    from pipeline import run_multi_agent_pipeline
    return run_multi_agent_pipeline(braf_report)


@pytest.fixture(scope="session")
def pipeline_egfr(egfr_report):
    from pipeline import run_multi_agent_pipeline
    return run_multi_agent_pipeline(egfr_report)
