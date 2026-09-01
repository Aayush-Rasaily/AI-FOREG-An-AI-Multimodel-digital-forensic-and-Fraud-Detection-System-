"""Signature verification schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SignatureVerdict(StrEnum):
    MATCH = "MATCH"
    NON_MATCH = "NON_MATCH"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNAVAILABLE = "UNAVAILABLE"


class SignatureRegionResponse(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    page_number: int | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class SignatureVerificationResponse(BaseModel):
    id: UUID
    reference_hash: str
    questioned_hash: str
    model: str
    model_version: str
    similarity: float | None = Field(default=None, ge=0, le=1)
    threshold: float = Field(ge=0, le=1)
    verdict: SignatureVerdict
    device: str
    processing_time_ms: float | None
    reference_evidence_id: UUID | None
    questioned_evidence_id: UUID | None
    localization: SignatureRegionResponse | None
    artifact_id: UUID | None
    metadata: dict[str, Any]
    created_at: datetime


class SignatureVerificationListResponse(BaseModel):
    items: list[SignatureVerificationResponse]
    total: int
    limit: int
    offset: int
