"""Normalize detector outputs into persisted findings."""

from __future__ import annotations

from backend.app.ai.video.models.base import (
    VideoAIFindingItem,
    VideoDetectorOutput,
)


def normalize_detector_output(
    output: VideoDetectorOutput,
) -> tuple[VideoAIFindingItem, ...]:
    """Return findings from one detector output."""

    return output.findings
