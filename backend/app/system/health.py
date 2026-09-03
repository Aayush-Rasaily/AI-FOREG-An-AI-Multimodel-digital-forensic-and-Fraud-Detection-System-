"""System health snapshot helpers."""

from __future__ import annotations

import platform
import sys
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.health_service import (
    check_database_health,
)
from backend.app.core.config import Settings
from backend.app.system.models import ServiceStatus

_START_TIME = time.monotonic()


def _uptime_seconds() -> float:
    return time.monotonic() - _START_TIME


async def _check_redis(settings: Settings) -> dict[str, Any]:
    if not settings.redis_url:
        return {
            "status": ServiceStatus.NOT_CONFIGURED.value,
            "detail": "Redis URL not configured.",
        }
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
        )
        await client.ping()
        await client.aclose()
        return {
            "status": ServiceStatus.HEALTHY.value,
            "detail": "Redis reachable.",
        }
    except Exception as exc:
        return {
            "status": ServiceStatus.UNAVAILABLE.value,
            "detail": f"Redis unreachable: {type(exc).__name__}",
        }


def _resource_usage() -> dict[str, Any]:
    cpu_percent: float | None = None
    memory_mb: float | None = None
    disk_percent: float | None = None
    gpu_available = False
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        memory_mb = round(mem.used / (1024 * 1024), 2)
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
    except ImportError:
        pass
    return {
        "cpu_percent": cpu_percent,
        "memory_mb": memory_mb,
        "disk_percent": disk_percent,
        "gpu_available": gpu_available,
    }


async def build_health_snapshot(
    session: AsyncSession,
    settings: Settings,
) -> dict[str, Any]:
    """Collect deterministic health snapshot."""
    db_ok = await check_database_health(
        session,
        timeout_seconds=settings.db_health_timeout_seconds,
    )
    redis = await _check_redis(settings)
    resources = _resource_usage()
    overall = "healthy"
    if not db_ok or redis["status"] == ServiceStatus.UNAVAILABLE.value:
        overall = "degraded"
    return {
        "status": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "uptime_seconds": round(_uptime_seconds(), 2),
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "database": {
            "status": (
                ServiceStatus.HEALTHY.value
                if db_ok
                else ServiceStatus.UNAVAILABLE.value
            ),
        },
        "redis": redis,
        "resources": resources,
        "engine_version": "1.0",
        "policy_version": "1.0",
    }
