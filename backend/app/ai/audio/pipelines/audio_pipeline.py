"""Audio analysis pipeline orchestration."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import PurePath

import numpy as np

from backend.app.ai.audio.models import AudioAnalysisContext, AudioFeatureSummary
from backend.app.ai.audio.preprocessing.audio import (
    build_feature_summary,
    ffmpeg_available,
    load_bounded_audio,
)
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType


def _downsample_envelope(samples: np.ndarray, *, points: int = 256) -> list[float]:
    if samples.size == 0:
        return []
    chunk = max(samples.size // points, 1)
    trimmed = samples[: chunk * points]
    if trimmed.size == 0:
        return []
    reshaped = trimmed.reshape(-1, chunk)
    envelope = np.max(np.abs(reshaped), axis=1)
    return [round(float(value), 6) for value in envelope]


def _spectrogram_summary(
    samples: np.ndarray,
    sample_rate: int,
    *,
    bands: int = 32,
) -> dict[str, object]:
    if samples.size == 0 or sample_rate <= 0:
        return {"bands": [], "frame_count": 0}
    window = min(512, samples.size)
    frame = samples[:window].astype(np.float64)
    spectrum = np.abs(np.fft.rfft(frame))
    if spectrum.size == 0:
        return {"bands": [], "frame_count": 0}
    chunk = max(spectrum.size // bands, 1)
    trimmed = spectrum[: chunk * bands]
    reshaped = trimmed.reshape(bands, chunk)
    band_means = np.mean(reshaped, axis=1)
    return {
        "bands": [round(float(value), 6) for value in band_means],
        "frame_count": 1,
        "sample_rate": sample_rate,
    }


async def prepare_audio_context(
    context: AudioAnalysisContext,
) -> tuple[AudioAnalysisContext, tuple[DerivedArtifactPayload, ...]]:
    """Load bounded audio samples and derived artifacts for analysis."""

    settings = context.audio_settings
    extension = PurePath(context.original_filename).suffix.lower().lstrip(".")
    capabilities = {
        "ffmpeg_available": ffmpeg_available(settings.ffmpeg_command),
        "wav_decode": extension == "wav",
    }
    loaded = None
    async with context.storage.open(context.storage_key) as stream:
        loaded = await asyncio.to_thread(
            load_bounded_audio,
            stream,
            extension=extension or "wav",
            ffmpeg_command=settings.ffmpeg_command,
            target_sample_rate=settings.analysis_sample_rate,
            max_samples=settings.max_samples,
            max_duration_seconds=settings.max_duration_seconds,
        )
    artifacts: list[DerivedArtifactPayload] = []
    feature_summary: AudioFeatureSummary | None = None
    samples = None
    sample_rate = context.sample_rate
    duration_ms = context.duration_ms
    if loaded is not None:
        samples = loaded.samples
        sample_rate = loaded.sample_rate
        duration_ms = int(loaded.duration_seconds * 1000)
        feature_summary = build_feature_summary(
            loaded,
            window_seconds=settings.window_seconds,
            hop_seconds=settings.hop_seconds,
        )
        artifacts.append(
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_AUDIO_FEATURES,
                mime_type="application/json",
                content=json.dumps(feature_summary.to_dict(), sort_keys=True).encode(
                    "utf-8"
                ),
                metadata={"source": loaded.source},
            )
        )
        envelope = _downsample_envelope(samples)
        artifacts.append(
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_AUDIO_WAVEFORM,
                mime_type="application/json",
                content=json.dumps(
                    {
                        "sample_rate": sample_rate,
                        "duration_seconds": loaded.duration_seconds,
                        "envelope": envelope,
                    },
                    sort_keys=True,
                ).encode("utf-8"),
                metadata={"points": len(envelope)},
            )
        )
        spectrogram = _spectrogram_summary(samples, sample_rate)
        bands = spectrogram["bands"]
        band_count = len(bands) if isinstance(bands, list) else 0
        artifacts.append(
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_AUDIO_SPECTROGRAM,
                mime_type="application/json",
                content=json.dumps(spectrogram, sort_keys=True).encode("utf-8"),
                metadata={"bands": band_count},
            )
        )
    updated = replace(
        context,
        samples=samples,
        sample_rate=sample_rate,
        duration_ms=duration_ms,
        feature_summary=feature_summary,
        capabilities={
            **context.capabilities,
            **capabilities,
            "decoded_audio": loaded is not None,
        },
        preprocessing={
            **context.preprocessing,
            "decode_source": loaded.source if loaded else None,
            "ffmpeg_available": capabilities["ffmpeg_available"],
        },
    )
    return updated, tuple(artifacts)
