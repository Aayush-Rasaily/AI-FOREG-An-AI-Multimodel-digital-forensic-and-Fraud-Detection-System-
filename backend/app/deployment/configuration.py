"""Application configuration profiles and safe configuration export."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import Settings
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
)

REQUIRED_PRODUCTION_ENV_VARS: tuple[str, ...] = (
    "APP_ENV",
    "APP_VERSION",
    "DATABASE_URL",
    "REDIS_URL",
    "STORAGE_ROOT",
    "JWT_SECRET",
)

PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "local": {"debug": True, "docs_enabled": True},
    "development": {"debug": True, "docs_enabled": True},
    "test": {"debug": True, "docs_enabled": False},
    "staging": {"debug": False, "docs_enabled": False},
    "production": {"debug": False, "docs_enabled": False},
}


def configuration_profile(settings: Settings) -> dict[str, Any]:
    """Return the active configuration profile summary (no secrets)."""

    defaults = PROFILE_DEFAULTS.get(settings.app_env, {})
    return {
        "profile": settings.app_env,
        "application": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "api_prefix": settings.api_prefix,
        "storage_backend": settings.storage_backend,
        "auth_required": settings.auth_required,
        "cors_origins_count": len(settings.cors_origins),
        "docs_enabled": bool(defaults.get("docs_enabled", settings.debug)),
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
    }


def export_configuration(settings: Settings) -> dict[str, Any]:
    """Export non-secret configuration for ops / disaster recovery metadata."""

    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "app_version": settings.app_version,
        "api_prefix": settings.api_prefix,
        "log_level": settings.log_level,
        "database_pool_size": settings.db_pool_size,
        "storage_backend": settings.storage_backend,
        "storage_root": str(settings.storage_root),
        "max_upload_size_mb": settings.max_upload_size_mb,
        "redis_configured": bool(settings.redis_url),
        "celery_broker_configured": bool(settings.celery_broker_url),
        "ocr_enabled": settings.ocr_enabled,
        "auth_required": settings.auth_required,
        "cors_origins": list(settings.cors_origins),
        "profile": configuration_profile(settings),
    }


def verify_configuration(settings: Settings) -> list[dict[str, str]]:
    """Return configuration integrity findings (deterministic ordering)."""

    findings: list[dict[str, str]] = []
    profile = settings.app_env
    if profile == "production" and settings.debug:
        findings.append(
            {
                "check": "debug_disabled_in_production",
                "status": "FAIL",
                "message": "DEBUG must be false in production.",
            }
        )
    else:
        findings.append(
            {
                "check": "debug_disabled_in_production",
                "status": "PASS",
                "message": "Debug flag is acceptable for this profile.",
            }
        )

    if profile == "production" and not settings.auth_required:
        findings.append(
            {
                "check": "auth_required_in_production",
                "status": "FAIL",
                "message": "JWT_SECRET must be configured in production.",
            }
        )
    else:
        findings.append(
            {
                "check": "auth_required_in_production",
                "status": "PASS",
                "message": "Authentication configuration is acceptable.",
            }
        )

    if not settings.database_url:
        findings.append(
            {
                "check": "database_url",
                "status": "FAIL",
                "message": "DATABASE_URL is missing.",
            }
        )
    else:
        findings.append(
            {
                "check": "database_url",
                "status": "PASS",
                "message": "DATABASE_URL is configured.",
            }
        )

    if not settings.storage_root:
        findings.append(
            {
                "check": "storage_root",
                "status": "FAIL",
                "message": "STORAGE_ROOT is missing.",
            }
        )
    else:
        findings.append(
            {
                "check": "storage_root",
                "status": "PASS",
                "message": "STORAGE_ROOT is configured.",
            }
        )

    return sorted(findings, key=lambda item: item["check"])
