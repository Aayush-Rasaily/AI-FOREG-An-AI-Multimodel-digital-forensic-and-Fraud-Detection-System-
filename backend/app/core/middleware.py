"""HTTP middleware for request correlation and access logging."""

import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

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
    """Add conservative response headers for the API surface."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Apply headers without exposing runtime or infrastructure details."""

        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'")
        return response
