"""HTTP middleware for request correlation, access logging, and security."""

import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.app.core.request_context import (
    clear_request_id,
    set_request_id,
)
from backend.app.monitoring.logging import (
    clear_observability_context,
    extract_ids_from_path,
    observability_log_fields,
    set_case_id,
    set_evidence_id,
    set_trace_id,
    set_user_id,
)
from backend.app.monitoring.prometheus import observe_request
from backend.app.monitoring.tracing import get_trace_id
from backend.app.security.headers import apply_security_headers
from backend.app.security.ratelimit import (
    allow_request,
    classify_request,
    identity_keys,
)

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request identifier and emit one access log per request."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process a request within an isolated correlation context."""

        request_id = uuid4()
        set_request_id(request_id)
        request.state.request_id = request_id
        started_at = perf_counter()
        response: Response | None = None

        path_ids = extract_ids_from_path(request.url.path)
        set_case_id(path_ids.get("case_id"))
        set_evidence_id(path_ids.get("evidence_id"))
        user = getattr(request.state, "user", None)
        if user is not None and getattr(user, "id", None) is not None:
            set_user_id(str(user.id))
        set_trace_id(get_trace_id())

        try:
            response = await call_next(request)
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            status_code = response.status_code if response else 500
            path = request.url.path
            # Refresh trace id after handler in case instrumentation created one.
            set_trace_id(get_trace_id())
            extras = {
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                **observability_log_fields(),
            }
            logger.info("HTTP request completed", extra=extras)
            if not path.endswith("/metrics"):
                observe_request(
                    method=request.method,
                    path=path,
                    status=status_code,
                    duration_seconds=duration_ms / 1000.0,
                )
            clear_observability_context()
            clear_request_id()

        assert response is not None
        response.headers["X-Request-ID"] = str(request_id)
        trace_id = get_trace_id()
        if trace_id:
            response.headers["X-Trace-ID"] = trace_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add enterprise security headers for the API surface."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Apply headers without exposing runtime or infrastructure details."""

        response = await call_next(request)
        settings = getattr(request.app.state, "settings", None)
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        https = request.url.scheme == "https" or forwarded_proto.lower() == "https"
        enable_hsts = bool(
            settings is not None
            and settings.app_env in {"production", "staging"}
            and https
        )
        apply_security_headers(
            response.headers,
            enable_hsts=enable_hsts,
            hsts_max_age=getattr(settings, "hsts_max_age", 31536000),
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce burst + sustained rate limits for sensitive API categories."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        settings = getattr(request.app.state, "settings", None)
        enabled = (
            True
            if settings is None
            else bool(getattr(settings, "rate_limit_enabled", True))
        )
        if not enabled:
            return await call_next(request)

        category = classify_request(request.method, request.url.path)
        if category is None:
            return await call_next(request)

        ip, user_key = identity_keys(request)
        use_redis = (
            True
            if settings is None
            else bool(getattr(settings, "rate_limit_use_redis", True))
        )
        allowed = await allow_request(
            category=category,
            ip=ip,
            user_key=user_key,
            use_redis=use_redis,
        )
        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "category": category,
                    "client": ip,
                },
            )
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please retry later.",
                        "request_id": str(request_id) if request_id else None,
                        "details": {"category": category},
                    }
                },
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
