"""Face detection and tracking interfaces for video analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from backend.app.ai.image.preprocessing.faces import HeuristicFaceDetector


@dataclass(frozen=True, slots=True)
class TrackedFace:
    """One face tracked across sampled frames."""

    track_id: str
    frame_number: int
    timestamp_ms: int
    x: float
    y: float
    width: float
    height: float
    embedding: tuple[float, ...] = ()


class FaceTracker(Protocol):
    """Interface for temporal face tracking."""

    def detect(self, rgb: np.ndarray, *, width: int, height: int) -> tuple[
        tuple[float, float, float, float],
        ...,
    ]:
        """Detect faces in one frame."""
        ...

    def track(
        self,
        frames: tuple[tuple[int, int, np.ndarray, int, int], ...],
    ) -> tuple[TrackedFace, ...]:
        """Track faces across multiple frames."""
        ...


class HeuristicFaceTracker:
    """Classical face detection across sampled frames."""

    def __init__(self) -> None:
        self._detector = HeuristicFaceDetector()

    def detect(
        self,
        rgb: np.ndarray,
        *,
        width: int,
        height: int,
    ) -> tuple[tuple[float, float, float, float], ...]:
        return self._detector.detect_faces(rgb, width=width, height=height)

    def track(
        self,
        frames: tuple[tuple[int, int, np.ndarray, int, int], ...],
    ) -> tuple[TrackedFace, ...]:
        tracked: list[TrackedFace] = []
        for frame_number, timestamp_ms, rgb, width, height in frames:
            faces = self.detect(rgb, width=width, height=height)
            for index, (x, y, box_w, box_h) in enumerate(faces):
                tracked.append(
                    TrackedFace(
                        track_id=f"face-{frame_number}-{index}",
                        frame_number=frame_number,
                        timestamp_ms=timestamp_ms,
                        x=x,
                        y=y,
                        width=box_w,
                        height=box_h,
                    )
                )
        return tuple(tracked)
