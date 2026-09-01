"""Shared helpers for document AI detectors."""

from __future__ import annotations

import json
from typing import Any

from backend.app.ai.document.models.base import (
    DetectionMethod,
    DetectorCapabilityStatus,
    DocumentAIFindingItem,
    DocumentFindingCategory,
)
from backend.app.forensics.models import Severity


def unavailable_finding(
    *,
    detector: str,
    category: DocumentFindingCategory,
    reason: str,
    model_name: str = "",
    model_version: str = "",
) -> DocumentAIFindingItem:
    """Return a capability finding without fabricated confidence."""

    return DocumentAIFindingItem(
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
    )


def records_by_type(
    records: tuple[dict[str, Any], ...],
    extraction_type: str,
) -> list[dict[str, Any]]:
    """Filter extraction records by type."""

    return [
        record for record in records if record.get("extraction_type") == extraction_type
    ]


def artifact_json(
    artifacts: tuple[dict[str, Any], ...],
    artifact_type: str,
) -> dict[str, Any] | None:
    """Return parsed JSON metadata for the first matching artifact."""

    for artifact in artifacts:
        if artifact.get("artifact_type") != artifact_type:
            continue
        metadata = artifact.get("metadata")
        if isinstance(metadata, dict):
            return metadata
    return None


def load_artifact_bytes(
    artifacts: tuple[dict[str, Any], ...],
    artifact_type: str,
) -> bytes | None:
    """Load raw bytes when artifact payload is embedded in metadata."""

    for artifact in artifacts:
        if artifact.get("artifact_type") != artifact_type:
            continue
        payload = artifact.get("payload")
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        encoded = artifact.get("payload_base64")
        if isinstance(encoded, str):
            import base64

            return base64.b64decode(encoded)
    return None


def parse_json_artifact(raw: bytes | None) -> dict[str, Any]:
    """Parse JSON artifact bytes safely."""

    if not raw:
        return {}
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
