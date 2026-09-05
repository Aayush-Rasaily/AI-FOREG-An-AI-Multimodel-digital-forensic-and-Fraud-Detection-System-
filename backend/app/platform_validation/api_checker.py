"""API route and OpenAPI compatibility checks."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

from backend.app.platform_validation.models import CheckOutcome, CheckStatus
from backend.app.platform_validation.policy import REQUIRED_API_PATHS


def _collect_paths(app: FastAPI, *, api_prefix: str) -> set[str]:
    prefix = api_prefix.rstrip("/")
    paths: set[str] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if path.startswith(prefix):
            path = path[len(prefix) :] or "/"
        paths.add(path)
    return paths


def check_api_compatibility(
    app: FastAPI,
    *,
    api_prefix: str = "/api/v1",
) -> CheckOutcome:
    """Ensure required Phase API paths are registered."""

    registered = _collect_paths(app, api_prefix=api_prefix)
    missing = [path for path in REQUIRED_API_PATHS if path not in registered]
    details: dict[str, Any] = {
        "required": list(REQUIRED_API_PATHS),
        "missing": missing,
        "registered_count": len(registered),
    }
    if missing:
        return CheckOutcome(
            key="api_compatibility",
            category="api",
            label="API compatibility",
            status=CheckStatus.FAIL,
            message=f"Missing required API paths: {', '.join(missing)}",
            details=details,
        )
    return CheckOutcome(
        key="api_compatibility",
        category="api",
        label="API compatibility",
        status=CheckStatus.PASS,
        message="Required API paths are registered.",
        details=details,
    )


def check_openapi_generation(app: FastAPI) -> CheckOutcome:
    """Generate OpenAPI schema deterministically and validate structure."""

    try:
        schema = app.openapi()
    except Exception as exc:  # noqa: BLE001 — surface schema errors only
        return CheckOutcome(
            key="openapi_generation",
            category="api",
            label="OpenAPI generation",
            status=CheckStatus.FAIL,
            message=f"OpenAPI generation failed: {type(exc).__name__}",
            details={"error": str(exc)},
        )
    paths = schema.get("paths") or {}
    details = {
        "openapi": schema.get("openapi"),
        "path_count": len(paths),
        "has_info": "info" in schema,
    }
    if not paths or "info" not in schema:
        return CheckOutcome(
            key="openapi_generation",
            category="api",
            label="OpenAPI generation",
            status=CheckStatus.FAIL,
            message="OpenAPI schema is incomplete.",
            details=details,
        )
    return CheckOutcome(
        key="openapi_generation",
        category="api",
        label="OpenAPI generation",
        status=CheckStatus.PASS,
        message="OpenAPI schema generated successfully.",
        details=details,
    )
