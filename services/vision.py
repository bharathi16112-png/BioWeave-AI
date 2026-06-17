"""Pathology Vision Transformer (Phikon) feature extraction — free TCGA-pretrained model."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from functools import lru_cache

import torch
from PIL import Image

from services.config import DISABLE_ML, PATHOLOGY_VIT_MODEL
from services.wsi_tiler import SlideTile, extract_tiles

logger = logging.getLogger(__name__)

IMAGE_ONLY_MAX_CONFIDENCE = 0.55
MULTIMODAL_VISUAL_BOOST = 0.10


@dataclass
class VisualAnalysis:
    embedding_norm: float
    feature_entropy: float
    visual_confidence: float
    model_name: str
    tiles_processed: int
    method: str
    pathology_ready: bool = True


@lru_cache(maxsize=1)
def load_pathology_vit():
    """Load owkin/phikon — free pathology foundation model (TCGA, no auth)."""
    from transformers import AutoImageProcessor, ViTModel

    processor = AutoImageProcessor.from_pretrained(PATHOLOGY_VIT_MODEL)
    model = ViTModel.from_pretrained(PATHOLOGY_VIT_MODEL, add_pooling_layer=False)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    logger.info("Pathology ViT (%s) loaded on %s", PATHOLOGY_VIT_MODEL, device)
    return processor, model, device


def _embed_image(pil_image: Image.Image) -> torch.Tensor:
    processor, model, device = load_pathology_vit()
    inputs = processor(images=pil_image, return_tensors="pt")
    if device == "cuda":
        inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
        cls = outputs.last_hidden_state[:, 0, :]
    return cls.squeeze(0).cpu()


def _analyze_tiles(tiles: list[SlideTile]) -> VisualAnalysis | None:
    if DISABLE_ML:
        return None
    try:
        embeddings = [_embed_image(tile.image) for tile in tiles]
        stacked = torch.stack(embeddings)
        mean_emb = stacked.mean(dim=0)
        norms = torch.norm(stacked, dim=1)
        mean_norm = float(norms.mean().item())

        stacked_n = torch.nn.functional.normalize(stacked, dim=1)
        sim = stacked_n @ stacked_n.T
        avg_sim = float(sim.mean().item())
        entropy = float(max(0.01, 1.0 - avg_sim))

        visual_confidence = min(
            IMAGE_ONLY_MAX_CONFIDENCE,
            round(0.40 + (1.0 - entropy) * 0.12 + min(mean_norm / 100.0, 0.05), 2),
        )

        return VisualAnalysis(
            embedding_norm=round(mean_norm, 2),
            feature_entropy=round(entropy, 3),
            visual_confidence=visual_confidence,
            model_name=PATHOLOGY_VIT_MODEL,
            tiles_processed=len(tiles),
            method="phikon_tile_embedding",
            pathology_ready=True,
        )
    except Exception as exc:
        logger.error("Phikon analysis failed: %s", exc)
        return None


def analyze_slide_image(uploaded_image) -> VisualAnalysis | None:
    """
    Tile large slides and extract Phikon pathology embeddings.

    Uses free owkin/phikon (TCGA pan-cancer pretraining). Does not classify
    specific mutations — provides visual screening metrics for multimodal fusion.
    """
    try:
        tiles = extract_tiles(uploaded_image)
        if not tiles:
            return None
        return _analyze_tiles(tiles)
    except Exception as exc:
        logger.error("Slide analysis failed: %s", exc)
        return None


def fuse_multimodal_confidence(text_detection, visual: VisualAnalysis | None) -> tuple[float, str]:
    if text_detection and visual:
        fused = min(0.98, text_detection.confidence + MULTIMODAL_VISUAL_BOOST)
        return round(fused, 2), f"phikon+{text_detection.method}"
    if text_detection:
        return round(text_detection.confidence, 2), text_detection.method
    if visual:
        return visual.visual_confidence, visual.method
    return 0.0, "none"
