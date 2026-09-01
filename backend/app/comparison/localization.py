"""Localization helpers for comparison differences."""

from backend.app.comparison.models import DifferenceItem, RegionBox
from backend.app.comparison.schemas import DifferenceRegionResponse


def regions_to_responses(
    regions: tuple[RegionBox, ...],
) -> list[DifferenceRegionResponse]:
    """Map internal region boxes to API responses."""

    responses: list[DifferenceRegionResponse] = []
    for region in regions:
        responses.append(
            DifferenceRegionResponse(
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


def primary_region(difference: DifferenceItem) -> RegionBox | None:
    """Return the first localized region for a difference."""

    return difference.regions[0] if difference.regions else None
