"""Configuration for AI image forensic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ImageAISettings:
    """Runtime settings for the image AI forensic engine."""

    engine_version: str = "1.0"
    inference_timeout_seconds: float = 120.0
    max_image_bytes: int = 32 * 1024 * 1024
    default_device: str = "cpu"
    enable_gpu: bool = True
    batch_size: int = 1
    max_batch_size: int = 8
    memory_limit_mb: int = 2048
    enabled_detectors: tuple[str, ...] = (
        "ai_generated",
        "deepfake_face",
        "manipulation",
        "fake_logo",
        "government_id",
    )
    detector_overrides: dict[str, dict[str, object]] = field(default_factory=dict)
