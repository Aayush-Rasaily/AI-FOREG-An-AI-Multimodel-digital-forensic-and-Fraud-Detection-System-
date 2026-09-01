"""API schemas for case-level forensic intelligence."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.case_intelligence.models import (
    CaseConflictType,
    CaseIntelligenceRunStatus,
    ConflictResolutionStatus,
    EvidenceCoverageStatus,
    RelationshipStatus,
    RelationshipType,
    TimelineEventType,
)
from backend.app.forensics.models import Severity
from backend.app.fusion.models import FusionVerdict


class EvidenceCoverageResponse(BaseModel):
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
    supported_modalities: list[str]


class EvidenceParticipationResponse(BaseModel):
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
    supporting_finding_ids: list[str]
    contradictory_finding_ids: list[str]
    conflicts_count: int
    participating_modalities: list[str]
    unavailable_modalities: list[str]
    fusion_engine_version: str | None
    fusion_policy_version: str | None
    fusion_completed_at: datetime | None
    reason: str | None = None


class CaseRelationshipResponse(BaseModel):
    id: UUID | None = None
    relationship_id: str
    evidence_a_id: UUID
    evidence_b_id: UUID
    relationship_type: RelationshipType
    confidence: float | None
    supporting_reason: str
    source_reference: str
    status: RelationshipStatus


class CaseConflictResponse(BaseModel):
    id: UUID | None = None
    conflict_id: str
    conflict_type: CaseConflictType
    severity: Severity
    involved_evidence_ids: list[str]
    involved_finding_ids: list[str]
    explanation: str
    resolution_status: ConflictResolutionStatus


class TimelineEventResponse(BaseModel):
    id: UUID | None = None
    event_id: str
    event_type: TimelineEventType
    timestamp: datetime | None
    timestamp_known: bool
    evidence_id: UUID | None
    source_reference: str
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseIntelligenceRunResponse(BaseModel):
    id: UUID
    case_id: UUID
    status: CaseIntelligenceRunStatus
    engine_version: str
    policy_version: str
    verdict: FusionVerdict | None
    risk_score: float | None
    confidence: float | None
    evidence_count: int
    conflicts_count: int
    relationships_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any]
    provenance: dict[str, Any]


class CaseIntelligenceRunListResponse(BaseModel):
    items: list[CaseIntelligenceRunResponse]
    total: int
    limit: int
    offset: int


class CaseIntelligenceDetailResponse(CaseIntelligenceRunResponse):
    coverage: EvidenceCoverageResponse
    participations: list[EvidenceParticipationResponse]
    relationships: list[CaseRelationshipResponse]
    conflicts: list[CaseConflictResponse]
    timeline: list[TimelineEventResponse]
    explanation: str | None
    limitations: str | None
    supporting_evidence_ids: list[str]
    contradictory_evidence_ids: list[str]
