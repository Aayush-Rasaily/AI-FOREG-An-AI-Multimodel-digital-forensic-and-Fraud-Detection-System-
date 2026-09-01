"""Audio loading and bounded decoding."""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from backend.app.ai.audio.features.waveform import (
    frame_signal,
    rms_energy,
    simplified_mfcc,
    spectral_centroid,
    zero_crossing_rate,
)
from backend.app.ai.audio.models import AudioFeatureSummary


@dataclass(frozen=True, slots=True)
class LoadedAudio:
    """Bounded mono audio samples."""

    samples: np.ndarray
    sample_rate: int
    channels: int
    duration_seconds: float
    source: str


def ffmpeg_available(command: str = "ffmpeg") -> bool:
    return shutil.which(command) is not None


def load_wav_bytes(
    data: bytes,
    *,
    max_samples: int,
    target_sample_rate: int,
) -> LoadedAudio | None:
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            channels = audio.getnchannels()
            sample_rate = audio.getframerate()
            sample_width = audio.getsampwidth()
            frame_count = audio.getnframes()
            raw = audio.readframes(min(frame_count, max_samples))
    except (OSError, wave.Error, EOFError):
        return None
    if sample_width == 2:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 1:
        samples = (
            np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0
        ) / 128.0
    else:
        return None
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    samples = _resample(samples, sample_rate, target_sample_rate)
    samples = samples[:max_samples]
    duration = samples.size / target_sample_rate if target_sample_rate else 0.0
    return LoadedAudio(
        samples=samples,
        sample_rate=target_sample_rate,
        channels=1,
        duration_seconds=duration,
        source="wav",
    )


def decode_with_ffmpeg(
    stream: Any,
    *,
    ffmpeg_command: str,
    target_sample_rate: int,
    max_samples: int,
    max_duration_seconds: float,
) -> LoadedAudio | None:
    executable = shutil.which(ffmpeg_command)
    if not executable:
        return None
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as temporary:
        input_path = Path(temporary.name)
        shutil.copyfileobj(stream, temporary, length=1024 * 1024)
    try:
        result = subprocess.run(
            [
                executable,
                "-hide_banner",
                "-loglevel",
                "error",
                "-t",
                str(max_duration_seconds),
                "-i",
                str(input_path),
                "-ac",
                "1",
                "-ar",
                str(target_sample_rate),
                "-f",
                "wav",
                "pipe:1",
            ],
            capture_output=True,
            check=False,
            timeout=60,
        )
        if result.returncode != 0:
            return None
        return load_wav_bytes(
            result.stdout,
            max_samples=max_samples,
            target_sample_rate=target_sample_rate,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    finally:
        input_path.unlink(missing_ok=True)


def load_bounded_audio(
    stream: Any,
    *,
    extension: str,
    ffmpeg_command: str,
    target_sample_rate: int,
    max_samples: int,
    max_duration_seconds: float,
) -> LoadedAudio | None:
    if extension == "wav":
        data = stream.read()
        return load_wav_bytes(
            data,
            max_samples=max_samples,
            target_sample_rate=target_sample_rate,
        )
    if ffmpeg_available(ffmpeg_command):
        if hasattr(stream, "seek"):
            stream.seek(0)
        return decode_with_ffmpeg(
            stream,
            ffmpeg_command=ffmpeg_command,
            target_sample_rate=target_sample_rate,
            max_samples=max_samples,
            max_duration_seconds=max_duration_seconds,
        )
    return None


def build_feature_summary(
    loaded: LoadedAudio,
    *,
    window_seconds: float,
    hop_seconds: float,
) -> AudioFeatureSummary:
    frames = frame_signal(
        loaded.samples,
        sample_rate=loaded.sample_rate,
        window_seconds=window_seconds,
        hop_seconds=hop_seconds,
    )
    mfcc_values = [
        simplified_mfcc(frame, loaded.sample_rate) for frame in frames[:32]
    ]
    mfcc_mean = (
        tuple(float(value) for value in np.mean(mfcc_values, axis=0))
        if mfcc_values
        else ()
    )
    return AudioFeatureSummary(
        sample_rate=loaded.sample_rate,
        duration_seconds=loaded.duration_seconds,
        channels=loaded.channels,
        rms_energy=rms_energy(loaded.samples),
        zero_crossing_rate=zero_crossing_rate(loaded.samples),
        spectral_centroid_hz=spectral_centroid(loaded.samples, loaded.sample_rate),
        mfcc_mean=mfcc_mean,
        window_count=len(frames),
    )


def _resample(samples: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate or samples.size == 0:
        return samples
    target_length = int(samples.size * target_rate / source_rate)
    if target_length <= 0:
        return samples
    source_positions = np.linspace(0, samples.size - 1, target_length)
    indices = np.round(source_positions).astype(int)
    indices = np.clip(indices, 0, samples.size - 1)
    return samples[indices]
