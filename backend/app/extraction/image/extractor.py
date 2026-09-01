"""Pillow-backed image inspection and optional OCR extraction."""

import asyncio
import json
from typing import Any

from PIL import Image
from PIL.Image import DecompressionBombError, UnidentifiedImageError

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType
from backend.app.extraction.exceptions import ExtractionError
from backend.app.extraction.models import (
    BoundingBox,
    ExtractionContext,
    ExtractionItem,
    ExtractionResult,
    ExtractionSourceType,
    ExtractionStatus,
    ExtractionType,
    normalize_bbox,
)


class ImageExtractor:
    """Extract image facts and only provider-backed OCR regions."""

    extensions = frozenset({"jpg", "jpeg", "png", "webp", "tif", "tiff"})

    def can_extract(self, context: ExtractionContext) -> bool:
        """Support configured image extensions and image MIME values."""

        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return extension in self.extensions or context.mime_type.startswith("image/")

    async def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Read image headers without modifying the source object."""

        try:
            async with context.storage.open(context.storage_key) as stream:
                image = await asyncio.to_thread(Image.open, stream)
                try:
                    width, height = image.size
                    image_format = image.format or "UNKNOWN"
                    mode = image.mode
                    basic_metadata = {
                        str(key): value
                        for key, value in image.info.items()
                        if isinstance(value, (str, int, float, bool))
                        and len(str(value)) <= 256
                    }
                    items = [
                        ExtractionItem(
                            evidence_id=context.evidence_id,
                            source_type=ExtractionSourceType.ORIGINAL,
                            source_identifier=context.original_filename,
                            extraction_type=ExtractionType.METADATA,
                            content=json.dumps(
                                {
                                    "width": width,
                                    "height": height,
                                    "format": image_format,
                                    "mode": mode,
                                    "metadata": basic_metadata,
                                },
                                sort_keys=True,
                            ),
                            method="pillow_image_inspection",
                            version="1.0",
                            metadata={
                                "width": width,
                                "height": height,
                                "format": image_format,
                                "mode": mode,
                                "metadata": basic_metadata,
                            },
                        )
                    ]
                    metadata: dict[str, Any] = {
                        "width": width,
                        "height": height,
                        "format": image_format,
                        "mode": mode,
                        "ocr_status": "DISABLED",
                    }
                    artifacts = [
                        DerivedArtifactPayload(
                            artifact_type=ArtifactType.IMAGE_REGIONS,
                            mime_type="application/json",
                            content=json.dumps(
                                {
                                    "regions": [],
                                    "source_width": width,
                                    "source_height": height,
                                    "detector": None,
                                },
                                sort_keys=True,
                            ).encode("utf-8"),
                            metadata={"regions_detected": 0},
                        )
                    ]
                    status = ExtractionStatus.SUCCEEDED
                    error_code = None
                    error_message = None
                    if context.ocr_provider.enabled:
                        if not context.ocr_provider.available:
                            status = ExtractionStatus.PARTIAL
                            metadata["ocr_status"] = "UNAVAILABLE"
                            error_code = "OCR_UNAVAILABLE"
                            error_message = (
                                "The configured OCR executable is unavailable."
                            )
                        else:
                            try:
                                words = await context.ocr_provider.extract_words(image)
                                if len(words) > context.settings.extraction_max_items:
                                    words = words[
                                        : context.settings.extraction_max_items
                                    ]
                                    metadata["ocr_items_limited"] = True
                                metadata["ocr_status"] = "SUCCEEDED"
                                for word in words:
                                    bbox = BoundingBox(
                                        x=float(word["x"]),
                                        y=float(word["y"]),
                                        width=float(word["width"]),
                                        height=float(word["height"]),
                                    )
                                    items.append(
                                        ExtractionItem(
                                            evidence_id=context.evidence_id,
                                            source_type=ExtractionSourceType.ORIGINAL,
                                            source_identifier=context.original_filename,
                                            extraction_type=ExtractionType.WORD,
                                            content=str(word["text"]),
                                            method="tesseract_ocr",
                                            version="1.0",
                                            confidence=float(word["confidence"]),
                                            bbox=bbox,
                                            normalized_bbox=normalize_bbox(
                                                bbox,
                                                width,
                                                height,
                                            ),
                                            metadata={"provider": "tesseract"},
                                        )
                                    )
                                artifacts.append(
                                    DerivedArtifactPayload(
                                        artifact_type=ArtifactType.OCR_RESULT,
                                        mime_type="application/json",
                                        content=json.dumps(
                                            {"words": words},
                                            sort_keys=True,
                                        ).encode("utf-8"),
                                        metadata={"provider": "tesseract"},
                                    )
                                )
                            except Exception as exc:
                                status = ExtractionStatus.PARTIAL
                                metadata["ocr_status"] = "UNAVAILABLE"
                                error_code = getattr(exc, "code", "OCR_FAILED")
                                error_message = (
                                    "The OCR provider could not process the image."
                                )
                    return ExtractionResult(
                        status=status,
                        items=tuple(items),
                        artifacts=tuple(artifacts),
                        metadata=metadata,
                        error_code=error_code,
                        error_message_safe=error_message,
                    )
                finally:
                    image.close()
        except (DecompressionBombError, UnidentifiedImageError, OSError) as exc:
            raise ExtractionError(
                "IMAGE_EXTRACTION_FAILED",
                "The image could not be safely inspected.",
            ) from exc
