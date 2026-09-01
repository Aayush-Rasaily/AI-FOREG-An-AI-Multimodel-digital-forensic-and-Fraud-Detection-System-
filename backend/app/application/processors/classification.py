"""Safe broad file classification processor."""

import json

from backend.app.application.processors.base import (
    DerivedArtifactPayload,
    ProcessorContext,
    ProcessorResult,
)
from backend.app.core.config import Settings
from backend.app.domain.processing import ArtifactType, EvidenceClassification


class FileClassificationProcessor:
    """Classify using stored extension and MIME policy, never client MIME alone."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def can_process(self, context: ProcessorContext) -> bool:
        """Run after integrity inspection has succeeded."""

        return context.inspection is not None

    async def process(self, context: ProcessorContext) -> ProcessorResult:
        """Derive a broad category from independently stored evidence facts."""

        inspection = context.inspection
        if inspection is None:
            return ProcessorResult(classification=EvidenceClassification.UNKNOWN)

        configured_category = next(
            (
                category
                for category, extensions in self.settings.supported_extensions.items()
                if inspection.extension
                in {item.lower().lstrip(".") for item in extensions}
            ),
            None,
        )
        mime_category = next(
            (
                category
                for category, mimes in self.settings.supported_mime_types.items()
                if inspection.mime_type in {item.lower() for item in mimes}
            ),
            None,
        )
        category = configured_category if configured_category == mime_category else None
        classification = {
            "image": EvidenceClassification.IMAGE,
            "document": EvidenceClassification.DOCUMENT,
            "video": EvidenceClassification.VIDEO,
            "audio": EvidenceClassification.AUDIO,
        }.get(category or "", EvidenceClassification.UNKNOWN)
        payload: dict[str, object] = {
            "classification": classification.value,
            "extension": inspection.extension,
            "mime_type": inspection.mime_type,
        }
        return ProcessorResult(
            classification=classification,
            artifacts=(
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.CLASSIFICATION,
                    mime_type="application/json",
                    content=json.dumps(payload, sort_keys=True).encode("utf-8"),
                    metadata=payload,
                ),
            ),
        )
