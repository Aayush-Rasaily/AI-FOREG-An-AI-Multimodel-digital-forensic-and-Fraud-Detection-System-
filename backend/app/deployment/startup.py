"""Startup validation and graceful shutdown coordination."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.core.config import Settings
from backend.app.deployment.configuration import verify_configuration
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
)

_startup_result: dict[str, Any] | None = None
_shutdown_requested: bool = False


def mark_shutdown_requested() -> None:
    """Signal that graceful shutdown has begun."""

    global _shutdown_requested
    _shutdown_requested = True


def is_shutdown_requested() -> bool:
    """Return whether graceful shutdown was requested."""

    return _shutdown_requested


def run_startup_validation(settings: Settings) -> dict[str, Any]:
    """Validate configuration at process start (no network I/O)."""

    global _startup_result
    findings = verify_configuration(settings)
    failed = [item for item in findings if item["status"] == "FAIL"]
    result = {
        "status": "FAILED" if failed else "PASSED",
        "checks": findings,
        "fail_count": len(failed),
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": settings.app_env,
        "version": settings.app_version,
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
        "graceful_shutdown_supported": True,
    }
    _startup_result = result
    return result


def get_startup_validation() -> dict[str, Any] | None:
    """Return the last startup validation snapshot."""

    return _startup_result
