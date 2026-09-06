"""OpenTelemetry tracing setup (Phase 10B)."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_TRACING_CONFIGURED = False


def tracing_enabled() -> bool:
    """Return whether tracing should be activated."""

    if os.environ.get("OTEL_SDK_DISABLED", "").lower() in {"1", "true", "yes"}:
        return False
    return os.environ.get("OTEL_TRACES_EXPORTER", "none").lower() not in {
        "",
        "none",
        "false",
    } or os.environ.get("AI_FORGE_ENABLE_TRACING", "").lower() in {
        "1",
        "true",
        "yes",
    }


def setup_tracing(service_name: str = "ai-forge-api") -> Any | None:
    """Configure a TracerProvider when tracing is enabled; otherwise no-op."""

    global _TRACING_CONFIGURED
    if _TRACING_CONFIGURED:
        return None
    if not tracing_enabled():
        logger.info("OpenTelemetry tracing disabled (no exporter configured).")
        _TRACING_CONFIGURED = True
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        # Default to console exporter unless a real OTLP pipeline is configured.
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        _TRACING_CONFIGURED = True
        logger.info("OpenTelemetry tracing configured for %s", service_name)
        return provider
    except Exception:  # noqa: BLE001 — instrumentation must never block startup
        logger.exception("Failed to configure OpenTelemetry tracing")
        _TRACING_CONFIGURED = True
        return None


def get_trace_id() -> str | None:
    """Return the active OpenTelemetry trace id hex string, if any."""

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        context = span.get_span_context()
        if context is None or not context.is_valid:
            return None
        return format(context.trace_id, "032x")
    except Exception:  # noqa: BLE001
        return None


def instrument_fastapi(app: Any) -> None:
    """Instrument FastAPI with OpenTelemetry when available."""

    if not tracing_enabled():
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
    except Exception:  # noqa: BLE001
        logger.exception("FastAPI instrumentation failed")


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument SQLAlchemy engine when tracing is enabled."""

    if not tracing_enabled() or engine is None:
        return
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    except Exception:  # noqa: BLE001
        logger.exception("SQLAlchemy instrumentation failed")


def instrument_redis() -> None:
    """Instrument Redis clients when tracing is enabled."""

    if not tracing_enabled():
        return
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except Exception:  # noqa: BLE001
        logger.exception("Redis instrumentation failed")


def instrument_httpx() -> None:
    """Instrument HTTPX client when tracing is enabled."""

    if not tracing_enabled():
        return
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception:  # noqa: BLE001
        logger.exception("HTTPX instrumentation failed")
