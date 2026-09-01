"""Signature verification configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


@dataclass(frozen=True, slots=True)
class SignatureAISettings:
    """Runtime settings for Siamese signature verification."""

    enabled: bool = field(default_factory=lambda: _env_bool("SIGNATURE_MODEL_ENABLED"))
    model_path: str | None = field(
        default_factory=lambda: os.getenv("SIGNATURE_MODEL_PATH"),
    )
    model_sha256: str | None = field(
        default_factory=lambda: os.getenv("SIGNATURE_MODEL_SHA256"),
    )
    model_version: str = field(
        default_factory=lambda: os.getenv("SIGNATURE_MODEL_VERSION", "1.0.0"),
    )
    threshold: float = field(
        default_factory=lambda: _env_float("SIGNATURE_THRESHOLD", 0.80),
    )
    inconclusive_margin: float = field(
        default_factory=lambda: _env_float("SIGNATURE_INCONCLUSIVE_MARGIN", 0.05),
    )
    default_device: str = "cpu"
    enable_gpu: bool = True
