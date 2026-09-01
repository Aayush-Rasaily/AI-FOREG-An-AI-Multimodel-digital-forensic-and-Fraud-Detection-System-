"""Video preprocessing interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class VideoFrameSample:
    """One sampled video frame reference."""

    frame_number: int
    timestamp_ms: float
    width: int
    height: int


class FrameSampler(Protocol):
    """Interface for future deterministic frame sampling."""

    def sample(
        self,
        *,
        duration_ms: float,
        fps: float,
        max_frames: int,
    ) -> tuple[VideoFrameSample, ...]:
        """Return evenly spaced frame samples."""
        ...


def preprocess_video(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize video preprocessing input."""

    duration_ms = float(payload.get("duration_ms", 0))
    fps = float(payload.get("fps", 24))
    max_frames = int(payload.get("max_frames", 8))
    interval = duration_ms / max(max_frames - 1, 1) if max_frames > 1 else duration_ms
    samples = tuple(
        {
            "frame_number": index,
            "timestamp_ms": round(index * interval, 3),
        }
        for index in range(max_frames)
        if duration_ms > 0 or index == 0
    )
    return {
        "duration_ms": duration_ms,
        "fps": fps,
        "samples": samples,
    }
