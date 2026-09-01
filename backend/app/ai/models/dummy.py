"""Deterministic infrastructure verification model."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from backend.app.ai.models.base import AIModel
from backend.app.ai.registry.metadata import (
    DeviceRequirement,
    InputType,
    ModelFramework,
    ModelMetadata,
    OutputType,
)


class DummyModel(AIModel):
    """Verify AI infrastructure with deterministic non-forensic output."""

    MODEL_NAME = "dummy"
    MODEL_VERSION = "1.0.0"
    MODEL_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def __init__(self) -> None:
        self._loaded = False
        self._device = "cpu"
        self._warmup_seconds = 0.0

    def load(self, *, device: str) -> None:
        self._device = device
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False
        self._warmup_seconds = 0.0

    def warmup(self, *, batch_size: int = 1) -> float:
        if not self._loaded:
            raise RuntimeError("DummyModel must be loaded before warmup.")
        started = time.perf_counter()
        _ = self._deterministic_value({"warmup": True, "batch_size": batch_size})
        self._warmup_seconds = time.perf_counter() - started
        return self._warmup_seconds

    async def predict(
        self,
        inputs: Any,
        *,
        batch_size: int = 1,
    ) -> dict[str, Any]:
        if not self._loaded:
            raise RuntimeError("DummyModel must be loaded before predict.")
        deterministic = self._deterministic_value(inputs)
        return {
            "model": self.MODEL_NAME,
            "version": self.MODEL_VERSION,
            "infrastructure_check": "passed",
            "deterministic_value": deterministic,
            "device": self._device,
            "batch_size": batch_size,
            "input_fingerprint": self._fingerprint(inputs),
        }

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=self.MODEL_NAME,
            version=self.MODEL_VERSION,
            author="AI-FORGE Engineering",
            framework=ModelFramework.NATIVE,
            license="Proprietary",
            input_type=InputType.ANY,
            output_type=OutputType.INFRASTRUCTURE,
            model_hash=self.MODEL_HASH,
            training_dataset=None,
            supported_tasks=("infrastructure_check",),
            required_device=DeviceRequirement.ANY,
            description=(
                "Deterministic infrastructure verification model. "
                "Does not perform forensic analysis."
            ),
            tags=("infrastructure", "deterministic"),
        )

    def supports(self, task: str) -> bool:
        return task in self.metadata().supported_tasks

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "device": self._device,
            "warmup_seconds": round(self._warmup_seconds, 6),
            "status": "healthy" if self._loaded else "unloaded",
        }

    def version(self) -> str:
        return self.MODEL_VERSION

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @staticmethod
    def _fingerprint(inputs: Any) -> str:
        payload = json.dumps(inputs, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _deterministic_value(inputs: Any) -> int:
        digest = hashlib.sha256(
            json.dumps(inputs, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return int(digest[:8], 16) % 1000
