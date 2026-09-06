"""Readiness / dependency health probes for observability (Phase 10B)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.health_service import check_database_health
from backend.app.core.config import Settings


async def check_redis(settings: Settings) -> dict[str, Any]:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
        )
        try:
            await client.ping()
        finally:
            await client.aclose()
        return {"check": "redis", "status": "pass", "message": "Redis reachable."}
    except Exception as exc:  # noqa: BLE001
        return {
            "check": "redis",
            "status": "fail",
            "message": f"Redis unreachable: {type(exc).__name__}",
        }


def check_storage(settings: Settings) -> dict[str, Any]:
    root = Path(settings.storage_root)
    try:
        root.mkdir(parents=True, exist_ok=True)
        if not os.access(root, os.R_OK | os.W_OK):
            return {
                "check": "storage",
                "status": "fail",
                "message": "Storage root is not readable/writable.",
            }
        return {
            "check": "storage",
            "status": "pass",
            "message": f"Storage accessible at {root.as_posix()}.",
        }
    except OSError as exc:
        return {
            "check": "storage",
            "status": "fail",
            "message": f"Storage check failed: {type(exc).__name__}",
        }


def check_disk_space(
    settings: Settings, *, min_free_ratio: float = 0.05
) -> dict[str, Any]:
    root = Path(settings.storage_root)
    try:
        usage = shutil.disk_usage(root if root.exists() else Path.cwd())
        free_ratio = usage.free / usage.total if usage.total else 0.0
        status = "pass" if free_ratio >= min_free_ratio else "fail"
        return {
            "check": "disk_space",
            "status": status,
            "message": f"Free disk ratio={free_ratio:.4f}.",
            "free_bytes": usage.free,
            "total_bytes": usage.total,
        }
    except OSError as exc:
        return {
            "check": "disk_space",
            "status": "fail",
            "message": f"Disk check failed: {type(exc).__name__}",
        }


def check_memory(*, max_ratio: float = 0.95) -> dict[str, Any]:
    try:
        import psutil

        ratio = float(psutil.virtual_memory().percent) / 100.0
        status = "pass" if ratio <= max_ratio else "fail"
        return {
            "check": "memory",
            "status": status,
            "message": f"Memory utilization={ratio:.4f}.",
            "ratio": ratio,
        }
    except Exception:  # noqa: BLE001
        # psutil is optional; treat as warn/pass when unavailable.
        return {
            "check": "memory",
            "status": "pass",
            "message": "Memory probe unavailable; skipped.",
        }


def check_ai_engines(app_state: Any | None) -> dict[str, Any]:
    if app_state is None:
        return {
            "check": "ai_engines",
            "status": "pass",
            "message": "AI engine state not attached; skipped.",
        }
    stacks = [
        getattr(app_state, "ai_stack", None),
        getattr(app_state, "image_ai_stack", None),
        getattr(app_state, "document_ai_stack", None),
        getattr(app_state, "video_ai_stack", None),
        getattr(app_state, "audio_ai_stack", None),
    ]
    present = sum(1 for stack in stacks if stack is not None)
    if present == 0:
        return {
            "check": "ai_engines",
            "status": "fail",
            "message": "No AI stacks registered on application state.",
        }
    return {
        "check": "ai_engines",
        "status": "pass",
        "message": f"{present} AI stack(s) registered.",
        "stacks": present,
    }


async def build_readiness_report(
    *,
    settings: Settings,
    session: AsyncSession,
    app_state: Any | None = None,
) -> dict[str, Any]:
    """Aggregate readiness checks for ``/health/ready``."""

    db_ok = await check_database_health(
        session,
        timeout_seconds=settings.db_health_timeout_seconds,
    )
    checks = [
        {
            "check": "database",
            "status": "pass" if db_ok else "fail",
            "message": "Database reachable." if db_ok else "Database unavailable.",
        },
        await check_redis(settings),
        check_storage(settings),
        check_ai_engines(app_state),
        check_disk_space(settings),
        check_memory(),
    ]
    failed = [item for item in checks if item["status"] == "fail"]
    ready = len(failed) == 0
    # Non-production: redis failure should not always block local/dev readiness.
    if settings.app_env in {"local", "development", "test"}:
        hard_fails = [
            item
            for item in failed
            if item["check"] in {"database", "storage", "disk_space"}
        ]
        ready = len(hard_fails) == 0
    return {
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "checks": checks,
        "fail_count": len(failed),
        "environment": settings.app_env,
        "version": settings.app_version,
    }
