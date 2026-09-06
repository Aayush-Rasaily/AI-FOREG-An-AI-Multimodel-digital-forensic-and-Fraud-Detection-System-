"""Startup validation and graceful shutdown coordination."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.core.config import Settings
from backend.app.core.environment import validate_environment
from backend.app.deployment.configuration import verify_configuration
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
)

_startup_result: dict[str, Any] | None = None
_dependency_result: dict[str, Any] | None = None
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
    env_report = validate_environment(settings)
    env_checks = list(env_report.get("checks") or [])
    merged = [*findings, *env_checks]
    failed = [item for item in merged if item.get("status") == "FAIL"]
    result = {
        "status": "FAILED" if failed else "PASSED",
        "checks": merged,
        "fail_count": len(failed),
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": settings.app_env,
        "version": settings.app_version,
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
        "graceful_shutdown_supported": True,
        "environment_validation": {
            "status": env_report.get("status"),
            "fail_count": env_report.get("fail_count"),
            "warn_count": env_report.get("warn_count"),
        },
    }
    _startup_result = result
    return result


def set_dependency_validation(result: dict[str, Any]) -> None:
    """Store async dependency verification from application lifespan."""

    global _dependency_result
    _dependency_result = result


def get_dependency_validation() -> dict[str, Any] | None:
    """Return the last async dependency verification snapshot."""

    return _dependency_result


def get_startup_validation() -> dict[str, Any] | None:
    """Return the last startup validation snapshot."""

    return _startup_result
