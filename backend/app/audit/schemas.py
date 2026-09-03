"""API schemas for the audit framework."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditEventResponse(BaseModel):
    id: UUID
    timestamp: datetime
    user: str
    operation: str
    category: str
    case_id: UUID | None
    evidence_id: UUID | None
    previous_state: Any = None
    new_state: Any = None
    client_ip: str | None
    user_agent: str | None
    engine_version: str
    policy_version: str
    sha256_checksum: str | None
    integrity_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
    limit: int
    offset: int


class IntegrityResultResponse(BaseModel):
    target_type: str
    target_id: str
    status: str
    expected_hash: str | None = None
    computed_hash: str | None = None
    detail: str = ""


class IntegrityVerifyResponse(BaseModel):
    results: list[IntegrityResultResponse]
    overall_status: str
    verified_count: int
    mismatch_count: int
    unavailable_count: int


class AuditExportResponse(BaseModel):
    format: str
    total_events: int
    checksum: str
