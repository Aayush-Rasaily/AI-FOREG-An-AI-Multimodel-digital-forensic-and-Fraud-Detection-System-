"""Deterministic backup metadata utilities (no cloud integrations)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.app.core.config import Settings
from backend.app.deployment.configuration import export_configuration
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
)


def _backup_root(settings: Settings) -> Path:
    root = Path(settings.storage_root) / "deployment" / "backups"
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_backup_metadata(
    settings: Settings,
    *,
    kind: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist deterministic backup metadata for DR verification."""

    now = datetime.now(UTC).replace(microsecond=0)
    record = {
        "id": str(uuid4()),
        "kind": kind,
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "application_version": settings.app_version,
        "environment": settings.app_env,
        "details": details or {},
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
    }
    path = _backup_root(settings) / f"{record['id']}.json"
    path.write_text(
        json.dumps(record, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    record["path"] = path.as_posix()
    return record


def create_database_backup_metadata(settings: Settings) -> dict[str, Any]:
    """Record metadata describing a logical database backup point."""

    return create_backup_metadata(
        settings,
        kind="database",
        details={
            "note": "Logical backup marker only; operator runs pg_dump externally.",
            "database_configured": bool(settings.database_url),
        },
    )


def create_report_archive_metadata(settings: Settings) -> dict[str, Any]:
    """Record metadata for report archive readiness."""

    reports_dir = Path(settings.storage_root) / "reports"
    return create_backup_metadata(
        settings,
        kind="report_archive",
        details={
            "reports_dir": reports_dir.as_posix(),
            "exists": reports_dir.exists(),
        },
    )


def create_configuration_export(settings: Settings) -> dict[str, Any]:
    """Export configuration snapshot as backup metadata."""

    payload = export_configuration(settings)
    return create_backup_metadata(
        settings,
        kind="configuration_export",
        details=payload,
    )


def list_backup_metadata(settings: Settings) -> list[dict[str, Any]]:
    """List backup metadata records in deterministic order."""

    root = _backup_root(settings)
    items: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        data["path"] = path.as_posix()
        items.append(data)
    return sorted(
        items,
        key=lambda item: (item.get("created_at", ""), item.get("id", "")),
    )
