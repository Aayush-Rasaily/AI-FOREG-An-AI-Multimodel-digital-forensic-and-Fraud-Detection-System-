"""Aggregate audio findings into timeline and segment entries."""

from __future__ import annotations

from typing import Any

from backend.app.ai.audio.models import AudioAIFindingItem


def build_timeline(
    findings: tuple[AudioAIFindingItem, ...],
) -> tuple[dict[str, Any], ...]:
    """Build timeline entries from normalized findings."""

    entries: list[dict[str, Any]] = []
    for finding in findings:
        temporal = finding.temporal
        if temporal is None:
            continue
        entries.append(
            {
                "detector": finding.detector,
                "category": finding.category.value,
                "severity": finding.severity.value,
                "confidence": finding.confidence,
                "method": finding.method.value,
                "start_time_ms": temporal.start_time_ms,
                "end_time_ms": temporal.end_time_ms,
                "duration_ms": temporal.duration_ms,
                "description": finding.description,
            }
        )
    entries.sort(
        key=lambda item: (
            int(item["start_time_ms"])
            if isinstance(item.get("start_time_ms"), int)
            else 0
        )
    )
    return tuple(entries)


def build_segments(
    findings: tuple[AudioAIFindingItem, ...],
) -> tuple[dict[str, Any], ...]:
    """Build segment summaries from localized findings."""

    segments: list[dict[str, Any]] = []
    for index, finding in enumerate(findings):
        temporal = finding.temporal
        if temporal is None:
            continue
        segments.append(
            {
                "segment_id": f"{finding.detector}:{index}",
                "detector": finding.detector,
                "category": finding.category.value,
                "severity": finding.severity.value,
                "confidence": finding.confidence,
                "start_time_ms": temporal.start_time_ms,
                "end_time_ms": temporal.end_time_ms,
                "duration_ms": temporal.duration_ms,
                "description": finding.description,
            }
        )
    return tuple(segments)
