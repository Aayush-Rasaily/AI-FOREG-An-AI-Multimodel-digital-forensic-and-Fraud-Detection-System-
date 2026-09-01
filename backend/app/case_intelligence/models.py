"""Domain models for case-level forensic intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from backend.app.forensics.models import Severity
from backend.app.fusion.models import FusionVerdict


class CaseIntelligenceRunStatus(StrEnum):
    """Lifecycle for one case intelligence run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class EvidenceCoverageStatus(StrEnum):
    """Coverage state for one evidence item in a case."""

    NOT_ANALYZED = "not_analyzed"
    ANALYZED = "analyzed"
    INCONCLUSIVE = "inconclusive"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class RelationshipType(StrEnum):
    """Supported cross-evidence relationship categories."""

    DUPLICATE_HASH = "duplicate_hash"
    REFERENCE_LINK = "reference_link"
    COMPARISON_LINK = "comparison_link"
    SIGNATURE_VERIFICATION_LINK = "signature_verification_link"
    SHARED_METADATA = "shared_metadata"
    SHARED_FILENAME = "shared_filename"


class RelationshipStatus(StrEnum):
    """Whether a relationship is supported by existing records."""

    DETECTED = "detected"
    CONFIRMED = "confirmed"


class CaseConflictType(StrEnum):
    """Case-level conflict categories."""

    VERDICT_DISAGREEMENT = "verdict_disagreement"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    PROVENANCE_INCONSISTENCY = "provenance_inconsistency"
    METADATA_INCONSISTENCY = "metadata_inconsistency"
    FORENSIC_CONTRADICTION = "forensic_contradiction"
    COMPARISON_CONTRADICTION = "comparison_contradiction"
    CONFIDENCE_DISAGREEMENT = "confidence_disagreement"


class ConflictResolutionStatus(StrEnum):
    """Whether a case conflict has been resolved."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class TimelineEventType(StrEnum):
    """Deterministic case timeline event categories."""

    EVIDENCE_REGISTERED = "evidence_registered"
    EVIDENCE_PROCESSED = "evidence_processed"
    FUSION_COMPLETED = "fusion_completed"
    COMPARISON_COMPLETED = "comparison_completed"
    CUSTODY_EVENT = "custody_event"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    CASE_INTELLIGENCE_COMPLETED = "case_intelligence_completed"


@dataclass(frozen=True, slots=True)
class EvidenceParticipation:
    """One evidence item's contribution to a case assessment."""

    evidence_id: UUID
    evidence_number: str
    evidence_type: str
    evidence_hash: str
    evidence_status: str
    coverage_status: EvidenceCoverageStatus
    fusion_run_id: UUID | None
    fusion_verdict: FusionVerdict | None
    risk_score: float | None
    confidence: float | None
    supporting_finding_ids: tuple[str, ...]
    contradictory_finding_ids: tuple[str, ...]
    conflicts_count: int
    participating_modalities: tuple[str, ...]
    unavailable_modalities: tuple[str, ...]
    fusion_engine_version: str | None
    fusion_policy_version: str | None
    fusion_completed_at: datetime | None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceCoverage:
    """Case-level evidence coverage summary."""

    total_evidence: int
    analyzed: int
    not_analyzed: int
    inconclusive: int
    insufficient_evidence: int
    unavailable: int
    failed: int
    supporting_evidence: int
    contradictory_evidence: int
    open_conflicts: int
    supported_modalities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    """Detected relationship between two evidence items."""

    relationship_id: str
    evidence_a_id: UUID
    evidence_b_id: UUID
    relationship_type: RelationshipType
    confidence: float | None
    supporting_reason: str
    source_reference: str
    status: RelationshipStatus


@dataclass(frozen=True, slots=True)
class CaseConflict:
    """Case-level conflict across evidence items."""

    conflict_id: str
    involved_evidence_ids: tuple[UUID, ...]
    involved_finding_ids: tuple[str, ...]
    conflict_type: CaseConflictType
    severity: Severity
    explanation: str
    resolution_status: ConflictResolutionStatus = ConflictResolutionStatus.OPEN


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """One deterministic timeline entry."""

    event_id: str
    event_type: TimelineEventType
    timestamp: datetime | None
    timestamp_known: bool
    evidence_id: UUID | None
    source_reference: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CaseAssessment:
    """Final case-level forensic synthesis."""

    verdict: FusionVerdict
    risk_score: float | None
    confidence: float | None
    status: CaseIntelligenceRunStatus
    coverage: EvidenceCoverage
    participations: tuple[EvidenceParticipation, ...]
    relationships: tuple[EvidenceRelationship, ...]
    conflicts: tuple[CaseConflict, ...]
    timeline: tuple[TimelineEvent, ...]
    supporting_evidence_ids: tuple[UUID, ...]
    contradictory_evidence_ids: tuple[UUID, ...]
    explanation: str
    limitations: str
    provenance: dict[str, Any]
    engine_version: str
    policy_version: str


@dataclass(frozen=True, slots=True)
class CaseIntelligenceResult:
    """Complete case intelligence pipeline output."""

    status: CaseIntelligenceRunStatus
    assessment: CaseAssessment | None
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message_safe: str | None = None
