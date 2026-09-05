"""Provenance helpers for derived analytics metrics."""

from __future__ import annotations

from typing import Any

from backend.app.analytics.policy import AN_ENGINE_VERSION, AN_POLICY_VERSION


def metric_provenance(
    *, sources: list[str], detail: str | None = None
) -> dict[str, Any]:
    return {
        "sources": sorted(sources),
        "detail": detail,
        "engine_version": AN_ENGINE_VERSION,
        "policy_version": AN_POLICY_VERSION,
        "derived": True,
    }
