"""Audio AI detector plugin registry."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.detectors.base import AudioAIDetector
from backend.app.ai.audio.models import AudioDetectorMetadata

logger = logging.getLogger(__name__)


class AudioDetectorRegistry:
    """Register and discover audio forensic detectors."""

    def __init__(self, settings: AudioAISettings | None = None) -> None:
        self.settings = settings or AudioAISettings()
        self._factories: dict[str, Callable[[], AudioAIDetector]] = {}
        self._instances: dict[str, AudioAIDetector] = {}

    def register(self, factory: Callable[[], AudioAIDetector]) -> None:
        probe = factory()
        meta = probe.metadata()
        name = meta.name
        if name in self._factories:
            raise ValueError(f"Detector '{name}' is already registered.")
        self._factories[name] = factory
        logger.info(
            "Registered audio AI detector",
            extra={"detector": name, "version": meta.version},
        )

    def lookup(self, name: str, *, device: str) -> AudioAIDetector:
        if name not in self._factories:
            raise KeyError(f"Detector '{name}' is not registered.")
        instance = self._instances.get(name)
        if instance is None or not instance.is_loaded:
            instance = self._factories[name]()
            instance.load(device=device)
            instance.warmup()
            self._instances[name] = instance
        return instance

    def enabled_names(self) -> tuple[str, ...]:
        return tuple(
            name for name in self.settings.enabled_detectors if name in self._factories
        )

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    def list_metadata(self) -> tuple[AudioDetectorMetadata, ...]:
        return tuple(
            self._factories[name]().metadata() for name in sorted(self._factories)
        )

    def health(self) -> dict[str, dict[str, Any]]:
        return {
            name: self._factories[name]().health() for name in sorted(self._factories)
        }
