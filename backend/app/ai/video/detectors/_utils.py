"""Shared helpers for video AI detectors."""

from __future__ import annotations

import hashlib
from pathlib import Path

from backend.app.ai.video.exceptions import ModelIntegrityError
from backend.app.ai.video.models.base import (
    DetectionMethod,
    DetectorCapabilityStatus,
    VideoAIFindingItem,
    VideoFindingCategory,
)
from backend.app.forensics.models import Severity


def unavailable_finding(
    *,
    detector: str,
    category: VideoFindingCategory,
    reason: str,
    model_name: str = "",
    model_version: str = "",
) -> VideoAIFindingItem:
    """Return a capability finding without fabricated confidence."""

    return VideoAIFindingItem(
        detector=detector,
        category=category,
        severity=Severity.INFO,
        description=f"{detector} capability unavailable.",
        explanation=reason,
        method=DetectionMethod.AI,
        confidence=None,
        capability_status=DetectorCapabilityStatus.UNAVAILABLE,
        metadata={
            "status": DetectorCapabilityStatus.UNAVAILABLE.value,
            "reason": reason,
        },
        model_name=model_name,
        model_version=model_version,
        model_framework="NATIVE",
        limitations="No trained model configured for this detector.",
    )


def verify_model_hash(path: Path, expected_sha256: str | None) -> None:
    """Verify model weight integrity before loading."""

    if not expected_sha256:
        return
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual.lower() != expected_sha256.lower():
        raise ModelIntegrityError(
            "MODEL_INTEGRITY_FAILED",
            "Model weight hash does not match the configured expected value.",
        )
