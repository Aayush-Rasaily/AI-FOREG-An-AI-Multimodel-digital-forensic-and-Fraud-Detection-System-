"""Deterministic timeline event ordering."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.timeline.models import TimelineEvent

SOURCE_PRIORITY: dict[str, int] = {
    "custody": 1,
    "evidence": 2,
    "processing": 3,
    "extraction": 4,
    "forensic": 5,
    "image_ai": 6,
    "document_ai": 7,
    "signature_ai": 8,
    "video_ai": 9,
    "audio_ai": 10,
    "fusion": 11,
    "case_intelligence": 12,
    "report": 13,
    "metadata": 14,
    "missing": 99,
}


def order_events(events: list[TimelineEvent]) -> tuple[TimelineEvent, ...]:
    """Return events sorted deterministically."""

    return tuple(
        sorted(
            events,
            key=lambda item: (
                item.normalized_timestamp is None,
                item.normalized_timestamp or datetime.min.replace(tzinfo=UTC),
                -item.confidence,
                SOURCE_PRIORITY.get(item.source, 50),
                item.event_id,
            ),
        )
    )
