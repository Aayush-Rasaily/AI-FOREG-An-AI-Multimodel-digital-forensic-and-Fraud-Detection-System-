"""Temporal localization helpers."""

from __future__ import annotations

from backend.app.ai.audio.models import AudioAIFindingItem, TemporalEvidence


def attach_temporal(
    finding: AudioAIFindingItem,
    temporal: TemporalEvidence,
) -> AudioAIFindingItem:
    metadata = {
        **finding.metadata,
        "temporal": temporal.to_dict(),
    }
    return AudioAIFindingItem(
        detector=finding.detector,
        category=finding.category,
        severity=finding.severity,
        description=finding.description,
        explanation=finding.explanation,
        method=finding.method,
        confidence=finding.confidence,
        temporal=temporal,
        recommendation=finding.recommendation,
        metadata=metadata,
        model_name=finding.model_name,
        model_version=finding.model_version,
        model_framework=finding.model_framework,
        capability_status=finding.capability_status,
        limitations=finding.limitations,
    )
