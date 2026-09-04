"""API schemas for Phase 9C investigation intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CoverageMetricsResponse(BaseModel):
    evidence_total: int
    evidence_analyzed: int
    evidence_pending: int
    timeline_coverage: float
    knowledge_graph_coverage: float
    correlation_coverage: float
    fusion_coverage: float
    ai_coverage: float
    metadata_completeness: float
    chain_of_custody_completeness: float
    overall_completeness: float
    open_conflicts: int


class HypothesisResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    hypothesis_key: str
    hypothesis_type: str
    title: str
    explanation: str
    confidence: float
    priority: str
    status: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)


class EvidenceGapResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    gap_key: str
    gap_type: str
    severity: str
    reason: str
    recommended_action: str
    affected_evidence_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    recommendation_key: str
    code: str
    action_text: str
    priority: str
    related_hypothesis_keys: list[str] = Field(default_factory=list)
    related_gap_keys: list[str] = Field(default_factory=list)
    affected_evidence_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class IntelligenceRunResponse(BaseModel):
    id: UUID | None = None
    case_id: UUID
    status: str
    investigation_score: float
    overall_completeness: float
    hypothesis_count: int
    gap_count: int
    recommendation_count: int
    open_conflict_count: int
    coverage: CoverageMetricsResponse
    open_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    policy_version: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    hypotheses: list[HypothesisResponse] = Field(default_factory=list)
    gaps: list[EvidenceGapResponse] = Field(default_factory=list)
    recommendations: list[RecommendationResponse] = Field(default_factory=list)
    persisted: bool = True


class IntelligencePreviewResponse(IntelligenceRunResponse):
    persisted: bool = False


class InvestigationSummaryResponse(BaseModel):
    case_id: UUID
    run_id: UUID | None = None
    investigation_score: float
    overall_completeness: float
    coverage: CoverageMetricsResponse
    top_hypotheses: list[HypothesisResponse] = Field(default_factory=list)
    critical_gaps: list[EvidenceGapResponse] = Field(default_factory=list)
    top_recommendations: list[RecommendationResponse] = Field(
        default_factory=list
    )
    open_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    engine_version: str
    policy_version: str


class HypothesisListResponse(BaseModel):
    items: list[HypothesisResponse]
    total: int


class EvidenceGapListResponse(BaseModel):
    items: list[EvidenceGapResponse]
    total: int


class RecommendationListResponse(BaseModel):
    items: list[RecommendationResponse]
    total: int
