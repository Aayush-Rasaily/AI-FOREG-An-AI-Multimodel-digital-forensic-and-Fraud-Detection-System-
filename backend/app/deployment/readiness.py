"""Readiness aggregation for production probes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.deployment.validation import run_operational_validation


async def readiness_payload(
    *,
    settings: Settings,
    session: AsyncSession,
    app_state: Any | None = None,
) -> dict[str, Any]:
    """Return readiness based on operational validation."""

    validation = await run_operational_validation(
        settings=settings,
        session=session,
        app_state=app_state,
    )
    ready = validation["status"] in {"PASSED", "DEGRADED"}
    # Production strict: only PASSED is ready
    if settings.app_env == "production":
        ready = validation["status"] == "PASSED"
    return {
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "validation_status": validation["status"],
        "checks": validation["checks"],
        "timestamp": datetime.now(UTC).isoformat(),
        "policy_version": validation["policy_version"],
        "engine_version": validation["engine_version"],
    }
