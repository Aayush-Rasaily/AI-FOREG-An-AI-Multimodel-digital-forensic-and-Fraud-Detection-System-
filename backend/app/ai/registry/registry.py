"""Plugin registry for AI models."""

from __future__ import annotations

import logging
from collections.abc import Callable

from backend.app.ai.models.base import AIModel
from backend.app.ai.registry.metadata import ModelMetadata

logger = logging.getLogger(__name__)
ModelFactory = Callable[[], AIModel]


class ModelRegistry:
    """Register, lookup, and manage AI model plugins without switch dispatch."""

    def __init__(self) -> None:
        self._factories: dict[str, ModelFactory] = {}
        self._instances: dict[str, AIModel] = {}
        self._versions: dict[str, str] = {}

    def register(self, factory: ModelFactory) -> None:
        """Register a model factory; each model registers itself."""

        probe = factory()
        meta = probe.metadata()
        name = meta.name
        if name in self._factories:
            raise ValueError(f"Model '{name}' is already registered.")
        self._factories[name] = factory
        self._versions[name] = meta.version
        logger.info(
            "Registered AI model",
            extra={"model": name, "version": meta.version},
        )

    def unregister(self, name: str) -> None:
        """Remove a model from the registry and unload if active."""

        if name not in self._factories:
            raise KeyError(f"Model '{name}' is not registered.")
        instance = self._instances.pop(name, None)
        if instance is not None and instance.is_loaded:
            instance.unload()
        del self._factories[name]
        self._versions.pop(name, None)

    def reload(self, name: str) -> AIModel:
        """Replace the active instance with a freshly constructed model."""

        if name not in self._factories:
            raise KeyError(f"Model '{name}' is not registered.")
        existing = self._instances.get(name)
        if existing is not None and existing.is_loaded:
            existing.unload()
        instance = self._factories[name]()
        self._instances[name] = instance
        self._versions[name] = instance.version()
        return instance

    def lookup(self, name: str) -> AIModel:
        """Return the active model instance, creating one if needed."""

        if name not in self._factories:
            raise KeyError(f"Model '{name}' is not registered.")
        if name not in self._instances:
            self._instances[name] = self._factories[name]()
        return self._instances[name]

    def list_metadata(self) -> tuple[ModelMetadata, ...]:
        """Return metadata for every registered model."""

        return tuple(
            self._factories[name]().metadata() for name in sorted(self._factories)
        )

    def get_metadata(self, name: str) -> ModelMetadata:
        """Return metadata for one registered model."""

        if name not in self._factories:
            raise KeyError(f"Model '{name}' is not registered.")
        return self._factories[name]().metadata()

    def discover_capabilities(self) -> dict[str, list[str]]:
        """Return supported tasks keyed by model name."""

        return {
            name: list(self._factories[name]().metadata().supported_tasks)
            for name in sorted(self._factories)
        }

    def get_version(self, name: str) -> str:
        """Return the tracked version for one model."""

        if name not in self._versions:
            raise KeyError(f"Model '{name}' is not registered.")
        return self._versions[name]

    def names(self) -> tuple[str, ...]:
        """Return all registered model names."""

        return tuple(sorted(self._factories))

    def clear_instances(self) -> None:
        """Unload and drop all active instances."""

        for name in list(self._instances):
            instance = self._instances.pop(name)
            if instance.is_loaded:
                instance.unload()
