"""Deterministic platform validation engine and scoring."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI

from backend.app.core.config import Settings
from backend.app.platform_validation.models import (
    CheckOutcome,
    CheckStatus,
    ReadinessLevel,
    ValidationPlan,
)
from backend.app.platform_validation.policy import (
    PV_ENGINE_VERSION,
    PV_POLICY_VERSION,
    SEVERITY_WEIGHTS,
)
from backend.app.platform_validation.validator import (
    compatibility_panel,
    run_all_checks,
)


def score_readiness(outcomes: list[CheckOutcome]) -> tuple[float, ReadinessLevel]:
    """Compute readiness score and level from check outcomes."""

    if not outcomes:
        return 0.0, ReadinessLevel.NOT_READY
    total = float(len(outcomes))
    weighted = sum(SEVERITY_WEIGHTS[item.status.value] for item in outcomes)
    score = round((weighted / total) * 100.0, 2)
    statuses = {item.status for item in outcomes}
    if CheckStatus.FAIL in statuses:
        level = ReadinessLevel.NOT_READY
    elif CheckStatus.WARN in statuses:
        level = ReadinessLevel.DEGRADED
    else:
        level = ReadinessLevel.READY
    return score, level


def build_health_report(
    outcomes: list[CheckOutcome],
    *,
    readiness_score: float,
    readiness_level: ReadinessLevel,
) -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in outcomes:
        by_category.setdefault(item.category, []).append(
            {
                "key": item.key,
                "label": item.label,
                "status": item.status.value,
                "message": item.message,
            }
        )
    counts = {
        "pass": sum(1 for item in outcomes if item.status == CheckStatus.PASS),
        "warn": sum(1 for item in outcomes if item.status == CheckStatus.WARN),
        "fail": sum(1 for item in outcomes if item.status == CheckStatus.FAIL),
        "total": len(outcomes),
    }
    return {
        "readiness_score": readiness_score,
        "readiness_level": readiness_level.value,
        "counts": counts,
        "categories": {key: by_category[key] for key in sorted(by_category.keys())},
        "generated_at": datetime.now(UTC).isoformat(),
        "engine_version": PV_ENGINE_VERSION,
        "policy_version": PV_POLICY_VERSION,
        "ai_rerun": False,
        "data_mutation": False,
    }


def build_issues(outcomes: list[CheckOutcome]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for item in outcomes:
        if item.status == CheckStatus.PASS:
            continue
        issues.append(
            {
                "check_key": item.key,
                "category": item.category,
                "severity": item.status.value,
                "message": item.message,
                "details": dict(item.details),
            }
        )
    issues.sort(key=lambda row: (row["severity"], row["check_key"]))
    return issues


class PlatformValidationEngine:
    def __init__(self, settings: Settings, app: FastAPI) -> None:
        self.settings = settings
        self.app = app

    async def plan(self) -> ValidationPlan:
        outcomes = run_all_checks(settings=self.settings, app=self.app)
        score, level = score_readiness(outcomes)
        health = build_health_report(
            outcomes,
            readiness_score=score,
            readiness_level=level,
        )
        compatibility = compatibility_panel()
        provenance = {
            "engine_version": PV_ENGINE_VERSION,
            "policy_version": PV_POLICY_VERSION,
            "deterministic": True,
            "ai_rerun": False,
            "data_mutation": False,
            "check_count": len(outcomes),
            "compatibility": compatibility,
        }
        return ValidationPlan(
            outcomes=tuple(outcomes),
            readiness_score=score,
            readiness_level=level,
            provenance=provenance,
            health_report=health,
            compatibility=compatibility,
        )
