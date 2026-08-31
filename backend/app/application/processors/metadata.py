"""Safe basic metadata extraction processor."""

import json

from backend.app.application.processors.base import (
    DerivedArtifactPayload,
    ProcessorContext,
    ProcessorResult,
)
from backend.app.domain.processing import ArtifactType


class MetadataProcessor:
    """Extract registered file facts without forensic interpretation."""

    def can_process(self, context: ProcessorContext) -> bool:
        """Run only after the original has passed integrity inspection."""

        return context.inspection is not None

    async def process(self, context: ProcessorContext) -> ProcessorResult:
        """Create a deterministic metadata artifact from verified facts."""

        inspection = context.inspection
        if inspection is None:
            return ProcessorResult()
        metadata: dict[str, object] = {
            "filename": context.evidence.original_filename,
            "extension": inspection.extension,
            "mime_type": inspection.mime_type,
            "file_size": inspection.file_size,
            "sha256_hash": inspection.sha256_hash,
            "metadata_scope": "basic_registered_file_facts",
        }
        return ProcessorResult(
            metadata=metadata,
            artifacts=(
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.METADATA,
                    mime_type="application/json",
                    content=json.dumps(metadata, sort_keys=True).encode("utf-8"),
                    metadata={"scope": "basic_registered_file_facts"},
                ),
            ),
        )
