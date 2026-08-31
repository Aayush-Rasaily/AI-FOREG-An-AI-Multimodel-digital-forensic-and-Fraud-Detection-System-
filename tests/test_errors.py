"""Tests for the global API error contract."""

import json
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError

from backend.app.core.exceptions import (
    unhandled_exception_handler,
    validation_exception_handler,
)


async def test_unknown_route_returns_consistent_error(
    client: httpx.AsyncClient,
) -> None:
    """404 responses use the public error envelope and request correlation."""

    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "HTTP_404"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_validation_errors_are_sanitized() -> None:
    """Validation responses omit submitted values from their details."""

    request = Request({"type": "http", "method": "GET", "path": "/"})
    request.state.request_id = uuid4()
    validation_error = RequestValidationError(
        [
            {
                "type": "string_type",
                "loc": ("query", "token"),
                "msg": "Input should be a valid string",
                "input": "sensitive-value",
            }
        ]
    )

    response = await validation_exception_handler(request, validation_error)
    payload: dict[str, Any] = json.loads(response.body)

    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert "sensitive-value" not in response.body.decode()


@pytest.mark.asyncio
async def test_unhandled_errors_are_generic() -> None:
    """Unexpected exceptions do not disclose implementation details."""

    request = Request({"type": "http", "method": "GET", "path": "/"})
    request.state.request_id = uuid4()

    response = await unhandled_exception_handler(
        request,
        RuntimeError("database password must not leak"),
    )

    assert response.status_code == 500
    assert "database password" not in response.body.decode()
    assert json.loads(response.body)["error"]["code"] == "INTERNAL_ERROR"
