"""Tests for environment-backed configuration."""

from pydantic import SecretStr

from backend.app.core.config import Settings


def test_settings_load_required_phase_one_environment(monkeypatch) -> None:
    """Supported environment variables map to validated settings."""

    monkeypatch.setenv("APP_NAME", "Test Forge")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("CORS_ORIGINS", '["https://example.test"]')
    monkeypatch.setenv("JWT_SECRET", "test-only-secret")
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "100")
    monkeypatch.setenv("STORAGE_BACKEND", "s3")

    settings = Settings(_env_file=None)

    assert settings.app_name == "Test Forge"
    assert settings.app_env == "test"
    assert settings.cors_origins == ["https://example.test"]
    assert settings.jwt_secret == SecretStr("test-only-secret")
    assert settings.max_upload_size_mb == 100
    assert settings.storage_backend == "s3"
