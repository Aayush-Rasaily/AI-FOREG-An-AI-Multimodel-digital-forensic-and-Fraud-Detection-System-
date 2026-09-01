"""Model loading orchestration for future weight artifacts."""

from __future__ import annotations

import logging
from pathlib import Path

from backend.app.ai.config.settings import AISettings, ModelFormat
from backend.app.ai.models.base import AIModel
from backend.app.ai.registry.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelLoader:
    """Load models through the registry without hardcoded format switches."""

    def __init__(
        self,
        registry: ModelRegistry,
        settings: AISettings,
    ) -> None:
        self.registry = registry
        self.settings = settings
        self._format_handlers: dict[ModelFormat, str] = {
            fmt: fmt.value for fmt in settings.supported_formats
        }

    def load_model(
        self,
        name: str,
        *,
        device: str,
        artifact_path: Path | None = None,
        model_format: ModelFormat | None = None,
    ) -> AIModel:
        """Load a registered model onto the requested device."""

        model = self.registry.lookup(name)
        if artifact_path is not None and model_format is not None:
            self._validate_artifact(artifact_path, model_format)
            logger.info(
                "Artifact path validated for future loading",
                extra={
                    "model": name,
                    "format": model_format.value,
                    "path": str(artifact_path),
                },
            )
        model.load(device=device)
        return model

    def reload_model(self, name: str, *, device: str) -> AIModel:
        """Reload a model through the registry."""

        model = self.registry.reload(name)
        model.load(device=device)
        return model

    def supported_formats(self) -> tuple[ModelFormat, ...]:
        """Return configured supported artifact formats."""

        return self.settings.supported_formats

    def _validate_artifact(self, path: Path, model_format: ModelFormat) -> None:
        if model_format not in self._format_handlers:
            raise ValueError(f"Unsupported model format: {model_format.value}")
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
