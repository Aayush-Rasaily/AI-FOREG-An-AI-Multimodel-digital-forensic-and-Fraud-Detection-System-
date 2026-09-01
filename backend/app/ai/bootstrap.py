"""Bootstrap helpers for the AI inference framework."""

from __future__ import annotations

from backend.app.ai.cache.manager import CacheManager
from backend.app.ai.config.settings import AISettings
from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.document.signature.config import SignatureAISettings
from backend.app.ai.document.signature.model import SiameseSignatureModel
from backend.app.ai.inference.engine import AIInferenceEngine
from backend.app.ai.models.dummy import DummyModel
from backend.app.ai.registry.loader import ModelLoader
from backend.app.ai.registry.registry import ModelRegistry


def build_registry(
    signature_settings: SignatureAISettings | None = None,
) -> ModelRegistry:
    """Create a registry with the built-in infrastructure models."""

    registry = ModelRegistry()
    registry.register(DummyModel)
    settings = signature_settings or SignatureAISettings()
    if settings.enabled:
        registry.register(lambda: SiameseSignatureModel(settings))
    return registry


def build_ai_stack(
    settings: AISettings | None = None,
) -> tuple[ModelRegistry, ModelLoader, CacheManager, DeviceManager, AIInferenceEngine]:
    """Compose the AI inference stack for dependency injection."""

    ai_settings = settings or AISettings()
    registry = build_registry()
    loader = ModelLoader(registry, ai_settings)
    cache = CacheManager(
        max_models=ai_settings.cache_max_models,
        ttl_seconds=ai_settings.cache_ttl_seconds,
    )
    device_manager = DeviceManager(prefer_gpu=ai_settings.enable_gpu)
    engine = AIInferenceEngine(
        registry=registry,
        loader=loader,
        cache=cache,
        device_manager=device_manager,
        settings=ai_settings,
    )
    return registry, loader, cache, device_manager, engine
