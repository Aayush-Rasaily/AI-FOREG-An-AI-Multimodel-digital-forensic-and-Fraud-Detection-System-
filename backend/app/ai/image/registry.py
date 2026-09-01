"""Image AI detector plugin registry."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from backend.app.ai.image.config import ImageAISettings
from backend.app.ai.image.detectors.base import ImageAIDetector
from backend.app.ai.image.models import ImageDetectorMetadata

logger = logging.getLogger(__name__)


class ImageDetectorRegistry:
    """Register and discover image forensic AI detectors without switch dispatch."""

    def __init__(self, settings: ImageAISettings | None = None) -> None:
        self.settings = settings or ImageAISettings()
        self._factories: dict[str, Callable[[], ImageAIDetector]] = {}
        self._instances: dict[str, ImageAIDetector] = {}

    def register(self, factory: Callable[[], ImageAIDetector]) -> None:
        """Register one detector factory."""

        probe = factory()
        meta = probe.metadata()
        name = meta.name
        if name in self._factories:
            raise ValueError(f"Detector '{name}' is already registered.")
        self._factories[name] = factory
        logger.info(
            "Registered image AI detector",
            extra={"detector": name, "version": meta.version},
        )

    def unregister(self, name: str) -> None:
        """Remove a detector from the registry."""

        if name not in self._factories:
            raise KeyError(f"Detector '{name}' is not registered.")
        instance = self._instances.pop(name, None)
        if instance is not None and instance.is_loaded:
            instance.unload()
        del self._factories[name]

    def reload(self, name: str, *, device: str) -> ImageAIDetector:
        """Replace the active detector instance."""

        if name not in self._factories:
            raise KeyError(f"Detector '{name}' is not registered.")
        existing = self._instances.get(name)
        if existing is not None and existing.is_loaded:
            existing.unload()
        instance = self._factories[name]()
        instance.load(device=device)
        self._instances[name] = instance
        return instance

    def lookup(self, name: str, *, device: str) -> ImageAIDetector:
        """Return an active detector instance."""

        if name not in self._factories:
            raise KeyError(f"Detector '{name}' is not registered.")
        instance = self._instances.get(name)
        if instance is None or not instance.is_loaded:
            instance = self.reload(name, device=device)
        return instance

    def enabled_names(self) -> tuple[str, ...]:
        """Return configured enabled detector names."""

        return tuple(
            name for name in self.settings.enabled_detectors if name in self._factories
        )

    def names(self) -> tuple[str, ...]:
        """Return all registered detector names."""

        return tuple(sorted(self._factories))

    def list_metadata(self) -> tuple[ImageDetectorMetadata, ...]:
        """Return metadata for every registered detector."""

        return tuple(
            self._factories[name]().metadata() for name in sorted(self._factories)
        )

    def discover_capabilities(self) -> dict[str, tuple[str, ...]]:
        """Map detector names to supported tasks."""

        return {meta.name: meta.supported_tasks for meta in self.list_metadata()}

    def health(self) -> dict[str, dict[str, Any]]:
        """Return health for all registered detectors."""

        return {
            name: self._factories[name]().health() for name in sorted(self._factories)
        }
