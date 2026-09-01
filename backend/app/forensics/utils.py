"""Shared deterministic helpers for forensic detectors."""

import asyncio
import io
import json
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError

from backend.app.extraction.models import normalize_bbox
from backend.app.forensics.models import RegionBox


def load_image_rgb(image_bytes: bytes) -> tuple[np.ndarray, int, int]:
    """Decode bytes to an RGB numpy array and dimensions."""

    with Image.open(io.BytesIO(image_bytes)) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        array = np.asarray(rgb, dtype=np.uint8)
    return array, width, height


async def load_image_from_storage(
    storage: Any,
    storage_key: str,
    *,
    max_bytes: int,
) -> tuple[np.ndarray, int, int]:
    """Read evidence bytes through storage without modifying the source."""

    async with storage.open(storage_key) as stream:
        data = await asyncio.to_thread(stream.read, max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("Image exceeds configured forensic analysis size limit.")
    return await asyncio.to_thread(load_image_rgb, data)


def region_from_pixels(
    x: float,
    y: float,
    width: float,
    height: float,
    source_width: int,
    source_height: int,
    *,
    page_number: int | None = None,
    frame_number: int | None = None,
) -> RegionBox:
    """Build a pixel region with bounded normalized coordinates."""

    from backend.app.extraction.models import BoundingBox

    normalized = normalize_bbox(
        BoundingBox(x=x, y=y, width=width, height=height),
        float(source_width),
        float(source_height),
    )
    return RegionBox(
        x=x,
        y=y,
        width=width,
        height=height,
        page_number=page_number,
        frame_number=frame_number,
        normalized=RegionBox(
            x=normalized.x,
            y=normalized.y,
            width=normalized.width,
            height=normalized.height,
            page_number=page_number,
            frame_number=frame_number,
        ),
    )


def grid_regions(
    values: np.ndarray,
    threshold: float,
    source_width: int,
    source_height: int,
    *,
    grid: int = 8,
    min_area_ratio: float = 0.01,
) -> tuple[RegionBox, ...]:
    """Convert a thresholded grid into merged bounding boxes."""

    if values.size == 0:
        return ()
    height, width = values.shape
    cell_h = max(1, height // grid)
    cell_w = max(1, width // grid)
    regions: list[RegionBox] = []
    min_pixels = max(1, int(source_width * source_height * min_area_ratio))
    for row in range(grid):
        for col in range(grid):
            y0 = row * cell_h
            x0 = col * cell_w
            y1 = min(height, y0 + cell_h)
            x1 = min(width, x0 + cell_w)
            block = values[y0:y1, x0:x1]
            if block.size == 0:
                continue
            if float(np.mean(block)) < threshold:
                continue
            px_w = (x1 - x0) * source_width / width
            px_h = (y1 - y0) * source_height / height
            if px_w * px_h < min_pixels:
                continue
            regions.append(
                region_from_pixels(
                    x0 * source_width / width,
                    y0 * source_height / height,
                    px_w,
                    px_h,
                    source_width,
                    source_height,
                )
            )
    return tuple(regions)


def severity_from_score(score: float) -> str:
    """Map a normalized score into a severity label."""

    if score >= 0.9:
        return "CRITICAL"
    if score >= 0.75:
        return "HIGH"
    if score >= 0.55:
        return "MEDIUM"
    if score >= 0.35:
        return "LOW"
    return "INFO"


def parse_artifact_json(content: bytes) -> dict[str, Any]:
    """Parse a JSON artifact payload safely."""

    parsed = json.loads(content.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Artifact JSON must be an object.")
    return parsed


def encode_png(array: np.ndarray) -> bytes:
    """Encode an RGB or grayscale numpy array as PNG bytes."""

    mode = "L" if array.ndim == 2 else "RGB"
    with io.BytesIO() as buffer:
        Image.fromarray(array.astype(np.uint8), mode=mode).save(buffer, format="PNG")
        return buffer.getvalue()


def safe_exif(image_bytes: bytes) -> dict[str, Any]:
    """Return serializable EXIF metadata when available."""

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            raw = image.getexif()
            if not raw:
                return {}
            return {
                str(key): str(value) for key, value in raw.items() if value is not None
            }
    except (UnidentifiedImageError, OSError):
        return {}
