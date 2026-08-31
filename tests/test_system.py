"""Tests for safe system information."""

import httpx


async def test_system_info_does_not_expose_runtime_secrets(
    client: httpx.AsyncClient,
) -> None:
    """System information contains only explicitly safe diagnostics."""

    response = await client.get("/api/v1/system/info")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["service"] == "AI_Forge"
    assert "database_url" not in response.text
    assert "jwt_secret" not in response.text
    assert "filesystem" not in response.text
