"""Metadata comparison matcher."""

from backend.app.comparison.models import (
    ComparisonContext,
    DifferenceItem,
    DifferenceSeverity,
    DifferenceType,
    MatcherResult,
)
from backend.app.comparison.utils import load_bytes_from_storage, safe_exif


class MetadataMatcher:
    """Compare producer, creator, dates, and EXIF metadata fields."""

    name = "metadata"
    version = "1.0"

    def can_compare(self, context: ComparisonContext) -> bool:
        return True

    async def compare(self, context: ComparisonContext) -> MatcherResult:
        differences = await _compare_metadata(context)
        return MatcherResult(
            matcher=self.name,
            version=self.version,
            differences=tuple(differences),
            metadata={"difference_count": len(differences)},
        )


async def _compare_metadata(context: ComparisonContext) -> list[DifferenceItem]:
    max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
    ref_meta = dict(context.reference_metadata)
    q_meta = dict(context.questioned_metadata)
    differences: list[DifferenceItem] = []
    tracked_fields = (
        "producer",
        "creator",
        "mod_date",
        "creation_date",
        "software",
        "orientation",
        "dpi",
        "resolution",
        "gps",
        "camera",
    )
    for field in tracked_fields:
        ref_value = ref_meta.get(field)
        q_value = q_meta.get(field)
        if ref_value is None and q_value is None:
            continue
        if str(ref_value) != str(q_value):
            differences.append(
                DifferenceItem(
                    matcher="metadata",
                    difference_type=DifferenceType.METADATA_CHANGED,
                    severity=DifferenceSeverity.MEDIUM,
                    confidence=0.85,
                    description=f"Metadata field '{field}' differs from reference.",
                    explanation=(
                        f"Reference reports {ref_value!s}; "
                        f"submitted reports {q_value!s}."
                    ),
                    original_value=str(ref_value) if ref_value is not None else None,
                    submitted_value=str(q_value) if q_value is not None else None,
                    metadata={"field": field},
                )
            )
    if context.questioned_mime_type.startswith("image/"):
        ref_bytes = await load_bytes_from_storage(
            context.storage,
            context.reference_storage_key,
            max_bytes=max_bytes,
        )
        q_bytes = await load_bytes_from_storage(
            context.storage,
            context.questioned_storage_key,
            max_bytes=max_bytes,
        )
        ref_exif = safe_exif(ref_bytes)
        q_exif = safe_exif(q_bytes)
        for key in set(ref_exif) | set(q_exif):
            if ref_exif.get(key) != q_exif.get(key):
                differences.append(
                    DifferenceItem(
                        matcher="metadata",
                        difference_type=DifferenceType.METADATA_CHANGED,
                        severity=DifferenceSeverity.LOW,
                        confidence=0.8,
                        description=f"EXIF field '{key}' differs from reference.",
                        explanation=(
                            f"Reference EXIF {key}={ref_exif.get(key)!s}; "
                            f"submitted {q_exif.get(key)!s}."
                        ),
                        original_value=str(ref_exif.get(key)),
                        submitted_value=str(q_exif.get(key)),
                        metadata={"exif_key": key},
                    )
                )
    return differences
