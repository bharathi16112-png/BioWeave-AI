"""Optional local LLM enrichment for agent rationales."""

from __future__ import annotations

import logging

from services.config import LLM_MODEL

logger = logging.getLogger(__name__)


def is_llm_enabled() -> bool:
    return bool(LLM_MODEL)


def enrich_therapeutic_rationale(
    mutation: str,
    pathway: str,
    drug: str,
    report_excerpt: str,
    base_rationale: str,
) -> tuple[str, int]:
    """
    Optionally rewrite the therapeutic rationale with a local LLM.

    Returns (rationale_text, tokens_generated). Falls back to base_rationale
    when BIOWEAVE_LLM_MODEL is not configured or loading fails.
    """
    model_name = LLM_MODEL
    if not model_name:
        return base_rationale, 0

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        device = 0 if torch.cuda.is_available() else -1
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        llm = pipeline(
            "text-generation",
            model=AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
            ),
            tokenizer=tokenizer,
            device=device,
        )

        prompt = (
            "You are a precision oncology assistant. Write a concise 2-sentence "
            "therapeutic rationale for a clinician. Do not invent new drugs.\n"
            f"Mutation: {mutation}\n"
            f"Pathway: {pathway}\n"
            f"Recommended therapy: {drug}\n"
            f"Report excerpt: {report_excerpt[:400]}\n"
            f"Baseline rationale: {base_rationale}\n"
            "Rationale:"
        )

        result = llm(
            prompt,
            max_new_tokens=120,
            do_sample=False,
            return_full_text=False,
        )
        text = result[0]["generated_text"].strip()
        tokens = len(tokenizer.encode(text))
        if text:
            return text, tokens
    except Exception as exc:
        logger.warning("LLM enrichment unavailable: %s", exc)

    return base_rationale, 0
