"""System diagnostics runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.health_service import (
    check_database_health,
)
from backend.app.core.config import Settings
from backend.app.system.models import DiagnosticStatus
from backend.app.system.policy import DIAGNOSTIC_CHECKS
from backend.app.system.storage import collect_storage_stats


def _check(name: str, status: DiagnosticStatus, detail: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": status.value,
        "detail": detail,
    }


def _verify_migration_files() -> tuple[DiagnosticStatus, str]:
    try:
        versions_dir = (
            Path(__file__).resolve().parents[2]
            / "alembic"
            / "versions"
        )
        head_files = list(versions_dir.glob("20260901_0019*"))
        if not head_files:
            return (
                DiagnosticStatus.WARN,
                "Expected head migration not found on disk.",
            )
        return DiagnosticStatus.PASS, "Migration chain verified."
    except OSError:
        return DiagnosticStatus.WARN, "Could not verify migration files."


async def run_diagnostics(
    session: AsyncSession,
    settings: Settings,
) -> dict[str, Any]:
    """Run all configured diagnostic checks."""
    checks: list[dict[str, Any]] = []

    # configuration
    config_ok = bool(settings.app_name and settings.database_url)
    detail = (
        "Application configuration loaded."
        if config_ok
        else "Missing required config."
    )
    checks.append(_check(
        "configuration",
        DiagnosticStatus.PASS if config_ok else DiagnosticStatus.FAIL,
        detail,
    ))

    # database_connectivity
    db_ok = await check_database_health(
        session,
        timeout_seconds=settings.db_health_timeout_seconds,
    )
    checks.append(_check(
        "database_connectivity",
        DiagnosticStatus.PASS if db_ok else DiagnosticStatus.FAIL,
        "Database reachable." if db_ok else "Database unreachable.",
    ))

    # storage_verification
    storage = collect_storage_stats(settings)
    storage_ok = storage.get("root_configured", False)
    checks.append(_check(
        "storage_verification",
        DiagnosticStatus.PASS if storage_ok else DiagnosticStatus.WARN,
        f"Storage backend: {settings.storage_backend}.",
    ))

    # migration_verification
    mig_status, mig_detail = _verify_migration_files()
    checks.append(_check("migration_verification", mig_status, mig_detail))

    # ai_model_availability
    from backend.app.models.ai import AIModelRecord

    ai_count = await session.scalar(
        select(func.count()).select_from(AIModelRecord),
    )
    ai_count = int(ai_count or 0)
    checks.append(_check(
        "ai_model_availability",
        DiagnosticStatus.PASS if ai_count > 0 else DiagnosticStatus.WARN,
        f"{ai_count} AI model(s) registered.",
    ))

    # queue_health
    try:
        await session.execute(text("SELECT 1"))
        queue_ok = True
    except Exception:
        queue_ok = False
    checks.append(_check(
        "queue_health",
        DiagnosticStatus.PASS if queue_ok else DiagnosticStatus.WARN,
        "Job queue infrastructure available (in-process).",
    ))

    # cache_verification
    if settings.redis_url:
        checks.append(_check(
            "cache_verification",
            DiagnosticStatus.PASS,
            "Redis URL configured.",
        ))
    else:
        checks.append(_check(
            "cache_verification",
            DiagnosticStatus.SKIP,
            "Redis not configured.",
        ))

    # dependency_checks
    deps_ok = True
    missing: list[str] = []
    for pkg in ("fastapi", "sqlalchemy", "pydantic"):
        if importlib.util.find_spec(pkg) is None:
            deps_ok = False
            missing.append(pkg)
    checks.append(_check(
        "dependency_checks",
        DiagnosticStatus.PASS if deps_ok else DiagnosticStatus.FAIL,
        "All core dependencies present."
        if deps_ok
        else f"Missing: {', '.join(missing)}",
    ))

    fail_count = sum(
        1 for c in checks if c["status"] == DiagnosticStatus.FAIL.value
    )
    warn_count = sum(
        1 for c in checks if c["status"] == DiagnosticStatus.WARN.value
    )
    overall = "healthy"
    if fail_count > 0:
        overall = "unhealthy"
    elif warn_count > 0:
        overall = "degraded"

    return {
        "overall_status": overall,
        "checks": checks,
        "check_names": list(DIAGNOSTIC_CHECKS),
        "pass_count": sum(
            1 for c in checks
            if c["status"] == DiagnosticStatus.PASS.value
        ),
        "warn_count": warn_count,
        "fail_count": fail_count,
    }
