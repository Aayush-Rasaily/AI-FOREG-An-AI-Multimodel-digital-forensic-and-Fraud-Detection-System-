"""Startup secret validation and log redaction helpers (Phase 10D)."""

from __future__ import annotations

import os
import re
from typing import Any, Literal

from backend.app.core.config import Settings

SECRET_ENV_KEYS: tuple[str, ...] = (
    "JWT_SECRET",
    "AUTH_BOOTSTRAP_PASSWORD",
    "POSTGRES_PASSWORD",
    "RABBITMQ_DEFAULT_PASS",
    "ENCRYPTION_KEY",
    "API_KEY",
    "OPENAI_API_KEY",
    "S3_SECRET_ACCESS_KEY",
)

REQUIRED_PRODUCTION_SECRETS: frozenset[str] = frozenset(
    {
        "JWT_SECRET",
        "DATABASE_URL",
        "REDIS_URL",
    }
)

PLACEHOLDER_FRAGMENTS: tuple[str, ...] = (
    "change-me",
    "changeme",
    "replace-",
    "replace-with",
    "example",
    "todo",
    "password",
)

_REDACT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(api[_-]?key|secret|token|credential)\s*[:=]\s*\S+"),
    re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+\S+"),
    re.compile(r"(?i)(cookie|set-cookie)\s*[:=]\s*\S+"),
    re.compile(r"(?i)jwt_secret\s*[:=]\s*\S+"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)

REDACTION_PLACEHOLDER = "[REDACTED]"


def _status(
    check: str,
    status: Literal["PASS", "WARN", "FAIL"],
    message: str,
) -> dict[str, Any]:
    return {"check": check, "status": status, "message": message}


def redact_secrets(text: str) -> str:
    """Remove common secret material from log/exception text."""

    redacted = text
    for pattern in _REDACT_PATTERNS:
        redacted = pattern.sub(REDACTION_PLACEHOLDER, redacted)
    return redacted


def validate_runtime_secrets(settings: Settings) -> list[dict[str, Any]]:
    """Validate JWT/DB/Redis/API/encryption secrets for the active profile."""

    findings: list[dict[str, Any]] = []
    production_like = settings.app_env in {"production", "staging"}

    jwt = (
        settings.jwt_secret.get_secret_value()
        if settings.jwt_secret is not None
        else None
    )
    if not jwt:
        findings.append(
            _status(
                "secret_jwt_secret",
                "FAIL" if production_like else "WARN",
                "JWT_SECRET is not configured.",
            )
        )
    elif any(fragment in jwt.lower() for fragment in PLACEHOLDER_FRAGMENTS):
        findings.append(
            _status(
                "secret_jwt_secret_placeholder",
                "FAIL" if settings.app_env == "production" else "WARN",
                "JWT_SECRET appears to be a placeholder value.",
            )
        )
    elif len(jwt) < 32 and production_like:
        findings.append(
            _status(
                "secret_jwt_secret_strength",
                "FAIL" if settings.app_env == "production" else "WARN",
                "JWT_SECRET should be at least 32 characters in production.",
            )
        )
    else:
        findings.append(
            _status("secret_jwt_secret", "PASS", "JWT_SECRET is present.")
        )

    if not settings.database_url:
        findings.append(
            _status(
                "secret_database_url",
                "FAIL" if production_like else "WARN",
                "DATABASE_URL is not configured.",
            )
        )
    elif "localhost" in settings.database_url and settings.app_env == "production":
        findings.append(
            _status(
                "secret_database_url_host",
                "WARN",
                "DATABASE_URL points at localhost in production.",
            )
        )
    else:
        findings.append(
            _status("secret_database_url", "PASS", "DATABASE_URL is present.")
        )

    if not settings.redis_url:
        findings.append(
            _status(
                "secret_redis_url",
                "FAIL" if production_like else "WARN",
                "REDIS_URL is not configured.",
            )
        )
    else:
        findings.append(
            _status("secret_redis_url", "PASS", "REDIS_URL is present.")
        )

    for key in (
        "ENCRYPTION_KEY",
        "API_KEY",
        "OPENAI_API_KEY",
        "S3_SECRET_ACCESS_KEY",
        "AUTH_BOOTSTRAP_PASSWORD",
        "POSTGRES_PASSWORD",
    ):
        raw = os.environ.get(key)
        if not raw:
            findings.append(
                _status(
                    f"secret_{key.lower()}",
                    "WARN",
                    f"{key} is not set (optional unless required by deployment).",
                )
            )
            continue
        if any(fragment in raw.lower() for fragment in PLACEHOLDER_FRAGMENTS):
            findings.append(
                _status(
                    f"secret_{key.lower()}_placeholder",
                    "WARN",
                    f"{key} appears to be a placeholder value.",
                )
            )
        else:
            findings.append(
                _status(f"secret_{key.lower()}", "PASS", f"{key} is present.")
            )

    # Secure session/token TTL bounds for production
    if settings.app_env == "production":
        if settings.auth_access_token_minutes > 60:
            findings.append(
                _status(
                    "session_access_ttl",
                    "WARN",
                    "Access token TTL exceeds 60 minutes in production.",
                )
            )
        else:
            findings.append(
                _status(
                    "session_access_ttl",
                    "PASS",
                    "Access token TTL is within recommended bounds.",
                )
            )
        if settings.debug:
            findings.append(
                _status(
                    "session_debug",
                    "FAIL",
                    "Debug mode must be disabled for secure sessions.",
                )
            )

    return findings


def assert_production_secrets(settings: Settings) -> None:
    """Raise RuntimeError when production secrets are missing/weak."""

    if settings.app_env != "production":
        return
    failures = [
        item
        for item in validate_runtime_secrets(settings)
        if item["status"] == "FAIL"
    ]
    if failures:
        messages = "; ".join(item["message"] for item in failures)
        raise RuntimeError(
            "Production secret validation failed: " + messages
        )
