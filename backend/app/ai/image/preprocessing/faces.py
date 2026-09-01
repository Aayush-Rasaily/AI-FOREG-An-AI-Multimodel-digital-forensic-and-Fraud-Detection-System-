"""Face detection interface for deepfake analysis."""

from __future__ import annotations

from typing import Protocol

import numpy as np

from backend.app.ai.image.utils import detect_face_regions


class FaceDetectionBackend(Protocol):
    """Pluggable face detection backend."""

    def detect_faces(
        self,
        array: np.ndarray,
        *,
        width: int,
        height: int,
    ) -> tuple[tuple[float, float, float, float], ...]:
        """Return face boxes as (x, y, width, height)."""
        ...


class HeuristicFaceDetector:
    """Default heuristic face detector until a model backend is configured."""

    def detect_faces(
        self,
        array: np.ndarray,
        *,
        width: int,
        height: int,
    ) -> tuple[tuple[float, float, float, float], ...]:
        return detect_face_regions(array, width, height)
