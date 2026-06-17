"""
pipeline.py — Precision Oncology Multi-Agent Inference Pipeline
================================================================
Loads Meta-Llama-3-8B-Instruct directly onto the AMD Instinct MI300X
via native ROCm/HIP ↔ PyTorch CUDA compatibility layer, then drives a
structured extraction prompt to produce the JSON schema consumed by
every dashboard component.

Hardware path
─────────────
ROCm exposes MI300X to PyTorch via the CUDA compat layer, so
`torch.cuda.is_available()` returns True on a correctly configured
ROCm stack and `device_map="auto"` routes all layers to VRAM.

Usage
─────
    from pipeline import run_multi_agent_pipeline
    profile_data = run_multi_agent_pipeline(raw_report_text)
"""

import json
import time
import logging

import torch
import streamlit as st
from transformers import pipeline as hf_pipeline

logger = logging.getLogger(__name__)

# ── Model identifier ──────────────────────────────────────────────────────────
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

# ── Maximum tokens the model should generate ─────────────────────────────────
MAX_NEW_TOKENS = 1200


# ─────────────────────────────────────────────────────────────────────────────
# Device resolution
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_device() -> str:
    """
    Returns the best available compute device.

    On an AMD MI300X with ROCm ≥ 6.x installed the PyTorch CUDA
    compatibility shim maps HIP → CUDA API, so cuda:0 is the MI300X.
    Falls back to CPU with a warning if no GPU is found.
    """
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        vram_total  = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        logger.info(
            "GPU detected: %s | VRAM: %.1f GB | ROCm/CUDA path active",
            device_name, vram_total,
        )
        return "cuda"

    logger.warning(
        "No CUDA/ROCm device found — falling back to CPU. "
        "Inference will be significantly slower."
    )
    return "cpu"


# ─────────────────────────────────────────────────────────────────────────────
# Model loader  (cached across Streamlit reruns)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_inference_model():
    """
    Loads Llama-3-8B-Instruct into MI300X VRAM using native
    PyTorch / HIP compilation via the ROCm CUDA compat layer.

    `device_map="auto"` + `torch_dtype=torch.float16` keeps the full
    8 B parameter model comfortably within a single MI300X's 192 GB
    HBM3 pool while maximising throughput.

    Returns
    -------
    transformers.Pipeline
        A text-generation pipeline bound to the resolved device.
    """
    device = _resolve_device()

    # On MI300X: float16 is optimal — bfloat16 also works on ROCm 6+
    dtype = torch.float16

    pipe = hf_pipeline(
        "text-generation",
        model=MODEL_ID,
        torch_dtype=dtype,
        device_map="auto",          # routes all layers to GPU VRAM
        model_kwargs={
            "low_cpu_mem_usage": True,   # stream weights from disk → GPU
        },
    )

    logger.info("Model %s loaded on %s", MODEL_ID, device.upper())
    return pipe


# ─────────────────────────────────────────────────────────────────────────────
# JSON extractor
# ─────────────────────────────────────────────────────────────────────────────

def _clean_json(raw: str) -> dict:
    """
    Parses JSON from model output, stripping any markdown fences the
    model may have wrapped around the payload despite instructions.

    Raises
    ------
    json.JSONDecodeError
        If the cleaned string still cannot be parsed.
    """
    text = raw.strip()

    # Strip ```json … ``` or ``` … ``` fences
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    # Find the outermost { … } block if the model prefixed a sentence
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    return json.loads(text)


# ─────────────────────────────────────────────────────────────────────────────
# Telemetry helper
# ─────────────────────────────────────────────────────────────────────────────

