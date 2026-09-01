"""Shared helpers for image AI detectors."""

from __future__ import annotations

import io
from typing import Any

import numpy as np
from PIL import Image

from backend.app.forensics.utils import grid_regions, region_from_pixels


def encode_grayscale_png(values: np.ndarray) -> bytes:
    """Encode a float or uint8 grayscale map as PNG."""

    array = values.astype(np.float32)
    if array.max() > 0:
        array = array / array.max()
    png_array = (array * 255.0).astype(np.uint8)
    image = Image.fromarray(png_array, mode="L")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def encode_overlay_png(
    rgb: np.ndarray,
    overlay: np.ndarray,
    *,
    alpha: float = 0.45,
) -> bytes:
    """Blend a heatmap overlay onto the source image."""

    base = rgb.astype(np.float32)
    heat = overlay.astype(np.float32)
    if heat.max() > 0:
        heat = heat / heat.max()
    tint = np.zeros_like(base)
    tint[:, :, 0] = heat * 255.0
    tint[:, :, 1] = heat * 64.0
    blended = np.clip(base * (1.0 - alpha) + tint * alpha, 0, 255).astype(np.uint8)
    image = Image.fromarray(blended, mode="RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def high_frequency_energy_map(rgb: np.ndarray) -> np.ndarray:
    """Compute normalized high-frequency energy per pixel."""

    gray = rgb.mean(axis=2).astype(np.float32)
    dx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    dy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    energy = dx + dy
    if energy.max() > 0:
        energy = energy / energy.max()
    return energy


def patch_variance_map(rgb: np.ndarray, *, patch_size: int = 16) -> np.ndarray:
    """Compute local patch variance across the image."""

    gray = rgb.mean(axis=2).astype(np.float32)
    height, width = gray.shape
    output = np.zeros((height, width), dtype=np.float32)
    for y in range(0, height, patch_size):
        for x in range(0, width, patch_size):
            patch = gray[y : y + patch_size, x : x + patch_size]
            variance = float(patch.var()) if patch.size else 0.0
            output[y : y + patch_size, x : x + patch_size] = variance
    if output.max() > 0:
        output = output / output.max()
    return output


def detect_face_regions(
    rgb: np.ndarray,
    width: int,
    height: int,
) -> tuple[tuple[float, float, float, float], ...]:
    """Heuristic face-region candidates using skin-tone clustering."""

    normalized = rgb.astype(np.float32) / 255.0
    red = normalized[:, :, 0]
    green = normalized[:, :, 1]
    blue = normalized[:, :, 2]
    skin_mask = (red > 0.35) & (green > 0.28) & (blue < 0.45) & (red > green)
    if not skin_mask.any():
        return ()
    ys, xs = np.where(skin_mask)
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = float(ys.min()), float(ys.max())
    box_w = max(1.0, x1 - x0)
    box_h = max(1.0, y1 - y0)
    if box_w * box_h < (width * height * 0.01):
        return ()
    return ((x0, y0, box_w, box_h),)


def id_document_layout_regions(
    width: int,
    height: int,
    document_type: str,
) -> tuple[tuple[str, float, float, float, float], ...]:
    """Return normalized layout regions for supported ID document types."""

    layouts: dict[str, tuple[tuple[str, float, float, float, float], ...]] = {
        "passport": (
            ("photo", 0.08, 0.25, 0.22, 0.35),
            ("mrz", 0.05, 0.82, 0.90, 0.12),
            ("data_block", 0.35, 0.25, 0.55, 0.45),
        ),
        "driver_license": (
            ("photo", 0.05, 0.20, 0.25, 0.45),
            ("data_block", 0.35, 0.18, 0.58, 0.55),
            ("barcode", 0.10, 0.78, 0.80, 0.12),
        ),
        "national_id": (
            ("photo", 0.65, 0.20, 0.28, 0.45),
            ("data_block", 0.08, 0.20, 0.52, 0.55),
        ),
        "pan": (
            ("name_block", 0.10, 0.35, 0.80, 0.12),
            ("number_block", 0.10, 0.55, 0.80, 0.12),
        ),
        "aadhaar": (
            ("photo", 0.05, 0.25, 0.22, 0.35),
            ("number_block", 0.30, 0.55, 0.60, 0.12),
            ("qr_region", 0.70, 0.25, 0.22, 0.35),
        ),
    }
    template = layouts.get(document_type, layouts["national_id"])
    regions: list[tuple[str, float, float, float, float]] = []
    for label, nx, ny, nw, nh in template:
        regions.append(
            (
                label,
                nx * width,
                ny * height,
                nw * width,
                nh * height,
            )
        )
    return tuple(regions)


def regions_from_map(
    values: np.ndarray,
    *,
    source_width: int,
    source_height: int,
    threshold: float = 0.55,
) -> tuple[Any, ...]:
    """Convert an activation map into bounded regions."""

    return grid_regions(
        values,
        threshold=threshold,
        source_width=source_width,
        source_height=source_height,
    )


def peak_region(
    values: np.ndarray,
    *,
    source_width: int,
    source_height: int,
) -> Any | None:
    """Return the highest-energy region from an activation map."""

    flat_index = int(values.argmax())
    y_index, x_index = np.unravel_index(flat_index, values.shape)
    patch = max(8, min(source_width, source_height) // 8)
    x = max(0.0, float(x_index - patch // 2))
    y = max(0.0, float(y_index - patch // 2))
    return region_from_pixels(
        x,
        y,
        float(min(patch, source_width - x)),
        float(min(patch, source_height - y)),
        source_width,
        source_height,
    )
