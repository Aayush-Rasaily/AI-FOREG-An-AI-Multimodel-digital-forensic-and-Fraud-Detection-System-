"""Inference latency and resource metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BenchmarkMetrics:
    """Track load, warmup, and inference performance."""

    load_time_ms: float = 0.0
    warmup_time_ms: float = 0.0
    inference_latency_ms: float = 0.0
    peak_memory_mb: float | None = None
    device: str = "cpu"
    batch_size: int = 1
    cache_hit: bool = False
    cache_miss: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
    _started_at: float | None = field(default=None, repr=False)

    def start_inference(self) -> None:
        self._started_at = time.perf_counter()

    def finish_inference(self) -> None:
        if self._started_at is None:
            return
        self.inference_latency_ms = (time.perf_counter() - self._started_at) * 1000
        self._started_at = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "load_time_ms": round(self.load_time_ms, 3),
            "warmup_time_ms": round(self.warmup_time_ms, 3),
            "inference_latency_ms": round(self.inference_latency_ms, 3),
            "peak_memory_mb": self.peak_memory_mb,
            "device": self.device,
            "batch_size": self.batch_size,
            "cache_hit": self.cache_hit,
            "cache_miss": self.cache_miss,
            "extra": self.extra,
        }
