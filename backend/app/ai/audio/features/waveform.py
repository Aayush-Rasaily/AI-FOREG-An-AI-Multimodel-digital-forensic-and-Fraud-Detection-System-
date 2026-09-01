"""Shared audio feature extraction helpers."""

from __future__ import annotations

import numpy as np


def rms_energy(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))


def zero_crossing_rate(samples: np.ndarray) -> float:
    if samples.size < 2:
        return 0.0
    signs = np.sign(samples)
    crossings = np.sum(np.abs(np.diff(signs)) > 0)
    return float(crossings / max(samples.size - 1, 1))


def frame_signal(
    samples: np.ndarray,
    *,
    sample_rate: int,
    window_seconds: float,
    hop_seconds: float,
) -> tuple[np.ndarray, ...]:
    window_size = max(int(sample_rate * window_seconds), 1)
    hop_size = max(int(sample_rate * hop_seconds), 1)
    if samples.size < window_size:
        return (samples.astype(np.float32),)
    frames: list[np.ndarray] = []
    for start in range(0, samples.size - window_size + 1, hop_size):
        frames.append(samples[start : start + window_size].astype(np.float32))
    if not frames:
        frames.append(samples.astype(np.float32))
    return tuple(frames)


def spectral_centroid(samples: np.ndarray, sample_rate: int) -> float:
    if samples.size == 0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(samples.astype(np.float64)))
    freqs = np.fft.rfftfreq(samples.size, d=1.0 / sample_rate)
    total = float(spectrum.sum())
    if total <= 0:
        return 0.0
    return float(np.sum(freqs * spectrum) / total)


def stft_magnitude(
    samples: np.ndarray,
    *,
    sample_rate: int,
    window_seconds: float = 0.05,
) -> np.ndarray:
    window_size = max(int(sample_rate * window_seconds), 64)
    if samples.size < window_size:
        padded = np.pad(samples, (0, window_size - samples.size))
    else:
        padded = samples[:window_size]
    window = np.hanning(window_size)
    windowed = padded.astype(np.float64) * window
    return np.abs(np.fft.rfft(windowed))


def simplified_mfcc(
    samples: np.ndarray,
    sample_rate: int,
    count: int = 13,
) -> np.ndarray:
    magnitude = stft_magnitude(samples, sample_rate=sample_rate)
    if magnitude.size == 0:
        return np.zeros(count, dtype=np.float64)
    log_mag = np.log1p(magnitude)
    indices = np.linspace(0, log_mag.size - 1, count).astype(int)
    return log_mag[indices]


def estimate_pitch_hz(samples: np.ndarray, sample_rate: int) -> float | None:
    if samples.size < sample_rate // 10:
        return None
    centered = samples.astype(np.float64) - np.mean(samples)
    correlation = np.correlate(centered, centered, mode="full")
    correlation = correlation[correlation.size // 2 :]
    min_lag = sample_rate // 400
    max_lag = sample_rate // 80
    if max_lag >= correlation.size:
        return None
    segment = correlation[min_lag:max_lag]
    if segment.size == 0:
        return None
    lag = int(np.argmax(segment)) + min_lag
    if lag <= 0:
        return None
    return float(sample_rate / lag)
