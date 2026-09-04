"""Pydantic schemas for Phase 8F security governance API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SecurityRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    code: str
    name: str
    description: str
    permissions: list[str] = Field(default_factory=list)
    policy_version: str


class SecurityRoleListResponse(BaseModel):
    items: list[SecurityRoleResponse]
    total: int


class SecurityPermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    code: str
    resource: str
    action: str
    description: str
    roles: list[str] = Field(default_factory=list)
    policy_version: str


class SecurityPermissionListResponse(BaseModel):
    items: list[SecurityPermissionResponse]
    total: int


class CaseAccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    user_id: UUID
    access_level: str
    granted_by: UUID | None = None
    reason: str | None = None
    active: bool
    granted_at: datetime
    revoked_at: datetime | None = None


class CaseAccessListResponse(BaseModel):
    items: list[CaseAccessResponse]
    total: int


class CaseAccessUpdateRequest(BaseModel):
    user_id: UUID
    access_level: str
    reason: str | None = None
    active: bool = True


class ComplianceResponse(BaseModel):
    status: str
    case_id: UUID | None = None
    chain_of_custody_complete: bool
    evidence_integrity_ok: bool
    audit_complete: bool
    workflow_compliant: bool
    report_approval_compliant: bool
    missing_approvals: list[str] = Field(default_factory=list)
    missing_provenance: list[str] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime
    policy_version: str
    engine_version: str
    report_id: UUID | None = None


class PolicyDocumentResponse(BaseModel):
    policy_version: str
    engine_version: str
    case_retention_days: int
    evidence_retention_days: int
    report_publication_requires_approval: bool
    workflow_approval_required_for_archive: bool
    ai_execution_requires_case_access: bool
    export_requires_audit_view: bool
    policies: list[dict[str, Any]]


class PolicyViolationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID | None = None
    policy_code: str
    severity: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime
    resolved_at: datetime | None = None
    policy_version: str


class PolicyViolationListResponse(BaseModel):
    items: list[PolicyViolationResponse]
    total: int


class ValidationFindingResponse(BaseModel):
    check: str
    status: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationRequest(BaseModel):
    case_id: UUID | None = None


class ValidationResponse(BaseModel):
    status: str
    findings: list[ValidationFindingResponse]
    generated_at: datetime
    policy_version: str
    engine_version: str
    case_id: UUID | None = None
