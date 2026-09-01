"""Frame normalization helpers."""

from __future__ import annotations

import numpy as np


def normalize_frame(rgb: np.ndarray, *, target_size: int = 512) -> np.ndarray:
    """Resize and normalize one RGB frame for model input."""

    from PIL import Image

    image = Image.fromarray(rgb.astype(np.uint8), mode="RGB")
    image.thumbnail((target_size, target_size))
    resized = np.asarray(image, dtype=np.float32) / 255.0
    return resized
