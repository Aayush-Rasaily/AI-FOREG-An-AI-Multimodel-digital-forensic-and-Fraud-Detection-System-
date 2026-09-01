"""Inference response contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from backend.app.ai.postprocessing.normalization import NormalizedInferenceOutput


@dataclass(frozen=True, slots=True)
class InferenceResponse:
    """Standard response returned by the inference engine."""

    request_id: UUID
    model_name: str
    model_version: str
    device: str
    latency_ms: float
    output: NormalizedInferenceOutput
    benchmark: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "device": self.device,
            "latency_ms": self.latency_ms,
            "output": self.output.to_dict(),
            "benchmark": self.benchmark,
        }
