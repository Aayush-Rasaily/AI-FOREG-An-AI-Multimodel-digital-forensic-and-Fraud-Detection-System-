"""Domain dataclasses for interoperability jobs (non-ORM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InvestigationSnapshot:
    """Normalized case investigation payload for exporters."""

    case: dict[str, Any]
    evidence: list[dict[str, Any]]
    custody: list[dict[str, Any]]
    extractions: list[dict[str, Any]]
    ai_summaries: list[dict[str, Any]]
    fusion_summaries: list[dict[str, Any]]
    correlation_summaries: list[dict[str, Any]]
    timeline: dict[str, Any] | None
    reports: list[dict[str, Any]]
    workflow: dict[str, Any] | None
    security: dict[str, Any] | None
    policy_versions: dict[str, str] = field(default_factory=dict)
    ai_engine_versions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationFinding:
    check: str
    status: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    integrity_status: str
    findings: list[ValidationFinding]
    conflicts: list[str]
    package_version: str | None
    schema_version: str | None
