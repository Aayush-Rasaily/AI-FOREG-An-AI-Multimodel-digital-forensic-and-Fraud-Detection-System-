"""Signature inference helpers."""

from __future__ import annotations

import logging
import threading
from typing import Any

from backend.app.ai.document.signature.config import SignatureAISettings
from backend.app.ai.document.signature.loader import SignatureModelLoader
from backend.app.ai.document.signature.model import (
    ModelIntegrityError,
    SiameseSignatureModel,
)
from backend.app.ai.document.signature.preprocessing import preprocess_signature_image

logger = logging.getLogger(__name__)


class SignatureInferenceEngine:
    """Run Siamese signature verification through the Phase 6A model contract."""

    _ensure_lock = threading.Lock()

    def __init__(
        self,
        model: SiameseSignatureModel | None = None,
        settings: SignatureAISettings | None = None,
    ) -> None:
        self.settings = settings or SignatureAISettings()
        self.model = model or SiameseSignatureModel(self.settings)

    def ensure_loaded(self, *, device: str) -> None:
        """Load weights once; concurrent callers share the process singleton."""

        requested = device
        if self.settings.enable_gpu and requested in {"cpu", "auto", "any"}:
            requested = "auto"
        elif not self.settings.enable_gpu:
            requested = "cpu"
        with self._ensure_lock:
            if self.model.is_loaded:
                return
            try:
                self.model.load(device=requested)
            except ModelIntegrityError:
                logger.exception(
                    "Signature model integrity check failed; returning UNAVAILABLE",
                )
                return

    async def verify_pair(
        self,
        reference_bytes: bytes,
        questioned_bytes: bytes,
        *,
        device: str,
    ) -> dict[str, Any]:
        self.ensure_loaded(device=device)
        if not self.model.is_loaded:
            return await self.model.predict({})
        reference = preprocess_signature_image(reference_bytes)
        questioned = preprocess_signature_image(questioned_bytes)
        return await self.model.predict(
            {"reference": reference, "questioned": questioned},
        )

    def reset_cache_for_tests(self) -> None:
        """Drop process-wide weights (tests only)."""

        SignatureModelLoader.reset_for_tests()
        self.model.unload()
