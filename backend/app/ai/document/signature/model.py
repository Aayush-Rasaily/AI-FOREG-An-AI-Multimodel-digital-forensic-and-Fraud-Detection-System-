"""Siamese signature verification model."""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from typing import Any

from backend.app.ai.document.signature.config import SignatureAISettings
from backend.app.ai.models.base import AIModel
from backend.app.ai.registry.metadata import (
    DeviceRequirement,
    InputType,
    ModelFramework,
    ModelMetadata,
    OutputType,
)

logger = logging.getLogger(__name__)


class ModelIntegrityError(RuntimeError):
    """Raised when configured model weights fail integrity verification."""


class SiameseSignatureModel(AIModel):
    """Siamese signature verification model with EfficientNet-B0 backbone."""

    MODEL_NAME = "siamese-signature"
    BACKBONE = "efficientnet-b0"

    def __init__(self, settings: SignatureAISettings | None = None) -> None:
        self.settings = settings or SignatureAISettings()
        self._loaded = False
        self._device = "cpu"
        self._warmup_seconds = 0.0
        self._module: Any = None
        self._load_error: str | None = None
        self._file_hash: str | None = None

    def load(self, *, device: str) -> None:
        self._device = device
        self._loaded = False
        self._module = None
        self._load_error = None
        if not self.settings.enabled:
            self._load_error = "Signature verification is disabled in configuration."
            return
        model_path = self.settings.model_path
        if not model_path:
            self._load_error = "SIGNATURE_MODEL_PATH is not configured."
            return
        path = Path(model_path)
        if not path.is_file():
            self._load_error = f"Signature model weights not found at '{model_path}'."
            return
        file_hash = self._hash_file(path)
        expected = (self.settings.model_sha256 or "").lower()
        if expected and file_hash != expected:
            raise ModelIntegrityError(
                "Configured signature model SHA-256 does not match the weight file.",
            )
        self._file_hash = file_hash
        try:
            import torch
            from torch import nn
            from torchvision.models import efficientnet_b0
        except ImportError as exc:
            self._load_error = "PyTorch is not installed."
            logger.warning("Signature model unavailable: %s", exc)
            return
        backbone = efficientnet_b0(weights=None)
        backbone.classifier = nn.Identity()
        embedding_dim = 128

        class SiameseNet(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.backbone = backbone
                self.projection = nn.Sequential(
                    nn.Linear(1280, embedding_dim),
                    nn.ReLU(),
                    nn.Linear(embedding_dim, embedding_dim),
                )

            def embed(self, tensor: torch.Tensor) -> torch.Tensor:
                features = self.backbone(tensor)
                return self.projection(features)

        model = SiameseNet()
        state = torch.load(path, map_location=device, weights_only=True)
        model.load_state_dict(state, strict=False)
        model.to(device)
        model.eval()
        self._module = model
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False
        self._module = None
        self._warmup_seconds = 0.0

    def warmup(self, *, batch_size: int = 1) -> float:
        if not self._loaded or self._module is None:
            raise RuntimeError("SiameseSignatureModel must be loaded before warmup.")
        import torch

        started = time.perf_counter()
        dummy = torch.zeros(batch_size, 3, 224, 224, device=self._device)
        with torch.no_grad():
            _ = self._module.embed(dummy)
        self._warmup_seconds = time.perf_counter() - started
        return self._warmup_seconds

    async def predict(
        self,
        inputs: Any,
        *,
        batch_size: int = 1,
    ) -> dict[str, Any]:
        if not self._loaded or self._module is None:
            return {
                "model": self.MODEL_NAME,
                "model_version": self.settings.model_version,
                "status": "unavailable",
                "reason": self._load_error or "Signature model is not loaded.",
                "similarity": None,
                "threshold": self.settings.threshold,
                "verdict": "UNAVAILABLE",
            }
        import torch

        reference = inputs.get("reference")
        questioned = inputs.get("questioned")
        if reference is None or questioned is None:
            raise ValueError(
                "Signature verification requires reference and questioned tensors."
            )
        started = time.perf_counter()
        ref_tensor = torch.as_tensor(reference, device=self._device).unsqueeze(0)
        q_tensor = torch.as_tensor(questioned, device=self._device).unsqueeze(0)
        with torch.no_grad():
            ref_embed = self._module.embed(ref_tensor)
            q_embed = self._module.embed(q_tensor)
            similarity = torch.cosine_similarity(ref_embed, q_embed).item()
        similarity = max(0.0, min(1.0, float(similarity)))
        verdict = self._verdict(similarity)
        latency_ms = (time.perf_counter() - started) * 1000.0
        return {
            "model": self.MODEL_NAME,
            "model_version": self.settings.model_version,
            "similarity": round(similarity, 6),
            "threshold": self.settings.threshold,
            "verdict": verdict,
            "device": self._device,
            "processing_time_ms": round(latency_ms, 3),
            "backbone": self.BACKBONE,
            "model_hash": self._file_hash,
        }

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=self.MODEL_NAME,
            version=self.settings.model_version,
            author="AI-FORGE Engineering",
            framework=ModelFramework.PYTORCH,
            license="Proprietary",
            input_type=InputType.IMAGE,
            output_type=OutputType.EMBEDDING,
            model_hash=self._file_hash or "",
            training_dataset="user-provided-signature-pairs",
            supported_tasks=("signature-verification",),
            required_device=DeviceRequirement.ANY,
            description=(
                "Siamese signature verification model using EfficientNet-B0 "
                "with contrastive training."
            ),
            tags=("signature", "siamese", "efficientnet-b0"),
            extra={"backbone": self.BACKBONE, "threshold": self.settings.threshold},
        )

    def supports(self, task: str) -> bool:
        return task in self.metadata().supported_tasks

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "device": self._device,
            "status": "healthy" if self._loaded else "unavailable",
            "reason": self._load_error,
            "model_path_configured": bool(self.settings.model_path),
            "integrity_verified": bool(self._file_hash),
        }

    def version(self) -> str:
        return self.settings.model_version

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _verdict(self, similarity: float) -> str:
        threshold = self.settings.threshold
        margin = self.settings.inconclusive_margin
        if similarity >= threshold:
            return "MATCH"
        if similarity <= threshold - margin:
            return "NON_MATCH"
        return "INCONCLUSIVE"

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
