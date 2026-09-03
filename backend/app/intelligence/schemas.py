"""Pydantic schemas for investigation intelligence responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceLinks(BaseModel):
    """Traceability links for a narrative paragraph or finding."""

    model_config = ConfigDict(extra="forbid")

    evidence_ids: list[str] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)
    fusion_ids: list[str] = Field(default_factory=list)
    timeline_ids: list[str] = Field(default_factory=list)
    correlation_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    report_ids: list[str] = Field(default_factory=list)
    audit_ids: list[str] = Field(default_factory=list)


class NarrativeParagraph(BaseModel):
    """A single explainable narrative paragraph."""

    model_config = ConfigDict(extra="forbid")

    section: str
    text: str
    provenance: ProvenanceLinks


class KeyFindingItem(BaseModel):
    """Prioritized key finding with provenance."""

    model_config = ConfigDict(extra="forbid")

    title: str
    severity: str
    confidence: float | None = None
    summary: str
    provenance: ProvenanceLinks


class RecommendationItem(BaseModel):
    """Deterministic next-step recommendation."""

    model_config = ConfigDict(extra="forbid")

    code: str
    title: str
    rationale: str
    supporting_finding_refs: list[str] = Field(default_factory=list)
    provenance: ProvenanceLinks


class CoverageStats(BaseModel):
    """Evidence and analysis coverage snapshot."""

    model_config = ConfigDict(extra="forbid")

    evidence_count: int
    analyzed_count: int
    not_analyzed_count: int
    mime_types: dict[str, int] = Field(default_factory=dict)
    date_range_start: str | None = None
    date_range_end: str | None = None
    processing_statuses: dict[str, int] = Field(default_factory=dict)


class InvestigationSummaryResponse(BaseModel):
    """Persisted investigation intelligence summary."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    case_id: UUID
    generated_at: datetime
    overall_risk: str
    overall_confidence: int
    overview: dict[str, Any]
    key_findings: list[dict[str, Any]]
    timeline_summary: dict[str, Any]
    correlation_summary: dict[str, Any]
    ai_summary: dict[str, Any]
    recommendations: list[dict[str, Any]]
    provenance: dict[str, Any]
    narrative: list[dict[str, Any]]
    engine_version: str
    policy_version: str


class InvestigationSummaryListResponse(BaseModel):
    """Paginated list of investigation summaries."""

    model_config = ConfigDict(extra="forbid")

    items: list[InvestigationSummaryResponse]
    total: int
    limit: int
    offset: int
