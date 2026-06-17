"""WSI / large slide tiling using Pillow (free, no OpenSlide required)."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from PIL import Image

from services.config import MAX_TILES, TILE_SIZE

logger = logging.getLogger(__name__)


@dataclass
class SlideTile:
    index: int
    x: int
    y: int
    width: int
    height: int
    image: Image.Image


def extract_tiles(uploaded_file, tile_size: int = TILE_SIZE, max_tiles: int = MAX_TILES) -> list[SlideTile]:
    """
    Crop a large pathology image into uniform tiles.

    Works with PNG/JPG uploads. For true gigapixel SVS/TIFF WSI files,
    install openslide-python separately (also free).
    """
    if hasattr(uploaded_file, "read"):
        uploaded_file.seek(0)
        raw = uploaded_file.read()
        uploaded_file.seek(0)
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    else:
        image = Image.open(uploaded_file).convert("RGB")

    width, height = image.size
    tiles: list[SlideTile] = []
    idx = 0

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            if idx >= max_tiles:
                break
            box = (x, y, min(x + tile_size, width), min(y + tile_size, height))
            crop = image.crop(box)
            if crop.width < tile_size or crop.height < tile_size:
                crop = crop.resize((tile_size, tile_size), Image.Resampling.BILINEAR)
            tiles.append(
                SlideTile(
                    index=idx,
                    x=x,
                    y=y,
                    width=box[2] - box[0],
                    height=box[3] - box[1],
                    image=crop,
                )
            )
            idx += 1
        if idx >= max_tiles:
            break

    logger.info("Extracted %d tiles from %dx%d slide", len(tiles), width, height)
    return tiles
