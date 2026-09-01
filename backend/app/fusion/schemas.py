"""API schemas for multimodal fusion."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.forensics.models import Severity
from backend.app.fusion.models import (
    ConflictResolutionStatus,
    ConflictType,
    FusionRunStatus,
    FusionVerdict,
    JuryMemberRole,
    Modality,
    ModalityAvailability,
)


class ModalityStatusResponse(BaseModel):
    modality: Modality
    availability: ModalityAvailability
    findings_count: int
    reason: str | None = None


class NormalizedFindingResponse(BaseModel):
    finding_id: str
    evidence_id: UUID
    modality: Modality
    analyzer: str
    category: str
    finding_type: str
    verdict: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    severity: Severity
    description: str
    explanation: str
    source_reference: str
    availability: ModalityAvailability
    model_name: str = ""
    model_version: str = ""
    temporal: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class JuryAssessmentResponse(BaseModel):
    id: UUID | None = None
    role: JuryMemberRole
    member_name: str
    verdict: FusionVerdict
    confidence: float | None = Field(default=None, ge=0, le=1)
    availability: ModalityAvailability
    supporting_finding_ids: list[str]
    contradictory_finding_ids: list[str]
    explanation: str
    limitations: str | None
    model_name: str = ""
    model_version: str = ""


class FusionConflictResponse(BaseModel):
    id: UUID | None = None
    conflict_id: str
    conflict_type: ConflictType
    severity: Severity
    involved_finding_ids: list[str]
    involved_modalities: list[str]
    explanation: str
    resolution_status: ConflictResolutionStatus


class AgreementMetricsResponse(BaseModel):
    modality_agreement_ratio: float
    jury_agreement_ratio: float
    supporting_modalities: int
    contradictory_modalities: int
    unavailable_modalities: int
    inconclusive_modalities: int
    confidence_spread: float | None
    jury_votes_available: int
    jury_votes_total: int


class FusionAnalysisRunResponse(BaseModel):
    id: UUID
    evidence_id: UUID
    status: FusionRunStatus
    engine_version: str
    policy_version: str
    verdict: FusionVerdict | None
    risk_score: float | None
    confidence: float | None
    findings_count: int
    conflicts_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any]
    provenance: dict[str, Any]


class FusionAnalysisRunListResponse(BaseModel):
    items: list[FusionAnalysisRunResponse]
    total: int
    limit: int
    offset: int


class FusionAnalysisDetailResponse(FusionAnalysisRunResponse):
    modality_status: list[ModalityStatusResponse]
    jury_assessments: list[JuryAssessmentResponse]
    conflicts: list[FusionConflictResponse]
    agreement: AgreementMetricsResponse | None
    explanation: str | None
    limitations: str | None
    supporting_finding_ids: list[str]
    contradictory_finding_ids: list[str]
    participating_modalities: list[Modality]
    unavailable_modalities: list[Modality]


class FusionSignalsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: UUID
    findings: list[NormalizedFindingResponse]
    modality_status: list[ModalityStatusResponse]
