"""Audio preprocessing interfaces."""

from __future__ import annotations

from typing import Any


def resample_audio(
    samples: tuple[float, ...],
    *,
    source_rate: int,
    target_rate: int,
) -> tuple[float, ...]:
    """Deterministically resample audio using nearest-neighbor indexing."""

    if source_rate <= 0 or target_rate <= 0 or not samples:
        return ()
    ratio = source_rate / target_rate
    indices = [
        min(int(index * ratio), len(samples) - 1) for index in range(len(samples))
    ]
    return tuple(samples[index] for index in indices)


def preprocess_audio(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize audio preprocessing input."""

    source_rate = int(payload.get("sample_rate", 44100))
    target_rate = int(payload.get("target_rate", 16000))
    raw_samples = payload.get("samples", [])
    if isinstance(raw_samples, list):
        samples = tuple(float(value) for value in raw_samples)
    else:
        samples = ()
    resampled = resample_audio(
        samples,
        source_rate=source_rate,
        target_rate=target_rate,
    )
    return {
        "sample_rate": target_rate,
        "source_rate": source_rate,
        "samples": resampled,
        "channel_count": int(payload.get("channel_count", 1)),
    }
