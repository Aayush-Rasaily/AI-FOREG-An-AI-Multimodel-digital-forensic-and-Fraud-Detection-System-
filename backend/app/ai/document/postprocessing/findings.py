"""Normalize document detector outputs into findings."""

from __future__ import annotations

from backend.app.ai.document.models.base import (
    DocumentAIFindingItem,
    DocumentDetectorOutput,
)


def normalize_detector_output(
    output: DocumentDetectorOutput,
) -> tuple[DocumentAIFindingItem, ...]:
    """Ensure every finding includes method and model metadata."""

    normalized: list[DocumentAIFindingItem] = []
    for finding in output.findings:
        normalized.append(
            DocumentAIFindingItem(
                detector=finding.detector or output.detector,
                category=finding.category,
                severity=finding.severity,
                description=finding.description,
                explanation=finding.explanation,
                method=finding.method,
                confidence=finding.confidence,
                regions=finding.regions,
                recommendation=finding.recommendation,
                metadata={
                    **finding.metadata,
                    "detector_version": output.version,
                },
                model_name=finding.model_name or output.model_name,
                model_version=finding.model_version or output.model_version,
                model_framework=finding.model_framework,
                capability_status=finding.capability_status,
            )
        )
    return tuple(normalized)
