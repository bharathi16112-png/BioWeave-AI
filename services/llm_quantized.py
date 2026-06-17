"""
AWQ / GPTQ quantized LLM loader for AMD MI300X / ROCm.

Loads Meta-Llama-3-8B-Instruct (or any compatible model) in 4-bit quantized
form using AutoAWQ (preferred on ROCm) or AutoGPTQ (CUDA fallback), reducing
VRAM from ~16GB to ~5-6GB while maintaining response quality.

Requirements (install separately — not in requirements.txt base):
    ROCm/AMD path:
        pip install autoawq          # ROCm-native 4-bit kernels
    NVIDIA path:
        pip install auto-gptq        # GPTQ 4-bit, well-tested on CUDA
    Fallback (any GPU, slower):
        pip install bitsandbytes     # BnB NF4 quantization

Environment variables:
    BIOWEAVE_LLM_MODEL       — HuggingFace model ID or local path
    BIOWEAVE_LLM_QUANT       — "awq" | "gptq" | "bnb" | "none" (default: auto)
    BIOWEAVE_LLM_MAX_TOKENS  — max new tokens per inference call (default: 150)

Usage:
    from services.llm_quantized import get_quantized_llm, generate_rationale
    llm = get_quantized_llm()              # loads once, cached
    text, n_tokens = generate_rationale(llm, mutation, pathway, drug, excerpt)
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_ID = os.environ.get("BIOWEAVE_LLM_MODEL", "")
_QUANT_MODE = os.environ.get("BIOWEAVE_LLM_QUANT", "auto").lower()
_MAX_NEW_TOKENS = int(os.environ.get("BIOWEAVE_LLM_MAX_TOKENS", "150"))


def _detect_quant_backend() -> str:
    """Auto-detect the best available quantization backend."""
    if _QUANT_MODE != "auto":
        return _QUANT_MODE

    try:
        import autoawq  # noqa: F401
        return "awq"
    except ImportError:
        pass

    try:
        import auto_gptq  # noqa: F401
        return "gptq"
    except ImportError:
        pass

    try:
        import bitsandbytes  # noqa: F401
        return "bnb"
    except ImportError:
        pass

    return "none"


@lru_cache(maxsize=1)
def get_quantized_llm() -> Any | None:
    """
    Load and cache a quantized LLM pipeline.

    Returns None if no model is configured or if loading fails.
    The caller is responsible for checking for None before use.
    """
    if not _MODEL_ID:
        logger.info("BIOWEAVE_LLM_MODEL not set — quantized LLM disabled.")
        return None

    import torch
    if not torch.cuda.is_available():
        logger.warning(
            "No GPU detected. Quantized LLM inference requires CUDA/ROCm. "
            "Set BIOWEAVE_LLM_MODEL only on GPU-equipped machines."
        )
        return None

    backend = _detect_quant_backend()
    logger.info("Loading %s with quantization backend: %s", _MODEL_ID, backend)

    try:
        if backend == "awq":
            return _load_awq(_MODEL_ID)
        if backend == "gptq":
            return _load_gptq(_MODEL_ID)
        if backend == "bnb":
            return _load_bnb(_MODEL_ID)
        # backend == "none" or unknown — load in fp16 without quantization
        return _load_fp16(_MODEL_ID)
    except Exception as exc:
        logger.error("Quantized LLM load failed (%s): %s", backend, exc)
        return None


def _load_awq(model_id: str) -> Any:
    """Load model with AutoAWQ 4-bit quantization (best on ROCm/MI300X)."""
    from awq import AutoAWQForCausalLM
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoAWQForCausalLM.from_quantized(
        model_id,
        fuse_layers=True,
        trust_remote_code=False,
        safetensors=True,
    )
    logger.info("AWQ model loaded: %s (VRAM: ~5-6 GB)", model_id)
    return {"model": model, "tokenizer": tokenizer, "backend": "awq"}


def _load_gptq(model_id: str) -> Any:
    """Load model with AutoGPTQ 4-bit quantization."""
    from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoGPTQForCausalLM.from_quantized(
        model_id,
        use_safetensors=True,
        device="cuda:0",
        inject_fused_attention=True,
    )
    logger.info("GPTQ model loaded: %s", model_id)
    return {"model": model, "tokenizer": tokenizer, "backend": "gptq"}


def _load_bnb(model_id: str) -> Any:
    """Load model with BitsAndBytes NF4 4-bit quantization (fallback)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
    )
    logger.info("BnB NF4 model loaded: %s", model_id)
    return {"model": model, "tokenizer": tokenizer, "backend": "bnb"}


def _load_fp16(model_id: str) -> Any:
    """Load model in fp16 without quantization (requires full VRAM)."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    logger.info("fp16 model loaded: %s (no quantization)", model_id)
    return {"model": model, "tokenizer": tokenizer, "backend": "fp16"}


def generate_rationale(
    llm_bundle: dict,
    mutation: str,
    pathway: str,
    drug: str,
    report_excerpt: str,
    base_rationale: str,
) -> tuple[str, int]:
    """
    Generate an LLM rationale using a quantized model bundle.

    Returns (rationale_text, tokens_generated).
    Falls back to base_rationale on any error.
    """
    if llm_bundle is None:
        return base_rationale, 0

    backend = llm_bundle.get("backend", "unknown")
    model = llm_bundle["model"]
    tokenizer = llm_bundle["tokenizer"]

    prompt = (
        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        "You are a precision oncology assistant. Write a concise 2-sentence "
        "therapeutic rationale for a clinician. Use only evidence from the context.\n"
        "<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
        f"Mutation: {mutation}\n"
        f"Pathway: {pathway}\n"
        f"Drug: {drug}\n"
        f"Report excerpt: {report_excerpt[:400]}\n"
        f"Baseline rationale: {base_rationale}\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )

    try:
        import torch

        if backend == "awq":
            # AWQ uses generate() directly
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=_MAX_NEW_TOKENS,
                    do_sample=False,
                    temperature=1.0,
                    pad_token_id=tokenizer.eos_token_id,
                )
            text = tokenizer.decode(
                output[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()
        else:
            # GPTQ / BnB / fp16 — use transformers pipeline
            from transformers import pipeline as hf_pipeline
            pipe = hf_pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=_MAX_NEW_TOKENS,
                do_sample=False,
                return_full_text=False,
            )
            result = pipe(prompt)
            text = result[0]["generated_text"].strip()

        n_tokens = len(tokenizer.encode(text))
        logger.info("LLM (%s) generated %d tokens", backend, n_tokens)
        return text or base_rationale, n_tokens

    except Exception as exc:
        logger.error("LLM generation failed (%s): %s", backend, exc)
        return base_rationale, 0
