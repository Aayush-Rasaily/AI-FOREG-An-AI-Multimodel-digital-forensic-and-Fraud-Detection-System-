"""Pydantic schemas for Phase 8G deployment / release APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CheckItem(BaseModel):
    check: str
    status: str
    message: str
    free_bytes: str | None = None
    total_bytes: str | None = None


class VersionResponse(BaseModel):
    application_version: str
    service: str
    environment: str
    policy_version: str
    engine_version: str


class ReleaseResponse(BaseModel):
    application_version: str
    schema_version: str
    migration_version: str
    environment: str
    policy_versions: dict[str, str]
    ai_engine_versions: dict[str, str]
    build_metadata: dict[str, Any]
    git_commit: str | None = None


class LivenessResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    policy_version: str
    engine_version: str


class ReadinessResponse(BaseModel):
    status: str
    ready: bool
    validation_status: str
    checks: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: str
    policy_version: str
    engine_version: str


class StartupValidationResponse(BaseModel):
    status: str
    checks: list[dict[str, str]] = Field(default_factory=list)
    fail_count: int
    timestamp: str
    environment: str
    version: str
    policy_version: str
    engine_version: str
    graceful_shutdown_supported: bool = True


class ConfigurationResponse(BaseModel):
    profile: dict[str, Any]
    export: dict[str, Any]
    findings: list[dict[str, str]] = Field(default_factory=list)


class ValidationResponse(BaseModel):
    status: str
    checks: list[dict[str, Any]] = Field(default_factory=list)
    fail_count: int
    warn_count: int
    pass_count: int
    policy_version: str
    engine_version: str


class ReleaseCheckResponse(BaseModel):
    status: str
    release: ReleaseResponse
    validation: ValidationResponse
    disaster_recovery: dict[str, Any]
    restore: dict[str, Any]
    backup_records: list[dict[str, Any]] = Field(default_factory=list)
