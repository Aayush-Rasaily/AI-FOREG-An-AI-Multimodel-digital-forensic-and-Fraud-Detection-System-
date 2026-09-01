"""Frame-level localization helpers."""

from __future__ import annotations

from backend.app.ai.video.models.base import VideoFrameReference
from backend.app.forensics.models import RegionBox
from backend.app.forensics.utils import region_from_pixels


def localize_on_frame(
    *,
    frame: VideoFrameReference,
    x: float,
    y: float,
    width: float,
    height: float,
) -> RegionBox:
    """Attach frame metadata to a spatial region."""

    source_width = frame.width or int(max(x + width, 1))
    source_height = frame.height or int(max(y + height, 1))
    region = region_from_pixels(x, y, width, height, source_width, source_height)
    return RegionBox(
        x=region.x,
        y=region.y,
        width=region.width,
        height=region.height,
        page_number=None,
        frame_number=frame.frame_number,
        polygon=region.polygon,
        normalized=region.normalized,
    )
