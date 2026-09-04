"""Operational validation for production readiness."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.health_service import check_database_health
from backend.app.core.config import Settings
from backend.app.deployment.configuration import (
    REQUIRED_PRODUCTION_ENV_VARS,
    verify_configuration,
)
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
    EXPECTED_MIGRATION_HEAD,
)


async def _redis_status(settings: Settings) -> dict[str, str]:
    if not settings.redis_url:
        return {
            "check": "redis",
            "status": "WARN",
            "message": "Redis URL not configured.",
        }
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url, socket_connect_timeout=1)
        try:
            await client.ping()
        finally:
            await client.aclose()
        return {
            "check": "redis",
            "status": "PASS",
            "message": "Redis reachable.",
        }
    except Exception as exc:  # noqa: BLE001 — surface connectivity only
        return {
            "check": "redis",
            "status": "FAIL",
            "message": f"Redis unreachable: {type(exc).__name__}",
        }


def _storage_status(settings: Settings) -> dict[str, str]:
    root = Path(settings.storage_root)
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".deployment_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {
            "check": "storage",
            "status": "PASS",
            "message": f"Storage writable at {root.as_posix()}.",
        }
    except OSError as exc:
        return {
            "check": "storage",
            "status": "FAIL",
            "message": f"Storage unavailable: {exc.strerror or type(exc).__name__}",
        }


def _disk_status(settings: Settings) -> dict[str, Any]:
    root = Path(settings.storage_root)
    try:
        usage = shutil.disk_usage(root if root.exists() else Path.cwd())
        free_ratio = usage.free / usage.total if usage.total else 0
        if free_ratio < 0.05:
            status = "FAIL"
            message = "Less than 5% disk free."
        elif free_ratio < 0.15:
            status = "WARN"
            message = "Less than 15% disk free."
        else:
            status = "PASS"
            message = "Disk capacity acceptable."
        return {
            "check": "disk",
            "status": status,
            "message": message,
            "free_bytes": str(usage.free),
            "total_bytes": str(usage.total),
        }
    except OSError as exc:
        return {
            "check": "disk",
            "status": "FAIL",
            "message": f"Disk check failed: {type(exc).__name__}",
        }


def _env_vars_status(settings: Settings) -> dict[str, str]:
    if settings.app_env != "production":
        return {
            "check": "required_env_vars",
            "status": "PASS",
            "message": "Non-production profile; strict env set not required.",
        }
    missing = [
        name
        for name in REQUIRED_PRODUCTION_ENV_VARS
        if not os.environ.get(name)
        and not (
            name == "JWT_SECRET" and settings.jwt_secret is not None
        )
        and not (name == "DATABASE_URL" and settings.database_url)
        and not (name == "REDIS_URL" and settings.redis_url)
        and not (name == "STORAGE_ROOT" and settings.storage_root)
        and not (name == "APP_ENV" and settings.app_env)
        and not (name == "APP_VERSION" and settings.app_version)
    ]
    # Settings already loaded values — treat configured Settings as present
    if settings.auth_required and settings.database_url and settings.redis_url:
        missing = []
    if missing:
        return {
            "check": "required_env_vars",
            "status": "FAIL",
            "message": f"Missing required env vars: {', '.join(missing)}",
        }
    return {
        "check": "required_env_vars",
        "status": "PASS",
        "message": "Required production environment variables present.",
    }


def _ai_availability(app_state: Any | None) -> dict[str, str]:
    if app_state is None:
        return {
            "check": "ai_models",
            "status": "WARN",
            "message": "Application state unavailable for AI check.",
        }
    stacks = [
        getattr(app_state, key, None)
        for key in (
            "ai_stack",
            "image_ai_stack",
            "document_ai_stack",
            "video_ai_stack",
            "audio_ai_stack",
        )
    ]
    present = sum(1 for stack in stacks if isinstance(stack, dict))
    if present == 0:
        return {
            "check": "ai_models",
            "status": "FAIL",
            "message": "No AI stacks registered.",
        }
    return {
        "check": "ai_models",
        "status": "PASS",
        "message": f"{present} AI stacks registered.",
    }


async def _migration_status(session: AsyncSession) -> dict[str, str]:
    try:
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import Connection

        def _current(connection: Connection) -> str | None:
            context = MigrationContext.configure(connection)
            return context.get_current_revision()

        connection = await session.connection()
        current = await connection.run_sync(_current)
        if current is None:
            return {
                "check": "migration_status",
                "status": "WARN",
                "message": "No alembic revision applied yet.",
            }
        if current == EXPECTED_MIGRATION_HEAD:
            return {
                "check": "migration_status",
                "status": "PASS",
                "message": f"At expected head {EXPECTED_MIGRATION_HEAD}.",
            }
        return {
            "check": "migration_status",
            "status": "WARN",
            "message": (
                f"Current revision {current}; "
                f"expected head {EXPECTED_MIGRATION_HEAD}."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "check": "migration_status",
            "status": "WARN",
            "message": f"Migration status unavailable: {type(exc).__name__}",
        }


async def run_operational_validation(
    *,
    settings: Settings,
    session: AsyncSession,
    app_state: Any | None = None,
) -> dict[str, Any]:
    """Run deterministic operational validation checks."""

    db_ok = await check_database_health(
        session, timeout_seconds=settings.db_health_timeout_seconds,
    )
    checks: list[dict[str, str]] = [
        {
            "check": "database",
            "status": "PASS" if db_ok else "FAIL",
            "message": (
                "Database connectivity confirmed."
                if db_ok
                else "Database connectivity failed."
            ),
        },
        await _redis_status(settings),
        _storage_status(settings),
        _disk_status(settings),
        _env_vars_status(settings),
        _ai_availability(app_state),
        await _migration_status(session),
    ]
    checks.extend(verify_configuration(settings))
    checks = sorted(checks, key=lambda item: item["check"])

    failed = [item for item in checks if item["status"] == "FAIL"]
    warned = [item for item in checks if item["status"] == "WARN"]
    if failed:
        overall = "FAILED"
    elif warned:
        overall = "DEGRADED"
    else:
        overall = "PASSED"

    return {
        "status": overall,
        "checks": checks,
        "fail_count": len(failed),
        "warn_count": len(warned),
        "pass_count": len(checks) - len(failed) - len(warned),
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
    }
