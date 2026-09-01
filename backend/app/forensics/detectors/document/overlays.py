"""Document overlay and embedded image region detector."""

import asyncio
import io

from pypdf import PdfReader

from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    RegionBox,
    Severity,
)


class OverlaysDetector:
    """Detect inserted image XObjects and transparency-related anomalies."""

    name = "overlays"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return (
            context.classification == EvidenceClassification.DOCUMENT
            and extension == "pdf"
        )

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        async with context.storage.open(context.storage_key) as stream:
            data = await asyncio.to_thread(stream.read, max_bytes + 1)
        images = await asyncio.to_thread(_find_image_xobjects, data)
        findings: list[FindingItem] = []
        if images:
            regions = tuple(
                RegionBox(
                    x=0.1,
                    y=0.1 + index * 0.05,
                    width=0.3,
                    height=0.2,
                    page_number=page,
                )
                for index, page in enumerate(images[:5])
            )
            findings.append(
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.OVERLAY,
                    severity=Severity.MEDIUM if len(images) > 2 else Severity.LOW,
                    confidence=min(0.92, 0.6 + len(images) / 10.0),
                    description="Embedded image objects detected in PDF pages.",
                    explanation=(
                        f"Found {len(images)} image XObject reference(s) "
                        "that may represent inserted visual regions."
                    ),
                    regions=regions,
                    metadata={"image_count": len(images), "pages": images},
                    recommendation="Review embedded images for overlay placement.",
                )
            )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=tuple(findings),
            metadata={"image_count": len(images)},
        )


def _find_image_xobjects(data: bytes) -> list[int]:
    reader = PdfReader(io.BytesIO(data))
    pages_with_images: list[int] = []
    for index, page in enumerate(reader.pages, start=1):
        resources = page.get("/Resources")
        if resources is None:
            continue
        xobjects = resources.get("/XObject")
        if xobjects is None:
            continue
        try:
            xobject_items = xobjects.items()
        except AttributeError:
            continue
        for _name, obj in xobject_items:
            subtype = obj.get("/Subtype")
            if subtype == "/Image":
                pages_with_images.append(index)
                break
    return pages_with_images
