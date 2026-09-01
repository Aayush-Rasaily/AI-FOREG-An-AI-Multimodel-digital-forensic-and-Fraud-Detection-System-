"""Reusable image preprocessing for AI forensic detectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np
from PIL import Image

from backend.app.ai.preprocessing.image import ImagePreprocessConfig, preprocess_image


@dataclass(frozen=True, slots=True)
class ImagePreprocessBundle:
    """Preprocessed image tensors and metadata."""

    array: np.ndarray
    width: int
    height: int
    original_width: int
    original_height: int
    scale: float
    padding: tuple[int, int, int, int]
    patches: tuple[np.ndarray, ...] = ()
    metadata: dict[str, Any] | None = None


class FaceDetector(Protocol):
    """Interface for future face detection backends."""

    def detect(
        self,
        array: np.ndarray,
        *,
        width: int,
        height: int,
    ) -> tuple[tuple[float, float, float, float], ...]:
        """Return face bounding boxes in pixel coordinates."""
        ...


def letterbox(
    array: np.ndarray,
    *,
    target_width: int,
    target_height: int,
    fill_value: int = 0,
) -> tuple[np.ndarray, float, tuple[int, int, int, int]]:
    """Resize preserving aspect ratio and pad to target dimensions."""

    height, width = array.shape[:2]
    scale = min(target_width / width, target_height / height)
    resized_width = max(1, int(width * scale))
    resized_height = max(1, int(height * scale))
    resized = np.asarray(
        Image.fromarray(array).resize((resized_width, resized_height)),
        dtype=array.dtype,
    )
    canvas = np.full(
        (target_height, target_width, array.shape[2]),
        fill_value,
        dtype=array.dtype,
    )
    pad_left = (target_width - resized_width) // 2
    pad_top = (target_height - resized_height) // 2
    canvas[pad_top : pad_top + resized_height, pad_left : pad_left + resized_width] = (
        resized
    )
    padding = (
        pad_left,
        pad_top,
        target_width - resized_width - pad_left,
        target_height - resized_height - pad_top,
    )
    return canvas, scale, padding


def extract_patches(
    array: np.ndarray,
    *,
    patch_size: int,
    stride: int | None = None,
) -> tuple[np.ndarray, ...]:
    """Extract fixed-size patches for batched inference."""

    step = stride or patch_size
    height, width = array.shape[:2]
    patches: list[np.ndarray] = []
    for y in range(0, height, step):
        for x in range(0, width, step):
            patch = array[y : y + patch_size, x : x + patch_size]
            if patch.shape[0] == patch_size and patch.shape[1] == patch_size:
                patches.append(patch)
    return tuple(patches)


def preprocess_for_analysis(
    array: np.ndarray,
    *,
    width: int,
    height: int,
    target_size: int = 512,
    normalize: bool = True,
    tile_size: int | None = None,
) -> ImagePreprocessBundle:
    """Apply the standard image AI preprocessing pipeline."""

    boxed, scale, padding = letterbox(
        array,
        target_width=target_size,
        target_height=target_size,
    )
    processed = preprocess_image(
        boxed,
        ImagePreprocessConfig(
            target_width=target_size,
            target_height=target_size,
            normalize=normalize,
            pad=False,
            tile_size=tile_size,
        ),
    )
    patches = extract_patches(processed["array"], patch_size=64) if tile_size else ()
    return ImagePreprocessBundle(
        array=processed["array"],
        width=target_size,
        height=target_size,
        original_width=width,
        original_height=height,
        scale=scale,
        padding=padding,
        patches=patches,
        metadata={"normalize": normalize, "tile_size": tile_size},
    )
