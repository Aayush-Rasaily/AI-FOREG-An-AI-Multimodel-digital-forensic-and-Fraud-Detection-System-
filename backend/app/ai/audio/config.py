"""Configuration for AI audio forensic analysis."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class AudioAISettings:
    """Runtime settings for the audio AI forensic engine."""

    engine_version: str = "1.0"
    inference_timeout_seconds: float = 300.0
    max_audio_bytes: int = 128 * 1024 * 1024
    max_duration_seconds: float = 600.0
    max_samples: int = 10_000_000
    analysis_sample_rate: int = 16_000
    window_seconds: float = 0.5
    hop_seconds: float = 0.25
    default_device: str = "cpu"
    enable_gpu: bool = True
    ffmpeg_command: str = field(
        default_factory=lambda: os.getenv("FFMPEG_COMMAND", "ffmpeg"),
    )
    enabled_detectors: tuple[str, ...] = (
        "synthetic_audio",
        "voice_clone",
        "deepfake_voice",
        "speaker_consistency",
        "splicing",
        "waveform",
        "spectral",
        "compression",
        "noise_consistency",
        "silence",
        "metadata",
    )
    synthetic_model_enabled: bool = field(
        default_factory=lambda: _env_bool("AUDIO_SYNTHETIC_MODEL_ENABLED"),
    )
    synthetic_model_path: str | None = field(
        default_factory=lambda: os.getenv("AUDIO_SYNTHETIC_MODEL_PATH"),
    )
    synthetic_model_sha256: str | None = field(
        default_factory=lambda: os.getenv("AUDIO_SYNTHETIC_MODEL_SHA256"),
    )
    synthetic_model_version: str = field(
        default_factory=lambda: os.getenv("AUDIO_SYNTHETIC_MODEL_VERSION", "1.0.0"),
    )
    voice_clone_model_enabled: bool = field(
        default_factory=lambda: _env_bool("AUDIO_VOICE_CLONE_MODEL_ENABLED"),
    )
    voice_clone_model_path: str | None = field(
        default_factory=lambda: os.getenv("AUDIO_VOICE_CLONE_MODEL_PATH"),
    )
    voice_clone_model_sha256: str | None = field(
        default_factory=lambda: os.getenv("AUDIO_VOICE_CLONE_MODEL_SHA256"),
    )
    voice_clone_model_version: str = field(
        default_factory=lambda: os.getenv("AUDIO_VOICE_CLONE_MODEL_VERSION", "1.0.0"),
    )
    deepfake_model_enabled: bool = field(
        default_factory=lambda: _env_bool("AUDIO_DEEPFAKE_MODEL_ENABLED"),
    )
    deepfake_model_path: str | None = field(
        default_factory=lambda: os.getenv("AUDIO_DEEPFAKE_MODEL_PATH"),
    )
    deepfake_model_sha256: str | None = field(
        default_factory=lambda: os.getenv("AUDIO_DEEPFAKE_MODEL_SHA256"),
    )
    deepfake_model_version: str = field(
        default_factory=lambda: os.getenv("AUDIO_DEEPFAKE_MODEL_VERSION", "1.0.0"),
    )
    detector_overrides: dict[str, dict[str, object]] = field(default_factory=dict)
