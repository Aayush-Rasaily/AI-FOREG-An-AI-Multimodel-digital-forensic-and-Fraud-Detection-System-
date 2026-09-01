"""Clip-level preprocessing helpers."""

from __future__ import annotations

from backend.app.ai.video.models.base import VideoFrameReference


def clip_frame_range(
    frames: tuple[VideoFrameReference, ...],
    *,
    start_frame: int,
    end_frame: int,
) -> tuple[VideoFrameReference, ...]:
    """Return frames within an inclusive frame-number range."""

    return tuple(
        frame
        for frame in frames
        if start_frame <= frame.frame_number <= end_frame
    )
