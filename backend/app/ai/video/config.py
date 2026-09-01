"""Configuration for AI video forensic analysis."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class VideoAISettings:
    """Runtime settings for the video AI forensic engine."""

    engine_version: str = "1.0"
    inference_timeout_seconds: float = 300.0
    max_video_bytes: int = 512 * 1024 * 1024
    max_duration_seconds: float = 600.0
    max_frames: int = 120
    sample_interval_seconds: float = 5.0
    default_device: str = "cpu"
    enable_gpu: bool = True
    batch_size: int = 4
    memory_limit_mb: int = 4096
    ffmpeg_command: str = field(
        default_factory=lambda: os.getenv("FFMPEG_COMMAND", "ffmpeg"),
    )
    enabled_detectors: tuple[str, ...] = (
        "deepfake",
        "synthetic_video",
        "temporal",
        "frame_manipulation",
        "face_consistency",
        "compression",
        "metadata",
    )
    deepfake_model_enabled: bool = field(
        default_factory=lambda: _env_bool("VIDEO_DEEPFAKE_MODEL_ENABLED"),
    )
    deepfake_model_path: str | None = field(
        default_factory=lambda: os.getenv("VIDEO_DEEPFAKE_MODEL_PATH"),
    )
    deepfake_model_sha256: str | None = field(
        default_factory=lambda: os.getenv("VIDEO_DEEPFAKE_MODEL_SHA256"),
    )
    deepfake_model_version: str = field(
        default_factory=lambda: os.getenv("VIDEO_DEEPFAKE_MODEL_VERSION", "1.0.0"),
    )
    synthetic_model_enabled: bool = field(
        default_factory=lambda: _env_bool("VIDEO_SYNTHETIC_MODEL_ENABLED"),
    )
    synthetic_model_path: str | None = field(
        default_factory=lambda: os.getenv("VIDEO_SYNTHETIC_MODEL_PATH"),
    )
    synthetic_model_sha256: str | None = field(
        default_factory=lambda: os.getenv("VIDEO_SYNTHETIC_MODEL_SHA256"),
    )
    synthetic_model_version: str = field(
        default_factory=lambda: os.getenv("VIDEO_SYNTHETIC_MODEL_VERSION", "1.0.0"),
    )
    detector_overrides: dict[str, dict[str, object]] = field(default_factory=dict)
