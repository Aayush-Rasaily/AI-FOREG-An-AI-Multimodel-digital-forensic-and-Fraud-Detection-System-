"""Shared deterministic helpers for comparison matchers."""

import asyncio
import io
import json
from typing import Any

import numpy as np
from PIL import Image, UnidentifiedImageError


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
        raise ValueError("Image exceeds configured comparison size limit.")
    return await asyncio.to_thread(load_image_rgb, data)


async def load_bytes_from_storage(
    storage: Any,
    storage_key: str,
    *,
    max_bytes: int,
) -> bytes:
    """Read raw bytes from storage."""

    async with storage.open(storage_key) as stream:
        data = await asyncio.to_thread(stream.read, max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("Object exceeds configured comparison size limit.")
    return data


def encode_png(array: np.ndarray) -> bytes:
    """Encode an RGB or grayscale numpy array as PNG bytes."""

    mode = "L" if array.ndim == 2 else "RGB"
    with io.BytesIO() as buffer:
        Image.fromarray(array.astype(np.uint8), mode=mode).save(buffer, format="PNG")
        return buffer.getvalue()


def compute_ssim(gray_a: np.ndarray, gray_b: np.ndarray) -> float:
    """Compute a deterministic structural similarity score in [0, 1]."""

    a = gray_a.astype(np.float64)
    b = gray_b.astype(np.float64)
    if a.shape != b.shape:
        height = min(a.shape[0], b.shape[0])
        width = min(a.shape[1], b.shape[1])
        a = a[:height, :width]
        b = b[:height, :width]
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    mu_a = np.mean(a)
    mu_b = np.mean(b)
    sigma_a = np.var(a)
    sigma_b = np.var(b)
    sigma_ab = np.mean((a - mu_a) * (b - mu_b))
    numerator = (2 * mu_a * mu_b + c1) * (2 * sigma_ab + c2)
    denominator = (mu_a**2 + mu_b**2 + c1) * (sigma_a + sigma_b + c2)
    if denominator == 0:
        return 1.0
    return float(max(0.0, min(1.0, numerator / denominator)))


def difference_mask(
    array_a: np.ndarray,
    array_b: np.ndarray,
    *,
    threshold: int = 24,
) -> np.ndarray:
    """Build a binary mask highlighting pixel differences."""

    if array_a.shape != array_b.shape:
        height = min(array_a.shape[0], array_b.shape[0])
        width = min(array_a.shape[1], array_b.shape[1])
        array_a = array_a[:height, :width]
        array_b = array_b[:height, :width]
    diff = np.abs(array_a.astype(np.int16) - array_b.astype(np.int16))
    magnitude = np.max(diff, axis=2) if diff.ndim == 3 else diff
    return (magnitude >= threshold).astype(np.uint8) * 255


def parse_artifact_json(content: bytes) -> dict[str, Any]:
    """Parse a JSON artifact payload safely."""

    parsed = json.loads(content.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Artifact JSON must be an object.")
    return parsed


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


def extract_text_content(records: tuple[dict[str, Any], ...]) -> str:
    """Join extracted text records into one comparable string."""

    parts: list[str] = []
    for record in records:
        content = record.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content.strip())
    return "\n".join(parts)
