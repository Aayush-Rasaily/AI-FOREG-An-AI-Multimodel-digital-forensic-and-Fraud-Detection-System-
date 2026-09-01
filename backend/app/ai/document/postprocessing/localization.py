"""Localization helpers for document AI findings."""

from __future__ import annotations

from backend.app.ai.document.models.schemas import DocumentFindingRegionResponse
from backend.app.forensics.models import RegionBox


def regions_to_responses(
    regions: tuple[RegionBox, ...],
) -> list[DocumentFindingRegionResponse]:
    """Convert domain regions to API responses."""

    responses: list[DocumentFindingRegionResponse] = []
    for region in regions:
        normalized = region.normalized
        responses.append(
            DocumentFindingRegionResponse(
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
                page_number=region.page_number,
                frame_number=region.frame_number,
                polygon=list(region.polygon) if region.polygon else None,
                normalized_location=(
                    {
                        "x": normalized.x,
                        "y": normalized.y,
                        "width": normalized.width,
                        "height": normalized.height,
                    }
                    if normalized is not None
                    else None
                ),
            )
        )
    return responses
