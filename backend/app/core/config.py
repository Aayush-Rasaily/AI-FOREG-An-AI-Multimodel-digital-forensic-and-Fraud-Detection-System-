"""Application settings loaded from environment variables."""

import os
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SUPPORTED_EXTENSIONS = {
    "image": ["jpg", "jpeg", "png", "webp", "tif", "tiff"],
    "document": ["pdf", "docx"],
    "video": ["mp4", "mov", "avi", "mkv", "webm"],
    "audio": ["wav", "mp3", "m4a", "aac", "flac"],
}
DEFAULT_SUPPORTED_MIME_TYPES = {
    "image": ["image/jpeg", "image/png", "image/webp", "image/tiff"],
    "document": [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
    "video": [
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/x-matroska",
        "video/webm",
    ],
    "audio": [
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp4",
        "audio/aac",
        "audio/flac",
    ],
}


class Settings(BaseSettings):
    """Validated runtime configuration for the API and worker processes."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
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
    db_pool_recycle: int = Field(default=1800, ge=60)
    db_health_timeout_seconds: float = Field(default=2.0, gt=0)

    storage_root: Path = Path("data")
    temp_storage_path: Path = Field(
        default=Path("data/tmp"),
        validation_alias=AliasChoices("TEMP_STORAGE_PATH", "TMP_STORAGE_PATH"),
    )
    ai_model_root: Path = Field(
        default=Path("models"),
        validation_alias=AliasChoices("AI_MODEL_ROOT", "MODEL_ROOT"),
    )
    storage_backend: Literal["local", "s3", "minio"] = "local"
    max_upload_size_mb: int = Field(default=50, ge=1, le=10240)
    upload_chunk_size_bytes: int = Field(default=1024 * 1024, ge=4096)
    supported_extensions: dict[str, list[str]] = Field(
        default_factory=lambda: deepcopy(DEFAULT_SUPPORTED_EXTENSIONS)
    )
    supported_mime_types: dict[str, list[str]] = Field(
        default_factory=lambda: deepcopy(DEFAULT_SUPPORTED_MIME_TYPES)
    )
    ocr_enabled: bool = False
    ocr_command: str = "tesseract"
    ffprobe_command: str = "ffprobe"
    ffmpeg_command: str = "ffmpeg"
    extraction_max_pages: int = Field(default=1000, ge=1, le=10000)
    extraction_max_text_chars: int = Field(
        default=1_000_000,
        ge=1_000,
        le=10_000_000,
    )
    extraction_max_items: int = Field(default=10_000, ge=100, le=100_000)
    media_sample_interval_seconds: float = Field(default=5.0, gt=0)
    media_max_frames: int = Field(default=120, ge=1, le=10000)

    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = Field(default=50, ge=1)
    celery_broker_url: str = "amqp://localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    cors_origins: list[str] = Field(default_factory=list)
    jwt_secret: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    auth_access_token_minutes: int = Field(default=15, ge=1, le=1440)
    auth_refresh_token_days: int = Field(default=7, ge=1, le=90)
    auth_remember_me_days: int = Field(default=30, ge=1, le=180)
    auth_bootstrap_username: str = "admin"
    auth_bootstrap_password: SecretStr | None = None

    @property
    def environment(self) -> str:
        """Return the configured deployment environment."""

        return self.app_env

    @property
    def api_v1_prefix(self) -> str:
        """Return the version-one API prefix for existing integrations."""

        return self.api_prefix

    @property
    def auth_required(self) -> bool:
        """Return True when JWT authentication is configured."""

        return self.jwt_secret is not None


class DevelopmentSettings(Settings):
    """Defaults tuned for local interactive development."""

    model_config = SettingsConfigDict(
        env_file=(".env.development", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    app_env: Literal["local", "development", "test", "staging", "production"] = (
        "development"
    )
    debug: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"


class TestingSettings(Settings):
    """Defaults tuned for automated tests (in-memory friendly)."""

    __test__ = False

    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    app_env: Literal["local", "development", "test", "staging", "production"] = "test"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite://"
    redis_url: str = "redis://localhost:6379/15"
    storage_root: Path = Path("data/test")
    temp_storage_path: Path = Path("data/test/tmp")
    ai_model_root: Path = Path("models/test")


class ProductionSettings(Settings):
    """Defaults tuned for hardened production deployments."""

    model_config = SettingsConfigDict(
        env_file=(".env.production", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    app_env: Literal["local", "development", "test", "staging", "production"] = (
        "production"
    )
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    storage_root: Path = Path("/app/data")
    temp_storage_path: Path = Path("/app/data/tmp")
    ai_model_root: Path = Path("/app/models")


def settings_class_for_env(
    app_env: str | None = None,
) -> type[Settings]:
    """Return the Settings subclass for an environment profile."""

    resolved = (
        app_env or os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "local"
    ).lower()
    mapping: dict[str, type[Settings]] = {
        "development": DevelopmentSettings,
        "dev": DevelopmentSettings,
        "test": TestingSettings,
        "testing": TestingSettings,
        "production": ProductionSettings,
        "prod": ProductionSettings,
        "staging": ProductionSettings,
        "local": Settings,
    }
    return mapping.get(resolved, Settings)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable-by-convention settings instance."""

    cls = settings_class_for_env()
    return cls()
