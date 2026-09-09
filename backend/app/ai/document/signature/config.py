"""Signature verification configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


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


def _packaged_model_path() -> Path:
    """Return the repository-packaged Siamese checkpoint path."""

    # config.py → signature → document → ai → models/signature/siamese_best.pt
    return (
        Path(__file__).resolve().parents[2]
        / "models"
        / "signature"
        / "siamese_best.pt"
    )


def _resolve_model_path() -> str | None:
    """Resolve ``SIGNATURE_MODEL_PATH`` or the packaged checkpoint.

    An explicitly empty ``SIGNATURE_MODEL_PATH`` disables the packaged default
    so tests and operators can force the UNAVAILABLE path.
    """

    raw = os.getenv("SIGNATURE_MODEL_PATH")
    if raw is not None:
        stripped = raw.strip()
        return stripped or None
    packaged = _packaged_model_path()
    if packaged.is_file():
        return str(packaged)
    return None


def _resolve_default_device() -> str:
    """Prefer CUDA when available; otherwise CPU. No GPU hard requirement."""

    if not _env_bool("SIGNATURE_ENABLE_GPU", True):
        return "cpu"
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


@dataclass(frozen=True, slots=True)
class SignatureAISettings:
    """Runtime settings for Siamese signature verification."""

    enabled: bool = field(
        default_factory=lambda: _env_bool("SIGNATURE_MODEL_ENABLED", True),
    )
    model_path: str | None = field(default_factory=_resolve_model_path)
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
    default_device: str = field(default_factory=_resolve_default_device)
    enable_gpu: bool = field(
        default_factory=lambda: _env_bool("SIGNATURE_ENABLE_GPU", True),
    )
