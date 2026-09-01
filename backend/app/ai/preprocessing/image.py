"""Image preprocessing utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from backend.app.ai.preprocessing.common import clamp


@dataclass(frozen=True, slots=True)
class ImagePreprocessConfig:
    """Configuration for image preprocessing."""

    target_width: int
    target_height: int
    normalize: bool = True
    pad: bool = True
    tile_size: int | None = None


def resize_image(
    array: np.ndarray,
    *,
    width: int,
    height: int,
) -> np.ndarray:
    """Resize an RGB array using deterministic nearest-neighbor sampling."""

    source_h, source_w = array.shape[:2]
    if source_h == height and source_w == width:
        return array
    y_indices = (np.arange(height) * source_h / height).astype(np.int64)
    x_indices = (np.arange(width) * source_w / width).astype(np.int64)
    return array[y_indices[:, None], x_indices[None, :]]


def normalize_image(array: np.ndarray) -> np.ndarray:
    """Scale uint8 RGB values to float32 in [0, 1]."""

    return array.astype(np.float32) / 255.0


def pad_image(
    array: np.ndarray,
    *,
    target_width: int,
    target_height: int,
    fill_value: int = 0,
) -> np.ndarray:
    """Pad an image to the target dimensions."""

    height, width = array.shape[:2]
    if height >= target_height and width >= target_width:
        return array[:target_height, :target_width]
    channels = array.shape[2] if array.ndim == 3 else 1
    shape = (
        (target_height, target_width, channels)
        if channels > 1
        else (target_height, target_width)
    )
    canvas = np.full(
        shape,
        fill_value,
        dtype=array.dtype,
    )
    canvas[:height, :width] = array
    return canvas


def tile_image(
    array: np.ndarray,
    *,
    tile_size: int,
) -> tuple[np.ndarray, ...]:
    """Split an image into fixed-size tiles."""

    height, width = array.shape[:2]
    tiles: list[np.ndarray] = []
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            tiles.append(array[y : y + tile_size, x : x + tile_size])
    return tuple(tiles)


def preprocess_image(
    array: np.ndarray,
    config: ImagePreprocessConfig,
) -> dict[str, Any]:
    """Apply the configured image preprocessing pipeline."""

    resized = resize_image(
        array,
        width=config.target_width,
        height=config.target_height,
    )
    processed = (
        pad_image(
            resized,
            target_width=config.target_width,
            target_height=config.target_height,
        )
        if config.pad
        else resized
    )
    if config.normalize:
        normalized = normalize_image(processed)
    else:
        normalized = processed.astype(np.float32)
    result: dict[str, Any] = {
        "array": normalized,
        "width": config.target_width,
        "height": config.target_height,
    }
    if config.tile_size is not None:
        result["tiles"] = tile_image(processed, tile_size=config.tile_size)
    result["scale"] = clamp(config.target_width / max(array.shape[1], 1), 0.01, 100.0)
    return result
