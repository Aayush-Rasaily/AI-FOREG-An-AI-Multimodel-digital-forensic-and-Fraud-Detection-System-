"""Telemetry bootstrap for Phase 10B observability."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from backend.app.monitoring.tracing import (
    instrument_fastapi,
    instrument_httpx,
    instrument_redis,
    instrument_sqlalchemy,
    setup_tracing,
)

logger = logging.getLogger(__name__)

_TELEMETRY_STARTED = False


def setup_telemetry(app: FastAPI, *, service_name: str = "ai-forge-api") -> None:
    """Initialize tracing and framework instrumentation (idempotent, non-blocking)."""

    global _TELEMETRY_STARTED
    if _TELEMETRY_STARTED:
        return
    setup_tracing(service_name=service_name)
    instrument_fastapi(app)
    instrument_redis()
    instrument_httpx()
    try:
        from backend.app.infrastructure.database.session import get_engine

        if get_engine.cache_info().currsize:
            instrument_sqlalchemy(get_engine())
    except Exception:  # noqa: BLE001
        logger.debug("SQLAlchemy instrumentation deferred", exc_info=True)
    _TELEMETRY_STARTED = True
    logger.info("Phase 10B telemetry bootstrap complete")


def record_background_task(name: str) -> Any:
    """Return a no-op / span context manager for background task instrumentation."""

    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("ai-forge.background")
        return tracer.start_as_current_span(f"background:{name}")
    except Exception:  # noqa: BLE001

        class _Null:
            def __enter__(self) -> None:
                return None

            def __exit__(self, *args: object) -> None:
                return None

        return _Null()
