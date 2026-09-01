"""Region preprocessing helpers for document AI analysis."""

from __future__ import annotations

from typing import Any


def record_to_bbox(record: dict[str, Any]) -> dict[str, float] | None:
    """Build a bbox dict from an extraction record."""

    bbox = record.get("bbox")
    if isinstance(bbox, dict):
        return {
            "x": float(bbox.get("x", 0)),
            "y": float(bbox.get("y", 0)),
            "width": float(bbox.get("width", 0)),
            "height": float(bbox.get("height", 0)),
        }
    keys = ("bbox_x", "bbox_y", "bbox_width", "bbox_height")
    if all(record.get(key) is not None for key in keys):
        return {
            "x": float(record["bbox_x"]),
            "y": float(record["bbox_y"]),
            "width": float(record["bbox_width"]),
            "height": float(record["bbox_height"]),
        }
    return None


def extraction_record_dict(record: Any) -> dict[str, Any]:
    """Convert an ORM extraction record to a detector-friendly dict."""

    bbox = None
    if record.bbox_x is not None:
        bbox = {
            "x": record.bbox_x,
            "y": record.bbox_y,
            "width": record.bbox_width,
            "height": record.bbox_height,
        }
    return {
        "id": str(record.id),
        "extraction_type": record.extraction_type.value,
        "content": record.content,
        "page_number": record.page_number,
        "frame_number": record.frame_number,
        "confidence": record.confidence,
        "metadata": record.metadata_json,
        "bbox": bbox,
    }
