"""Orchestrates validation, preprocessing, model execution, and postprocessing."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import numpy as np

from backend.app.ai.benchmarking.metrics import BenchmarkMetrics
from backend.app.ai.cache.manager import CacheManager
from backend.app.ai.config.settings import AISettings
from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.inference.request import InferenceRequest
from backend.app.ai.inference.response import InferenceResponse
from backend.app.ai.models.base import AIModel
from backend.app.ai.postprocessing.findings import normalize_raw_output
from backend.app.ai.preprocessing.audio import preprocess_audio
from backend.app.ai.preprocessing.document import preprocess_document
from backend.app.ai.preprocessing.image import ImagePreprocessConfig, preprocess_image
from backend.app.ai.preprocessing.video import preprocess_video
from backend.app.ai.registry.loader import ModelLoader
from backend.app.ai.registry.registry import ModelRegistry

logger = logging.getLogger(__name__)
Preprocessor = Callable[[dict[str, Any]], dict[str, Any]]


class AIInferenceEngine:
    """Production-grade inference orchestrator for all AI models."""

    def __init__(
        self,
        registry: ModelRegistry,
        loader: ModelLoader,
        cache: CacheManager,
        device_manager: DeviceManager,
        settings: AISettings,
        preprocessors: dict[str, Preprocessor] | None = None,
    ) -> None:
        self.registry = registry
        self.loader = loader
        self.cache = cache
        self.device_manager = device_manager
        self.settings = settings
        self.preprocessors = preprocessors or _default_preprocessors()

    async def run(self, request: InferenceRequest) -> InferenceResponse:
        """Execute the full inference pipeline."""

        request.validate()
        if request.model_name not in self.registry.names():
            raise KeyError(f"Model '{request.model_name}' is not registered.")
        meta = self.registry.get_metadata(request.model_name)
        if not any(task == request.task for task in meta.supported_tasks):
            raise ValueError(
                f"Model '{request.model_name}' does not support task '{request.task}'."
            )
        metrics = BenchmarkMetrics(batch_size=request.batch_size)
        device = self.device_manager.select_device(
            request.device or meta.required_device.value.lower()
        )
        metrics.device = device
        model = self._resolve_model(request.model_name, device=device, metrics=metrics)
        preprocessed = self._preprocess(request.payload)
        metrics.start_inference()
        raw_output = await model.predict(
            preprocessed,
            batch_size=min(request.batch_size, self.settings.max_batch_size),
        )
        metrics.finish_inference()
        normalized = normalize_raw_output(
            model_name=meta.name,
            model_version=model.version(),
            framework=meta.framework.value,
            task=request.task,
            raw_output=raw_output,
        )
        return InferenceResponse(
            request_id=request.request_id,
            model_name=meta.name,
            model_version=model.version(),
            device=device,
            latency_ms=metrics.inference_latency_ms,
            output=normalized,
            benchmark=metrics.to_dict(),
        )

    def _resolve_model(
        self,
        name: str,
        *,
        device: str,
        metrics: BenchmarkMetrics,
    ) -> AIModel:
        cached = self.cache.get(name)
        if cached is not None and cached.is_loaded:
            metrics.cache_hit = True
            return cached
        metrics.cache_miss = True
        load_started = time.perf_counter()
        model = self.loader.load_model(name, device=device)
        metrics.load_time_ms = (time.perf_counter() - load_started) * 1000
        if self.settings.warmup_on_load:
            metrics.warmup_time_ms = model.warmup(batch_size=1) * 1000
        self.cache.put(name, model, device=device)
        return model

    def _preprocess(self, payload: dict[str, Any]) -> dict[str, Any]:
        modality = str(payload.get("modality", "any")).lower()
        preprocessor = self.preprocessors.get(modality, self.preprocessors["any"])
        return preprocessor(payload)


def _default_preprocessors() -> dict[str, Preprocessor]:
    return {
        "image": _preprocess_image_payload,
        "document": preprocess_document,
        "video": preprocess_video,
        "audio": preprocess_audio,
        "any": lambda payload: dict(payload),
    }


def _preprocess_image_payload(payload: dict[str, Any]) -> dict[str, Any]:
    array = payload.get("array")
    if isinstance(array, np.ndarray):
        config = ImagePreprocessConfig(
            target_width=int(payload.get("width", array.shape[1])),
            target_height=int(payload.get("height", array.shape[0])),
            normalize=bool(payload.get("normalize", True)),
            pad=bool(payload.get("pad", True)),
            tile_size=payload.get("tile_size"),
        )
        return preprocess_image(array, config)
    return {
        "array": array,
        "width": payload.get("width"),
        "height": payload.get("height"),
    }
