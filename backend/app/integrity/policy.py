"""Deterministic policy for Phase 9F integrity monitoring."""

from __future__ import annotations

IM_ENGINE_VERSION = "9f.1.0"
IM_POLICY_VERSION = "1.0"

CHECK_CODES: tuple[tuple[str, str], ...] = (
    ("SHA256_CONSISTENCY", "SHA-256 Consistency"),
    ("FILE_SIZE_CONSISTENCY", "File Size Consistency"),
    ("MIME_CONSISTENCY", "MIME Consistency"),
    ("METADATA_DRIFT", "Metadata Drift"),
    ("TIMESTAMP_CONSISTENCY", "Timestamp Consistency"),
    ("CUSTODY_CONTINUITY", "Chain-of-Custody Continuity"),
    ("STORAGE_LOCATION", "Storage Location Verification"),
    ("DUPLICATE_DETECTION", "Duplicate Detection"),
    ("MISSING_PROVENANCE", "Missing Provenance"),
    ("MISSING_AUDIT", "Missing Audit Entries"),
    ("MISSING_AI_ARTIFACTS", "Missing AI Artifacts"),
    ("MISSING_REPORTS", "Missing Reports"),
)

SEVERITY_ORDER: dict[str, int] = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFO": 4,
}
