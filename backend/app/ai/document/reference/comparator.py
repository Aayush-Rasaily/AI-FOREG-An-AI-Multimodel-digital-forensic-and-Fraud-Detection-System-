"""Reference document comparison integration for document AI."""

from __future__ import annotations

from typing import Any
from uuid import UUID


class ReferenceDocumentComparator:
    """Bridge Phase 5C comparison differences into document AI findings."""

    @staticmethod
    def differences_to_records(
        differences: list[Any],
    ) -> tuple[dict[str, Any], ...]:
        records: list[dict[str, Any]] = []
        for item in differences:
            records.append(
                {
                    "id": str(item.id),
                    "matcher": item.matcher,
                    "difference_type": item.difference_type.value,
                    "severity": item.severity.value,
                    "confidence": item.confidence,
                    "description": item.description,
                    "explanation": item.explanation,
                    "metadata": item.metadata_json,
                }
            )
        return tuple(records)

    @staticmethod
    def summary_metadata(
        evidence_id: UUID,
        comparison_run_id: UUID | None,
        differences_count: int,
    ) -> dict[str, Any]:
        return {
            "questioned_evidence_id": str(evidence_id),
            "comparison_run_id": str(comparison_run_id) if comparison_run_id else None,
            "differences_count": differences_count,
        }
