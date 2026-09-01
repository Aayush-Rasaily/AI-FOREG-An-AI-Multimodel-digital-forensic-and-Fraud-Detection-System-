"""Convert detector outputs into AI-FORGE image findings."""

from __future__ import annotations

from typing import Any

from backend.app.ai.image.models import ImageAIFindingItem, ImageDetectorOutput


def normalize_detector_output(
    output: ImageDetectorOutput,
) -> tuple[ImageAIFindingItem, ...]:
    """Ensure every finding includes model metadata references."""

    normalized: list[ImageAIFindingItem] = []
    for item in output.findings:
        metadata = dict(item.metadata)
        metadata.setdefault("detector_version", output.version)
        normalized.append(
            ImageAIFindingItem(
                detector=item.detector,
                category=item.category,
                severity=item.severity,
                confidence=item.confidence,
                description=item.description,
                explanation=item.explanation,
                regions=item.regions,
                recommendation=item.recommendation,
                metadata=metadata,
                model_name=item.model_name or output.model_name,
                model_version=item.model_version or output.model_version,
                model_framework=item.model_framework,
                heatmap_artifact_key=item.heatmap_artifact_key,
                mask_artifact_key=item.mask_artifact_key,
            )
        )
    return tuple(normalized)


def findings_to_dict(items: tuple[ImageAIFindingItem, ...]) -> list[dict[str, Any]]:
    """Serialize findings for JSON artifact storage."""

    payload: list[dict[str, Any]] = []
    for item in items:
        payload.append(
            {
                "detector": item.detector,
                "category": item.category.value,
                "severity": item.severity.value,
                "confidence": item.confidence,
                "description": item.description,
                "explanation": item.explanation,
                "recommendation": item.recommendation,
                "model_name": item.model_name,
                "model_version": item.model_version,
                "model_framework": item.model_framework,
                "metadata": item.metadata,
                "regions": [
                    {
                        "x": region.x,
                        "y": region.y,
                        "width": region.width,
                        "height": region.height,
                    }
                    for region in item.regions
                ],
            }
        )
    return payload
