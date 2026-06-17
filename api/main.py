"""
FastAPI backend — self-hosted REST API for BioWeave-AI.

Phase 4 additions:
  - API key authentication (Bearer token, optional via BIOWEAVE_API_KEYS)
  - HIPAA-aligned audit logging middleware
  - /admin/generate-key endpoint for key provisioning
  - /admin/health-detail endpoint (auth-protected)
"""
from __future__ import annotations

import io
import logging
import time

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.auth import require_api_key, generate_api_key
from pipeline import run_multi_agent_pipeline
from services.audit_log import get_audit_logger
from services.hardware import detect_compute_environment
from utils.data_loader import get_available_mutations, load_profile

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BioWeave-AI API",
    description=(
        "Precision oncology multi-agent inference API. "
        "Research and demonstration use only — not FDA-cleared."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Audit logging middleware ──────────────────────────────────────────────────

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log every API request to the HIPAA audit trail."""
    t0 = time.perf_counter()
    response = await call_next(request)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    # Extract opaque user identity (set by auth dependency if auth is enabled)
    user_id = getattr(request.state, "user_id", "anonymous")
    ip = request.client.host if request.client else "unknown"

    get_audit_logger().log_api_request(
        method=request.method,
        path=request.url.path,
        user_id=user_id,
        ip_address=ip,
        status_code=response.status_code,
        latency_ms=latency_ms,
    )
    return response


# ── Request / response models ────────────────────────────────────────────────

class AnalyzeTextRequest(BaseModel):
    genomic_report: str = Field(..., min_length=1, description="Raw genomic report text")


class HealthResponse(BaseModel):
    status: str
    compute: dict


class GenerateKeyResponse(BaseModel):
    api_key: str
    key_hash: str
    note: str


# ── Public endpoints (no auth required) ─────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    """Basic liveness check — no auth required."""
    return {"status": "ok", "compute": detect_compute_environment()}


@app.get("/demo-profiles", tags=["demo"])
def demo_profiles():
    """List available demo mutation profiles."""
    return {"profiles": get_available_mutations()}


@app.get("/demo-profiles/{profile_name}", tags=["demo"])
def get_demo_profile(profile_name: str):
    """Return a single demo mutation profile."""
    try:
        return load_profile(profile_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Inference endpoints (auth required when BIOWEAVE_API_KEYS is set) ────────

@app.post("/analyze/text", tags=["inference"])
def analyze_text(
    body: AnalyzeTextRequest,
    user_id: str = Depends(require_api_key),
):
    """Run text-only genomic report analysis."""
    result = run_multi_agent_pipeline(body.genomic_report)
    if not result:
        raise HTTPException(status_code=500, detail="Pipeline returned no result")

    get_audit_logger().log(
        action="pipeline_run",
        user_id=user_id,
        resource=result.get("executive_summary", {}).get("mutation", "unknown"),
        outcome=result.get("analysis_status", {}).get("analysis_state", "unknown"),
        details={
            "input_type": "text",
            "latency_ms": result.get("system_metrics", {}).get("total_latency_ms"),
            "docking_method": result.get("pathway_intervention_engine", {})
                .get("docking", {}).get("method"),
        },
    )
    return result


@app.post("/analyze/multimodal", tags=["inference"])
async def analyze_multimodal(
    genomic_report: str = Form(..., description="Required genomic report text"),
    slide_image: UploadFile | None = File(None, description="Optional pathology slide PNG/JPG"),
    user_id: str = Depends(require_api_key),
):
    """Run multimodal analysis (text + optional pathology image)."""
    image_file = None
    if slide_image and slide_image.filename:
        content = await slide_image.read()
        image_file = io.BytesIO(content)

    result = run_multi_agent_pipeline(genomic_report, uploaded_image=image_file)
    if not result:
        raise HTTPException(status_code=500, detail="Pipeline returned no result")

    get_audit_logger().log(
        action="pipeline_run",
        user_id=user_id,
        resource=result.get("executive_summary", {}).get("mutation", "unknown"),
        outcome=result.get("analysis_status", {}).get("analysis_state", "unknown"),
        details={
            "input_type": "multimodal" if image_file else "text",
            "has_image": image_file is not None,
            "latency_ms": result.get("system_metrics", {}).get("total_latency_ms"),
        },
    )
    return result


# ── Admin endpoints (always auth-required) ───────────────────────────────────

@app.get("/admin/health-detail", tags=["admin"])
def health_detail(user_id: str = Depends(require_api_key)):
    """Detailed system info — requires authentication."""
    from services.docking import is_vina_available, is_meeko_available
    from services.ner import _load_ml_ner_pipeline
    from services.config import (
        PATHOLOGY_VIT_MODEL, ML_NER_MODEL, LLM_MODEL,
        ENABLE_DOCKING, DOCKING_EXHAUSTIVENESS,
    )
    return {
        "status": "ok",
        "compute": detect_compute_environment(),
        "features": {
            "vina_available": is_vina_available(),
            "meeko_available": is_meeko_available(),
            "llm_configured": bool(LLM_MODEL),
            "docking_enabled": ENABLE_DOCKING,
            "docking_exhaustiveness": DOCKING_EXHAUSTIVENESS,
        },
        "models": {
            "pathology_vit": PATHOLOGY_VIT_MODEL,
            "ner_model": ML_NER_MODEL,
            "llm_model": LLM_MODEL or "not configured",
        },
    }


@app.post("/admin/generate-key", tags=["admin"])
def admin_generate_key(user_id: str = Depends(require_api_key)):
    """
    Generate a new API key pair.

    Returns the plain key (share with consumer) and its hash (store in
    BIOWEAVE_API_KEYS). The plain key is shown only once — store it safely.
    """
    plain, key_hash = generate_api_key()
    get_audit_logger().log(
        action="api_key_generated",
        user_id=user_id,
        resource="api_key",
        outcome="completed",
    )
    return GenerateKeyResponse(
        api_key=plain,
        key_hash=key_hash,
        note=(
            "Add the key_hash to BIOWEAVE_API_KEYS (comma-separated). "
            "Give the api_key to your consumer. It is shown only once."
        ),
    )
