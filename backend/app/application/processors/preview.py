"""Safe preview derivative processor."""

import json

from backend.app.application.processors.base import (
    DerivedArtifactPayload,
    ProcessorContext,
    ProcessorResult,
)
from backend.app.domain.processing import ArtifactType


class PreviewProcessor:
    """Create a deterministic preview manifest without touching the original."""

    def can_process(self, context: ProcessorContext) -> bool:
        """Run only after verified inspection and classification."""

        return context.inspection is not None

    async def process(self, context: ProcessorContext) -> ProcessorResult:
        """Persist a safe preview descriptor for future media-specific adapters."""

        inspection = context.inspection
        if inspection is None:
            return ProcessorResult()
        preview_manifest: dict[str, object] = {
            "preview_kind": "metadata_manifest",
            "binary_preview_generated": False,
            "classification": context.classification.value,
            "source_filename": context.evidence.original_filename,
            "source_sha256": inspection.sha256_hash,
            "source_size": inspection.file_size,
            "note": "Binary previews require a format-specific safe adapter.",
        }
        return ProcessorResult(
            artifacts=(
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.PREVIEW,
                    mime_type="application/json",
                    content=json.dumps(
                        preview_manifest,
                        sort_keys=True,
                    ).encode("utf-8"),
                    metadata={"preview_kind": "metadata_manifest"},
                ),
            ),
        )
