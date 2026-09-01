"""Window analysis helpers for audio detectors."""

from __future__ import annotations

import numpy as np

from backend.app.ai.audio.features.waveform import (
    frame_signal,
    rms_energy,
    simplified_mfcc,
    spectral_centroid,
    zero_crossing_rate,
)
from backend.app.ai.audio.models import TemporalEvidence


def window_metrics(
    samples: np.ndarray,
    *,
    sample_rate: int,
    window_seconds: float,
    hop_seconds: float,
) -> list[dict[str, float | int]]:
    frames = frame_signal(
        samples,
        sample_rate=sample_rate,
        window_seconds=window_seconds,
        hop_seconds=hop_seconds,
    )
    hop_ms = int(hop_seconds * 1000)
    metrics: list[dict[str, float | int]] = []
    for index, frame in enumerate(frames):
        start_ms = index * hop_ms
        end_ms = start_ms + int(window_seconds * 1000)
        metrics.append(
            {
                "start_time_ms": start_ms,
                "end_time_ms": end_ms,
                "rms": rms_energy(frame),
                "zcr": zero_crossing_rate(frame),
                "centroid": spectral_centroid(frame, sample_rate),
                "mfcc0": float(simplified_mfcc(frame, sample_rate)[0]),
            }
        )
    return metrics


def temporal_from_ms(
    start_ms: int,
    end_ms: int,
    evidence_type: str,
) -> TemporalEvidence:
    return TemporalEvidence(
        start_time_ms=start_ms,
        end_time_ms=end_ms,
        duration_ms=max(end_ms - start_ms, 0),
        evidence_type=evidence_type,
    )
