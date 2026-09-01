"""Image metadata consistency detector."""

import asyncio

from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    Severity,
)
from backend.app.forensics.utils import safe_exif


class ImageMetadataDetector:
    """Inspect EXIF and image header metadata for inconsistencies."""

    name = "image_metadata"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        return context.classification == EvidenceClassification.IMAGE

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        async with context.storage.open(context.storage_key) as stream:
            data = await asyncio.to_thread(stream.read, max_bytes + 1)
        exif = await asyncio.to_thread(safe_exif, data)
        findings: list[FindingItem] = []
        if not exif:
            findings.append(
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.METADATA,
                    severity=Severity.INFO,
                    confidence=0.7,
                    description="No EXIF metadata block was present.",
                    explanation=(
                        "The image contains no embedded EXIF metadata. "
                        "This is common after re-encoding or export."
                    ),
                    metadata={"exif_present": False},
                )
            )
        else:
            software = exif.get("305") or exif.get("Software")
            orientation = exif.get("274") or exif.get("Orientation")
            if software:
                findings.append(
                    FindingItem(
                        detector=self.name,
                        category=FindingCategory.METADATA,
                        severity=Severity.INFO,
                        confidence=0.85,
                        description="Editing software metadata is present.",
                        explanation=f"Software field reports: {software}",
                        metadata={"software": software},
                    )
                )
            if orientation and str(orientation) not in {"1", "Horizontal (normal)"}:
                findings.append(
                    FindingItem(
                        detector=self.name,
                        category=FindingCategory.METADATA,
                        severity=Severity.LOW,
                        confidence=0.8,
                        description="Non-default orientation metadata detected.",
                        explanation=f"Orientation value: {orientation}",
                        metadata={"orientation": orientation},
                    )
                )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=tuple(findings),
            metadata={"exif_fields": len(exif)},
        )
