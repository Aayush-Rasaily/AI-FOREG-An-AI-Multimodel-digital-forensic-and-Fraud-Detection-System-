"""Localization helpers for forensic findings."""

from backend.app.forensics.models import FindingItem, RegionBox
from backend.app.forensics.schemas import FindingRegionResponse


def regions_to_responses(
    regions: tuple[RegionBox, ...],
) -> list[FindingRegionResponse]:
    """Map internal region boxes to API responses."""

    responses: list[FindingRegionResponse] = []
    for region in regions:
        responses.append(
            FindingRegionResponse(
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
                page_number=region.page_number,
                frame_number=region.frame_number,
                polygon=list(region.polygon) if region.polygon else None,
                normalized_location=(
                    {
                        "x": region.normalized.x,
                        "y": region.normalized.y,
                        "width": region.normalized.width,
                        "height": region.normalized.height,
                    }
                    if region.normalized
                    else None
                ),
            )
        )
    return responses


def primary_region(finding: FindingItem) -> RegionBox | None:
    """Return the first localized region for a finding."""

    return finding.regions[0] if finding.regions else None
