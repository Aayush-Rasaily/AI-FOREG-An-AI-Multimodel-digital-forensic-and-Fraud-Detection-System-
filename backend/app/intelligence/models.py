"""Domain enums and constants for investigation intelligence."""

from __future__ import annotations

from enum import StrEnum

ENGINE_VERSION = "8c.1.0"
POLICY_VERSION = "8c.1.0"


class CaseRiskLevel(StrEnum):
    """Overall case risk classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationCode(StrEnum):
    """Deterministic recommendation identifiers."""

    ACQUIRE_ORIGINAL = "acquire_original_media"
    HIGHER_RESOLUTION = "obtain_higher_resolution"
    VERIFY_SIGNATURE = "verify_signature_manually"
    INTERVIEW_SOURCE = "interview_document_source"
    RECOVER_METADATA = "recover_deleted_metadata"
    COLLECT_REFERENCE = "collect_reference_recording"
    ACQUIRE_CCTV = "acquire_cctv"
    EXPORT_REPORT = "export_report"
    RUN_ANALYSIS = "complete_missing_analyses"
    REVIEW_CORRELATIONS = "review_cross_evidence_links"
