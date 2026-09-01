"""Temporal localization helpers."""

from __future__ import annotations

from backend.app.ai.video.models.base import TemporalEvidence, VideoAIFindingItem


def format_timestamp_range(
    start_ms: int | None,
    end_ms: int | None,
) -> str:
    """Format a human-readable timestamp range."""

    if start_ms is None:
        return "unknown"
    start = _format_ms(start_ms)
    if end_ms is None or end_ms == start_ms:
        return start
    return f"{start} - {_format_ms(end_ms)}"


def attach_temporal(
    finding: VideoAIFindingItem,
    temporal: TemporalEvidence,
) -> VideoAIFindingItem:
    """Return a finding with temporal evidence attached."""

    metadata = {
        **finding.metadata,
        "temporal": temporal.to_dict(),
        "timestamp_range": format_timestamp_range(
            temporal.start_timestamp_ms,
            temporal.end_timestamp_ms,
        ),
    }
    return VideoAIFindingItem(
        detector=finding.detector,
        category=finding.category,
        severity=finding.severity,
        description=finding.description,
        explanation=finding.explanation,
        method=finding.method,
        confidence=finding.confidence,
        regions=finding.regions,
        temporal=temporal,
        recommendation=finding.recommendation,
        metadata=metadata,
        model_name=finding.model_name,
        model_version=finding.model_version,
        model_framework=finding.model_framework,
        capability_status=finding.capability_status,
        limitations=finding.limitations,
    )


def _format_ms(timestamp_ms: int) -> str:
    seconds, millis = divmod(timestamp_ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}.{millis // 10:02d}"