def _gpu_telemetry() -> dict:
    """Returns live VRAM and device stats for injection into system_metrics."""
    if not torch.cuda.is_available():
        return {
            "gpu_hardware":    "CPU (no GPU detected)",
            "compute_platform": "PyTorch CPU",
            "vram_allocated_gb": 0.0,
        }

    props        = torch.cuda.get_device_properties(0)
    allocated_gb = torch.cuda.memory_allocated(0) / (1024 ** 3)
    reserved_gb  = torch.cuda.memory_reserved(0)  / (1024 ** 3)

    return {
        "gpu_hardware":      props.name,
        "compute_platform":  f"ROCm / PyTorch {torch.__version__}",
        "vram_allocated_gb": round(allocated_gb, 2),
        "vram_reserved_gb":  round(reserved_gb,  2),
        "vram_total_gb":     round(props.total_memory / (1024 ** 3), 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# System prompt  (frozen schema — matches every dashboard component)
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are an advanced Precision Oncology Multi-Agent Reasoning Engine.

Analyze the raw clinical genomic report provided by the user and return a
**strictly formatted JSON string** matching the exact schema below.
Populate every field with values extracted or inferred from the report.

SCHEMA:
{
  "executive_summary": {
    "mutation":              "GENE VARIANT (e.g. BRAF V600E)",
    "clinical_significance": "Pathogenic | Likely Pathogenic | VUS | Benign",
    "affected_pathway":      "Primary signaling cascade name",
    "recommended_therapy":   "Approved drug or combination",
    "confidence":            0.00
  },
  "system_metrics": {
    "gpu_hardware":       "AMD Instinct MI300X",
    "compute_platform":   "ROCm v6.x Stack",
    "tokens_generated":   0,
    "total_latency_ms":   0,
    "vram_allocated_gb":  0.0
  },
  "agent_trace": [
    {
      "agent_name":   "Agent label",
      "status":       "completed | running | failed",
      "duration_ms":  0,
      "task":         "One-line description of reasoning step"
    }
  ],
  "graph_data": {
    "nodes": [
      {"id": "N1", "label": "Node label", "type": "mutation | protein | pathway_node | therapeutic | biological_outcome",
       "status": "active | inhibited | normal", "mechanism": "brief note"}
    ],
    "edges": [
      {"source": "N1", "target": "N2", "type": "genetic | signaling | intervention | phenotype",
       "relation": "relation_label", "confidence": 0.0}
    ]
  },
  "pathway_intervention_engine": {
    "baseline_pathway_activity_score":           0.00,
    "predicted_post_intervention_activity_score": 0.00,
    "therapeutic_rationale": "Mechanistic explanation"
  },
  "why_not_exclusion_panel": [
    {
      "drug":   "Drug name",
      "reason": "Clinical rationale for exclusion",
      "source": "Guideline or evidence reference"
    }
  ],
  "evidence_timeline": [
    {
      "year":     2000,
      "event":    "One-line description",
      "source":   "Citation or database",
      "type":     "discovery | approval | trial | publication"
    }
  ]
}

RULES:
- Output ONLY valid JSON — no markdown fences, no prose, no comments.
- Populate agent_trace with ≥ 3 reasoning steps reflecting actual analysis.
- graph_data must include the mutated gene, ≥ 1 downstream pathway node,
  ≥ 1 therapeutic node, and ≥ 2 edges.
- Scores are floats in [0, 1].
- evidence_timeline entries must be in chronological order.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def run_multi_agent_pipeline(raw_patient_report: str) -> dict | None:
    """
    Runs the full multi-agent oncology reasoning pipeline against a raw
    clinical text report.

    Parameters
    ----------
    raw_patient_report : str
        Free-text or structured clinical/genomic report to analyse.

    Returns
    -------
    dict | None
        Parsed profile_data dict (matches dashboard schema) on success,
        or None on unrecoverable error.
    """
    # ── 1. Load model ─────────────────────────────────────────────────
    try:
        pipe = load_inference_model()
    except Exception as exc:
        st.error(f"❌ Failed to initialise model on AMD hardware: {exc}")
        logger.exception("Model load failed")
        return None

    # ── 2. Build Llama-3 chat messages ────────────────────────────────
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Analyze the following clinical genomic report and return "
                f"the structured JSON output:\n\n{raw_patient_report}"
            ),
        },
    ]

    # Apply Llama-3 instruct chat template
    prompt = pipe.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    # ── 3. Inference on MI300X ────────────────────────────────────────
    t0 = time.perf_counter()
    with st.spinner("⚡ Processing genomic tensors on AMD MI300X…"):
        outputs = pipe(
            prompt,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            temperature=None,       # required when do_sample=False
            top_p=None,             # required when do_sample=False
            repetition_penalty=1.05,
        )
    latency_ms = int((time.perf_counter() - t0) * 1000)

    raw_output = outputs[0]["generated_text"][len(prompt):].strip()
    tokens_out = len(pipe.tokenizer.encode(raw_output))

    # ── 4. Parse JSON ─────────────────────────────────────────────────
    try:
        profile_data = _clean_json(raw_output)
    except json.JSONDecodeError as exc:
        st.error(
            f"⚠️ Model output could not be parsed as JSON: {exc}\n\n"
            f"Raw output preview:\n```\n{raw_output[:500]}\n```"
        )
        logger.error("JSON parse failure: %s\nRaw: %.500s", exc, raw_output)
        return None

    # ── 5. Patch system_metrics with live hardware telemetry ──────────
    telemetry = _gpu_telemetry()
    profile_data.setdefault("system_metrics", {}).update({
        **telemetry,
        "tokens_generated": tokens_out,
        "total_latency_ms": latency_ms,
    })

    return profile_data
