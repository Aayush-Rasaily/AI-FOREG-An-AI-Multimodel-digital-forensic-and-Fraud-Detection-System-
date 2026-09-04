"""Liveness helpers for production probes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.app.core.config import Settings
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
)


def liveness_payload(settings: Settings) -> dict[str, Any]:
    """Return a dependency-free liveness signal."""

    return {
        "status": "alive",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(UTC).isoformat(),
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
    }
