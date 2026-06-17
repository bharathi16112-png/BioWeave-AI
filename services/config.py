"""Central configuration — all integrations use free-tier defaults."""

from __future__ import annotations

import os

# ── Free public API endpoints (no payment required) ───────────────────────────
CLINVAR_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CIVIC_GRAPHQL_URL = "https://civicdb.org/api/graphql"
ONCOKB_DEMO_URL = "https://demo.oncokb.org/api/v1"
ONCOKB_PUBLIC_URL = "https://public.api.oncokb.org/api/v1"

# Optional free API keys (improve rate limits — not required)
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "8822d326fc42e73d38d0d378c35d16c12b08")
ONCOKB_API_TOKEN = os.environ.get("ONCOKB_API_TOKEN", "")

# Contact email for NCBI E-utilities etiquette
CONTACT_EMAIL = os.environ.get("BIOWEAVE_CONTACT_EMAIL", "bharathi16112@gmail.com")

# ── Free open-source models (HuggingFace, no auth for these) ──────────────────
PATHOLOGY_VIT_MODEL = os.environ.get("BIOWEAVE_PATHOLOGY_MODEL", "owkin/phikon")
ML_NER_MODEL = os.environ.get("BIOWEAVE_NER_MODEL", "OpenMed/OpenMed-NER-GenomicDetect-PubMed-109M")

# Feature flags
USE_ML_NER = os.environ.get("BIOWEAVE_USE_ML_NER", "true").lower() in ("1", "true", "yes")
DISABLE_ML = os.environ.get("BIOWEAVE_DISABLE_ML", "false").lower() in ("1", "true", "yes")
LLM_MODEL = os.environ.get("BIOWEAVE_LLM_MODEL", "")

# WSI / tiling
TILE_SIZE = int(os.environ.get("BIOWEAVE_TILE_SIZE", "224"))
MAX_TILES = int(os.environ.get("BIOWEAVE_MAX_TILES", "16"))

# ── AutoDock Vina docking settings ───────────────────────────────────────────
# Cache directory for downloaded receptor PDBQT files (~5MB per target)
DOCKING_CACHE_DIR = os.environ.get(
    "BIOWEAVE_DOCKING_CACHE",
    str(__import__("pathlib").Path.home() / ".cache" / "bioweave" / "docking"),
)

# Set to "false" to disable Vina docking (use curated scores instead)
ENABLE_DOCKING = os.environ.get("BIOWEAVE_ENABLE_DOCKING", "true").lower() in ("1", "true", "yes")

# Vina exhaustiveness (higher = more thorough but slower; 12 = good balance)
DOCKING_EXHAUSTIVENESS = int(os.environ.get("BIOWEAVE_DOCKING_EXHAUSTIVENESS", "12"))
