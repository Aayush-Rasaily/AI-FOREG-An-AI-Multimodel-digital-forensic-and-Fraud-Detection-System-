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

        try:
            response = await call_next(request)
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "HTTP request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code if response else 500,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            clear_request_id()

        response.headers["X-Request-ID"] = str(request_id)
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
