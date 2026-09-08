"""Phase 10A environment validation and production safety checks."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Literal

from backend.app.core.config import Settings

REQUIRED_BY_PROFILE: dict[str, tuple[str, ...]] = {
    "production": (
        "APP_ENV",
        "DATABASE_URL",
        "REDIS_URL",
        "STORAGE_ROOT",
        "JWT_SECRET",
    ),
    "staging": (
        "APP_ENV",
        "DATABASE_URL",
        "REDIS_URL",
        "STORAGE_ROOT",
        "JWT_SECRET",
    ),
    "development": ("APP_ENV", "DATABASE_URL"),
    "test": ("APP_ENV",),
    "local": (),
}

SECRET_ENV_KEYS: tuple[str, ...] = (
    "JWT_SECRET",
    "AUTH_BOOTSTRAP_PASSWORD",
    "POSTGRES_PASSWORD",
    "RABBITMQ_DEFAULT_PASS",
)

STRICT_SECRET_KEYS: frozenset[str] = frozenset({"JWT_SECRET"})

PLACEHOLDER_SECRET_FRAGMENTS: tuple[str, ...] = (
    "change-me",
    "replace-",
    "changeme",
    "replace-with",
    "example",
)


def _status(
    check: str,
    status: Literal["PASS", "WARN", "FAIL"],
    message: str,
    **details: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "check": check,
        "status": status,
        "message": message,
    }
    if details:
        payload["details"] = details
    return payload


def required_env_keys(settings: Settings) -> tuple[str, ...]:
    return REQUIRED_BY_PROFILE.get(settings.app_env, ())


def detect_missing_secrets(settings: Settings) -> list[dict[str, Any]]:
    """Detect missing or placeholder secrets (no secret values returned)."""

    findings: list[dict[str, Any]] = []
    for key in SECRET_ENV_KEYS:
        raw = os.environ.get(key)
        if key == "JWT_SECRET":
            raw = (
                settings.jwt_secret.get_secret_value()
                if settings.jwt_secret is not None
                else None
            )
        if not raw:
            if key in STRICT_SECRET_KEYS and settings.app_env in {
                "production",
                "staging",
            }:
                severity: Literal["PASS", "WARN", "FAIL"] = "FAIL"
            elif settings.app_env in {"production", "staging"}:
                severity = "WARN"
            else:
                severity = "WARN"
            findings.append(
                _status(
                    f"secret_{key.lower()}",
                    severity,
                    f"{key} is not configured.",
                )
            )
            continue
        lowered = raw.lower()
        if any(fragment in lowered for fragment in PLACEHOLDER_SECRET_FRAGMENTS):
            if key in STRICT_SECRET_KEYS and settings.app_env == "production":
                severity = "FAIL"
            else:
                severity = "WARN"
            findings.append(
                _status(
                    f"secret_{key.lower()}_placeholder",
                    severity,
                    f"{key} appears to be a placeholder value.",
                )
            )
        else:
            findings.append(
                _status(
                    f"secret_{key.lower()}",
                    "PASS",
                    f"{key} is present.",
                )
            )
    return findings


def production_safety_checks(settings: Settings) -> list[dict[str, Any]]:
    """Enforce production safety invariants."""

    findings: list[dict[str, Any]] = []
    if settings.app_env == "production":
        if settings.debug:
            findings.append(
                _status(
                    "production_debug",
                    "FAIL",
                    "DEBUG must be false in production.",
                )
            )
        else:
            findings.append(
                _status(
                    "production_debug",
                    "PASS",
                    "DEBUG is disabled in production.",
                )
            )
        if not settings.auth_required:
            findings.append(
                _status(
                    "production_auth",
                    "FAIL",
                    "JWT_SECRET must be set so authentication is required.",
                )
            )
        else:
            findings.append(
                _status(
                    "production_auth",
                    "PASS",
                    "Authentication is required in production.",
                )
            )
    else:
        findings.append(
            _status(
                "production_safety",
                "PASS",
                f"Production safety checks skipped for profile={settings.app_env}.",
            )
        )
    return findings


def validate_required_environment(settings: Settings) -> list[dict[str, Any]]:
    """Validate required environment variables for the active profile."""

    findings: list[dict[str, Any]] = []
    for key in required_env_keys(settings):
        present = bool(os.environ.get(key))
        if key == "APP_ENV":
            present = True
        if key == "DATABASE_URL":
            present = bool(settings.database_url)
        if key == "REDIS_URL":
            present = bool(settings.redis_url)
        if key == "STORAGE_ROOT":
            present = bool(settings.storage_root)
        if key == "JWT_SECRET":
            present = settings.jwt_secret is not None
        findings.append(
            _status(
                f"env_{key.lower()}",
                "PASS" if present else "FAIL",
                f"{key} {'is set' if present else 'is missing'}.",
            )
        )
    return findings


def _ensure_writable_dir(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return _status(
            "path_writable",
            "PASS",
            f"{path.as_posix()} is writable.",
            path=str(path),
        )
    except OSError as exc:
        return _status(
            "path_writable",
            "FAIL",
            f"{path.as_posix()} is not writable: {type(exc).__name__}",
            path=str(path),
        )


def verify_storage_layout(settings: Settings) -> list[dict[str, Any]]:
    """Verify storage, temp, and AI model directories (creates dirs if needed)."""

    findings: list[dict[str, Any]] = []
    storage = Path(settings.storage_root)
    temp = Path(settings.temp_storage_path)
    models = Path(settings.ai_model_root)

    for label, path in (
        ("storage_root", storage),
        ("temp_storage", temp),
        ("ai_model_root", models),
    ):
        if path.exists() and not path.is_dir():
            findings.append(
                _status(
                    label,
                    "FAIL",
                    f"{label} exists but is not a directory.",
                    path=str(path),
                )
            )
            continue
        writable = _ensure_writable_dir(path)
        writable["check"] = label
        findings.append(writable)
    return findings


def validate_environment(settings: Settings) -> dict[str, Any]:
    """Run synchronous environment / secret / safety validation."""

    checks = [
        *validate_required_environment(settings),
        *production_safety_checks(settings),
        *detect_missing_secrets(settings),
        *verify_storage_layout(settings),
    ]
    try:
        from backend.app.security.secrets import validate_runtime_secrets

        checks.extend(validate_runtime_secrets(settings))
    except Exception:  # noqa: BLE001 — never block validation assembly
        checks.append(
            _status(
                "secret_hardening",
                "WARN",
                "Extended secret validation could not run.",
            )
        )
    # Deduplicate overlapping secret PASS/FAIL preferring FAIL.
    by_check: dict[str, dict[str, Any]] = {}
    for item in checks:
        key = str(item["check"])
        existing = by_check.get(key)
        if existing is None or item["status"] == "FAIL":
            by_check[key] = item
        elif existing["status"] != "FAIL" and item["status"] == "WARN":
            by_key = by_check
            by_key[key] = item
    ordered = sorted(by_check.values(), key=lambda row: str(row["check"]))
    fail_count = sum(1 for item in ordered if item["status"] == "FAIL")
    warn_count = sum(1 for item in ordered if item["status"] == "WARN")
    return {
        "status": "FAILED" if fail_count else "PASSED",
        "fail_count": fail_count,
        "warn_count": warn_count,
        "checks": ordered,
        "profile": settings.app_env,
    }


async def verify_startup_dependencies(settings: Settings) -> dict[str, Any]:
    """Verify DB, Redis, and filesystem before accepting traffic."""

    checks: list[dict[str, Any]] = []

    # Database
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from backend.app.application.services.health_service import (
            check_database_health,
        )
        from backend.app.infrastructure.database.session import create_engine

        engine = create_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        try:
            async with session_factory() as session:
                ok = await check_database_health(
                    session,
                    timeout_seconds=settings.db_health_timeout_seconds,
                )
            if ok:
                severity_db: Literal["PASS", "WARN", "FAIL"] = "PASS"
                message = "Database connectivity verified."
            elif settings.app_env == "production":
                severity_db = "FAIL"
                message = "Database connectivity failed."
            else:
                severity_db = "WARN"
                message = "Database connectivity failed."
            checks.append(_status("database", severity_db, message))
        finally:
            await engine.dispose()
    except Exception as exc:  # noqa: BLE001
        severity_db_err: Literal["PASS", "WARN", "FAIL"] = (
            "FAIL" if settings.app_env == "production" else "WARN"
        )
        if settings.app_env in {"test", "local"}:
            severity_db_err = "WARN"
        checks.append(
            _status(
                "database",
                severity_db_err,
                f"Database verification failed: {type(exc).__name__}",
            )
        )

    # Redis
    try:
        import redis.asyncio as aioredis

        async def _ping_redis() -> None:
            client = aioredis.from_url(
                settings.redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            try:
                await client.ping()
            finally:
                await client.aclose()

        await asyncio.wait_for(_ping_redis(), timeout=2.0)
        checks.append(_status("redis", "PASS", "Redis is reachable."))
    except Exception as exc:  # noqa: BLE001
        severity_redis: Literal["PASS", "WARN", "FAIL"] = (
            "FAIL" if settings.app_env == "production" else "WARN"
        )
        if settings.app_env in {"test", "local"}:
            severity_redis = "WARN"
        checks.append(
            _status(
                "redis",
                severity_redis,
                f"Redis verification failed: {type(exc).__name__}",
            )
        )

    # Filesystem layout (idempotent)
    checks.extend(verify_storage_layout(settings))

    # Temporary OS temp accessibility
    try:
        with tempfile.NamedTemporaryFile(delete=True) as handle:
            handle.write(b"ok")
        checks.append(_status("os_temp", "PASS", "OS temporary storage is writable."))
    except OSError as exc:
        checks.append(
            _status(
                "os_temp",
                "FAIL",
                f"OS temporary storage failed: {type(exc).__name__}",
            )
        )

    fail_count = sum(1 for item in checks if item["status"] == "FAIL")
    warn_count = sum(1 for item in checks if item["status"] == "WARN")
    return {
        "status": "FAILED" if fail_count else "PASSED",
        "fail_count": fail_count,
        "warn_count": warn_count,
        "checks": checks,
        "profile": settings.app_env,
        "blocking": settings.app_env == "production",
    }


def cleanup_temporary_files(settings: Settings) -> dict[str, Any]:
    """Best-effort cleanup of application temp probe files on shutdown."""

    temp = Path(settings.temp_storage_path)
    removed = 0
    if temp.is_dir():
        for path in temp.glob(".write_probe*"):
            try:
                path.unlink(missing_ok=True)
                removed += 1
            except OSError:
                continue
    return {"removed": removed, "path": temp.as_posix()}
