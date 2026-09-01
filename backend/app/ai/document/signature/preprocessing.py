"""Signature image preprocessing."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image


def preprocess_signature_image(data: bytes, *, size: int = 224) -> np.ndarray:
    """Normalize a signature crop for Siamese inference."""

    image = Image.open(io.BytesIO(data)).convert("RGB")
    image = image.resize((size, size), Image.Resampling.BILINEAR)
    array = np.asarray(image, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    array = (array - mean) / std
    return np.transpose(array, (2, 0, 1))
