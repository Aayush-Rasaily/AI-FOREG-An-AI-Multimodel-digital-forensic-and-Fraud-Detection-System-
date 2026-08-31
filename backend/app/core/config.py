"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration for the API and worker processes."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    app_name: str = "AI_Forge"
    app_env: Literal["local", "development", "test", "staging", "production"] = Field(
        default="local",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = Field(
        default="/api/v1",
        validation_alias=AliasChoices("API_PREFIX", "API_V1_PREFIX"),
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_config_path: Path = Path("configs/logging.json")

    database_url: str = Field(default="postgresql+psycopg://localhost:5432/ai_forge")
    db_pool_size: int = Field(default=10, ge=1)
    db_max_overflow: int = Field(default=20, ge=0)
    db_pool_timeout: int = Field(default=30, ge=1)
    db_health_timeout_seconds: float = Field(default=2.0, gt=0)

    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = Field(default=50, ge=1)
    celery_broker_url: str = "amqp://localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    cors_origins: list[str] = Field(default_factory=list)
    jwt_secret: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    max_upload_size_mb: int = Field(default=50, ge=1, le=10240)
    storage_backend: Literal["local", "s3", "azure_blob"] = "local"

    @property
    def environment(self) -> str:
        """Return the configured deployment environment."""

        return self.app_env

    @property
    def api_v1_prefix(self) -> str:
        """Return the version-one API prefix for existing integrations."""

        return self.api_prefix


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable-by-convention settings instance."""

    return Settings()
