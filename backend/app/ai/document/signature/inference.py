"""Signature inference helpers."""

from __future__ import annotations

from typing import Any

from backend.app.ai.document.signature.config import SignatureAISettings
from backend.app.ai.document.signature.model import SiameseSignatureModel
from backend.app.ai.document.signature.preprocessing import preprocess_signature_image


class SignatureInferenceEngine:
    """Run Siamese signature verification through the Phase 6A model contract."""

    def __init__(
        self,
        model: SiameseSignatureModel | None = None,
        settings: SignatureAISettings | None = None,
    ) -> None:
        self.settings = settings or SignatureAISettings()
        self.model = model or SiameseSignatureModel(self.settings)

    def ensure_loaded(self, *, device: str) -> None:
        if not self.model.is_loaded:
            self.model.load(device=device)

    async def verify_pair(
        self,
        reference_bytes: bytes,
        questioned_bytes: bytes,
        *,
        device: str,
    ) -> dict[str, Any]:
        self.ensure_loaded(device=device)
        reference = preprocess_signature_image(reference_bytes)
        questioned = preprocess_signature_image(questioned_bytes)
        return await self.model.predict(
            {"reference": reference, "questioned": questioned},
        )
