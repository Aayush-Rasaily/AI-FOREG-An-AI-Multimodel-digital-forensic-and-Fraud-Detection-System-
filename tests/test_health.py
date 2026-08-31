"""Tests for the foundation health contract."""

import httpx


async def test_liveness_endpoint_returns_typed_envelope(
    client: httpx.AsyncClient,
) -> None:
    """Liveness is available without requiring external services."""

    response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.json()["data"]["status"] == "ok"
    assert response.json()["data"]["service"] == "AI_Forge"


async def test_health_endpoint_reports_application_and_database(
    client: httpx.AsyncClient,
) -> None:
    """Health reports dependency state without requiring a real database."""

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "healthy"
    assert body["data"]["database"] == "healthy"
    assert body["data"]["environment"] == "local"
    assert body["request_id"] == response.headers["X-Request-ID"]
