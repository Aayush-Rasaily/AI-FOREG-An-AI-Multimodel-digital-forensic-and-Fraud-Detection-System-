"""Provenance and related-artifact presence validation."""

from __future__ import annotations

from typing import Any


def missing_provenance_signals(item: dict[str, Any]) -> list[str]:
    """Return missing provenance signals for one evidence item."""

    missing: list[str] = []
    if not item.get("sha256_hash"):
        missing.append("sha256_hash")
    if not item.get("storage_key"):
        missing.append("storage_key")
    if not item.get("evidence_number"):
        missing.append("evidence_number")
    return missing


def has_audit_coverage(evidence_id: str, audit_evidence_ids: set[str]) -> bool:
    return evidence_id in audit_evidence_ids
