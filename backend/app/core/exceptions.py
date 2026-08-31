"""Application exception types and FastAPI exception handlers."""

import logging
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Base exception for expected application failures."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details) if details else None


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "RESOURCE_NOT_FOUND"


class ExternalServiceError(ApplicationError):
    """Raised when a downstream dependency cannot fulfill a request."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "EXTERNAL_SERVICE_ERROR"


def _error_payload(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: UUID | None = None,
) -> dict[str, Any]:
    """Build a serialized error response with request correlation."""

    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id or get_request_id(),
            details=details,
        )
    ).model_dump(mode="json")


def _request_id_from(request: Request) -> UUID | None:
    """Read correlation state even after middleware cleanup."""

    return getattr(request.state, "request_id", None) or get_request_id()


def _request_headers(request_id: UUID | None) -> dict[str, str]:
    """Return correlation headers only when a request identifier exists."""

    return {"X-Request-ID": str(request_id)} if request_id else {}


async def app_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Translate expected application exceptions into stable JSON."""

    if not isinstance(exc, ApplicationError):
        raise TypeError("Application exception handler received an invalid exception.")
    request_id = _request_id_from(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ),
        headers=_request_headers(request_id),
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return validation errors without leaking framework internals."""

    if not isinstance(exc, RequestValidationError):
        raise TypeError("Validation exception handler received an invalid exception.")
    request_id = _request_id_from(request)
    errors = [
        {
            "loc": error.get("loc"),
            "message": error.get("msg"),
            "type": error.get("type"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            code="VALIDATION_ERROR",
            message="The request could not be validated.",
            details={"errors": errors},
            request_id=request_id,
        ),
        headers=_request_headers(request_id),
    )


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Translate framework HTTP errors into the stable error contract."""

    if not isinstance(exc, StarletteHTTPException):
        raise TypeError("HTTP exception handler received an invalid exception.")
    request_id = _request_id_from(request)
    message = exc.detail if isinstance(exc.detail, str) else "The request failed."
    headers = dict(exc.headers or {})
    headers.update(_request_headers(request_id))
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            code=f"HTTP_{exc.status_code}",
            message=message,
            request_id=request_id,
        ),
        headers=headers,
    )


async def database_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Hide database implementation details from API clients."""

    if not isinstance(exc, SQLAlchemyError):
        raise TypeError("Database exception handler received an invalid exception.")
    request_id = _request_id_from(request)
    logger.exception("Database operation failed", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=_error_payload(
            code="DATABASE_UNAVAILABLE",
            message="The database service is temporarily unavailable.",
            request_id=request_id,
        ),
        headers=_request_headers(request_id),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Hide unexpected failure details while preserving server diagnostics."""

    logger.exception("Unhandled application exception", exc_info=exc)
    request_id = _request_id_from(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            request_id=request_id,
        ),
        headers=_request_headers(request_id),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the platform's exception-to-HTTP translation boundary."""

    app.add_exception_handler(ApplicationError, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
