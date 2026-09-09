"""Thread-safe singleton loader for the packaged Siamese signature model."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LoadedSignatureWeights:
    """Process-wide loaded Siamese network and integrity metadata."""

    module: Any
    device: str
    path: str
    file_hash: str


class SignatureModelLoader:
    """Lazy, once-per-process loader for Siamese signature weights.

    The checkpoint is a timm EfficientNet-B0 encoder with a 256-d projection
    head (`encoder.backbone.*` + `encoder.embedding.*`). Architecture must
    match those keys exactly; torchvision EfficientNet will not load.
    """

    _lock = threading.RLock()
    _cache: LoadedSignatureWeights | None = None
    _load_error: str | None = None

    @classmethod
    def reset_for_tests(cls) -> None:
        """Clear the process cache (unit tests only)."""

        with cls._lock:
            cls._cache = None
            cls._load_error = None

    @classmethod
    def last_error(cls) -> str | None:
        return cls._load_error

    @classmethod
    def get_or_load(
        cls,
        *,
        model_path: str,
        device: str,
        file_hash: str,
    ) -> LoadedSignatureWeights | None:
        """Return the shared module, loading it once if needed.

        Returns ``None`` when load fails; call :meth:`last_error` for details.
        Does not raise for missing deps or corrupt weights — callers map that
        to UNAVAILABLE. Integrity mismatches are handled by the caller before
        invoking this method.
        """

        resolved_device = cls.resolve_device(device)
        with cls._lock:
            if (
                cls._cache is not None
                and cls._cache.path == model_path
                and cls._cache.file_hash == file_hash
            ):
                if cls._cache.device != resolved_device:
                    try:
                        cls._cache.module.to(resolved_device)
                        cls._cache = LoadedSignatureWeights(
                            module=cls._cache.module,
                            device=resolved_device,
                            path=cls._cache.path,
                            file_hash=cls._cache.file_hash,
                        )
                    except Exception as exc:  # noqa: BLE001 — stay unavailable
                        cls._load_error = (
                            "Failed to move signature model to "
                            f"'{resolved_device}': {exc}"
                        )
                        logger.exception("Signature model device move failed")
                        return None
                return cls._cache

            try:
                module = cls._build_and_load(Path(model_path), resolved_device)
            except Exception as exc:  # noqa: BLE001 — map to UNAVAILABLE
                cls._load_error = str(exc)
                cls._cache = None
                logger.exception(
                    "Failed to load Siamese signature model from %s",
                    model_path,
                )
                return None

            cls._load_error = None
            cls._cache = LoadedSignatureWeights(
                module=module,
                device=resolved_device,
                path=model_path,
                file_hash=file_hash,
            )
            logger.info(
                "Loaded Siamese signature model from %s on %s (sha256=%s…)",
                model_path,
                resolved_device,
                file_hash[:12],
            )
            return cls._cache

    @staticmethod
    def resolve_device(requested: str) -> str:
        normalized = (requested or "cpu").strip().lower()
        if normalized in {"cuda", "gpu"}:
            try:
                import torch

                if torch.cuda.is_available():
                    return "cuda"
            except ImportError:
                pass
            return "cpu"
        if normalized in {"auto", "any"}:
            try:
                import torch

                if torch.cuda.is_available():
                    return "cuda"
            except ImportError:
                pass
            return "cpu"
        return "cpu"

    @staticmethod
    def _build_and_load(path: Path, device: str) -> Any:
        try:
            import timm
            import torch
            from torch import nn
        except ImportError as exc:
            raise RuntimeError(
                "PyTorch and timm are required for signature verification.",
            ) from exc

        class SignatureEncoder(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.backbone = timm.create_model(
                    "efficientnet_b0",
                    pretrained=False,
                    num_classes=0,
                    global_pool="avg",
                )
                self.embedding = nn.Sequential(
                    nn.Linear(1280, 256),
                    nn.ReLU(),
                    nn.Dropout(0.0),
                    nn.Linear(256, 256),
                )

            def forward(self, tensor: torch.Tensor) -> torch.Tensor:
                features = self.backbone(tensor)
                return self.embedding(features)

        class SiameseNet(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.encoder = SignatureEncoder()

            def embed(self, tensor: torch.Tensor) -> torch.Tensor:
                embedding = self.encoder(tensor)
                return nn.functional.normalize(embedding, p=2, dim=1)

        state = torch.load(path, map_location=device, weights_only=True)
        if not isinstance(state, dict):
            raise RuntimeError(
                "Signature checkpoint must be a state_dict mapping.",
            )
        # Allow accidental wrapping under common checkpoint keys.
        if "encoder.backbone.conv_stem.weight" not in state:
            for key in ("state_dict", "model", "model_state_dict"):
                nested = state.get(key) if isinstance(state, dict) else None
                if isinstance(nested, dict) and (
                    "encoder.backbone.conv_stem.weight" in nested
                ):
                    state = nested
                    break

        model = SiameseNet()
        model.load_state_dict(state, strict=True)
        model.to(device)
        model.eval()
        return model
