"""Aggregate video findings into timeline entries."""

from __future__ import annotations

from typing import Any

from backend.app.ai.video.models.base import VideoAIFindingItem


def build_timeline(
    findings: tuple[VideoAIFindingItem, ...],
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
                "start_frame": temporal.start_frame,
                "end_frame": temporal.end_frame,
                "start_timestamp_ms": temporal.start_timestamp_ms,
                "end_timestamp_ms": temporal.end_timestamp_ms,
                "description": finding.description,
            }
        )
    entries.sort(
        key=lambda item: (
            int(item["start_timestamp_ms"])
            if isinstance(item.get("start_timestamp_ms"), int)
            else 0
        )
    )
    return tuple(entries)
