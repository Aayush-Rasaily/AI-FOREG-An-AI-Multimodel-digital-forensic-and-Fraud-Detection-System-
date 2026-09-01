"""Domain models for multimodal fusion and AI jury."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from backend.app.forensics.models import Severity


class Modality(StrEnum):
    """Supported evidence modalities for fusion."""

    FORENSICS = "forensics"
    IMAGE_AI = "image_ai"
    DOCUMENT_AI = "document_ai"
    SIGNATURE_AI = "signature_ai"
    VIDEO_AI = "video_ai"
    AUDIO_AI = "audio_ai"
    COMPARISON = "comparison"


class ModalityAvailability(StrEnum):
    """Availability state for one modality."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class FindingVerdict(StrEnum):
    """Normalized verdict for one finding."""

    SUPPORTS_GENUINE = "supports_genuine"
    SUPPORTS_SUSPICIOUS = "supports_suspicious"
    SUPPORTS_FRAUD = "supports_fraud"
    INCONCLUSIVE = "inconclusive"
    UNAVAILABLE = "unavailable"
    NEUTRAL = "neutral"


class JuryMemberRole(StrEnum):
    """Independent jury assessment roles."""

    FORENSIC_ANALYST = "forensic_analyst"
    DOCUMENT_IMAGE_SPECIALIST = "document_image_specialist"
    MULTIMEDIA_SPECIALIST = "multimedia_specialist"
    SIGNATURE_SPECIALIST = "signature_specialist"
    CONSISTENCY_ANALYST = "consistency_analyst"
    SENIOR_JUDGE = "senior_judge"


class FusionVerdict(StrEnum):
    """Final multimodal assessment verdict."""

    GENUINE = "genuine"
    SUSPICIOUS = "suspicious"
    POTENTIAL_FRAUD = "potential_fraud"
    INCONCLUSIVE = "inconclusive"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNAVAILABLE = "unavailable"


class FusionRunStatus(StrEnum):
    """Lifecycle for one fusion analysis run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    CANCELLED = "CANCELLED"


class ConflictType(StrEnum):
    """Cross-modal conflict categories."""

    VERDICT_DISAGREEMENT = "verdict_disagreement"
    CONFIDENCE_DISAGREEMENT = "confidence_disagreement"
    MODALITY_DISAGREEMENT = "modality_disagreement"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    PROVENANCE_INCONSISTENCY = "provenance_inconsistency"
    CONTRADICTORY_FINDING = "contradictory_finding"


class ConflictResolutionStatus(StrEnum):
    """Whether a conflict has been resolved."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class NormalizedFinding:
    """Orchestration-layer finding representation."""

    finding_id: str
    evidence_id: UUID
    modality: Modality
    analyzer: str
    category: str
    finding_type: str
    verdict: FindingVerdict
    confidence: float | None
    severity: Severity
    description: str
    explanation: str
    source_reference: str
    availability: ModalityAvailability
    model_name: str = ""
    model_version: str = ""
    temporal: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ModalityStatus:
    """Availability summary for one modality."""

    modality: Modality
    availability: ModalityAvailability
    findings_count: int
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class JuryAssessment:
    """Structured assessment from one jury member."""

    role: JuryMemberRole
    member_name: str
    verdict: FusionVerdict
    confidence: float | None
    availability: ModalityAvailability
    supporting_finding_ids: tuple[str, ...]
    contradictory_finding_ids: tuple[str, ...]
    explanation: str
    limitations: str
    model_name: str = ""
    model_version: str = ""


@dataclass(frozen=True, slots=True)
class FusionConflict:
    """Detected cross-modal conflict."""

    conflict_id: str
    conflict_type: ConflictType
    severity: Severity
    involved_finding_ids: tuple[str, ...]
    involved_modalities: tuple[Modality, ...]
    explanation: str
    resolution_status: ConflictResolutionStatus = ConflictResolutionStatus.OPEN


@dataclass(frozen=True, slots=True)
class AgreementMetrics:
    """Deterministic agreement information."""

    modality_agreement_ratio: float
    jury_agreement_ratio: float
    supporting_modalities: int
    contradictory_modalities: int
    unavailable_modalities: int
    inconclusive_modalities: int
    confidence_spread: float | None
    jury_votes_available: int
    jury_votes_total: int


@dataclass(frozen=True, slots=True)
class FusionAssessment:
    """Final multimodal assessment."""

    verdict: FusionVerdict
    risk_score: float | None
    confidence: float | None
    status: FusionRunStatus
    supporting_finding_ids: tuple[str, ...]
    contradictory_finding_ids: tuple[str, ...]
    participating_modalities: tuple[Modality, ...]
    unavailable_modalities: tuple[Modality, ...]
    agreement: AgreementMetrics
    conflicts: tuple[FusionConflict, ...]
    jury_assessments: tuple[JuryAssessment, ...]
    explanation: str
    limitations: str
    provenance: dict[str, Any]
    engine_version: str
    policy_version: str


@dataclass(frozen=True, slots=True)
class FusionResult:
    """Complete fusion pipeline output."""

    status: FusionRunStatus
    assessment: FusionAssessment | None
    normalized_findings: tuple[NormalizedFinding, ...]
    modality_statuses: tuple[ModalityStatus, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message_safe: str | None = None
