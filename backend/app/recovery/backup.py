"""Enterprise backup bundle creation (Phase 10F)."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.app.core.config import Settings, get_settings
from backend.app.deployment.configuration import export_configuration
from backend.app.deployment.release import (
    EXPECTED_MIGRATION_HEAD,
    build_release_metadata,
)

BACKUP_ENGINE_VERSION = "10f.1.0"
MANIFEST_NAME = "manifest.json"


def backup_root(settings: Settings | None = None) -> Path:
    runtime = settings or get_settings()
    root = Path(runtime.storage_root) / "deployment" / "backups"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")
    path.write_bytes(encoded)
    return _sha256_bytes(encoded)


def _copy_tree_if_exists(source: Path, destination: Path) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    if not source.exists():
        return artifacts
    destination.mkdir(parents=True, exist_ok=True)
    if source.is_file():
        target = destination / source.name
        shutil.copy2(source, target)
        artifacts.append(
            {
                "path": target.name,
                "sha256": _sha256_file(target),
                "bytes": target.stat().st_size,
            }
        )
        return artifacts
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        artifacts.append(
            {
                "path": f"{destination.name}/{relative}",
                "sha256": _sha256_file(target),
                "bytes": target.stat().st_size,
            }
        )
    return artifacts


def create_backup_bundle(
    settings: Settings | None = None,
    *,
    stamp: str | None = None,
    include_reports: bool = True,
    include_exports: bool = True,
    include_ai_config: bool = True,
    database_dump_path: Path | None = None,
    redis_dump_path: Path | None = None,
) -> dict[str, Any]:
    """Create a stamped backup bundle with SHA-256 integrity metadata.

    Does not alter forensic data in place; only copies operational artifacts.
    """

    runtime = settings or get_settings()
    created = datetime.now(UTC).replace(microsecond=0)
    stamp_value = stamp or created.strftime("%Y%m%dT%H%M%SZ")
    dest = backup_root(runtime) / stamp_value
    dest.mkdir(parents=True, exist_ok=True)

    components: dict[str, Any] = {}
    file_index: list[dict[str, Any]] = []

    # Application / AI configuration (sanitized export)
    config_payload = {
        "configuration": export_configuration(runtime),
            "release": build_release_metadata(
                app_version=runtime.app_version,
                environment=runtime.app_env,
            ),
        "ai": {
            "model_root": Path(runtime.ai_model_root).as_posix(),
            "model_root_exists": Path(runtime.ai_model_root).exists(),
        },
    }
    config_path = dest / "configuration.json"
    file_index.append(
        {
            "path": config_path.name,
            "sha256": _write_json(config_path, config_payload),
            "bytes": config_path.stat().st_size,
            "component": "configuration",
        }
    )
    components["configuration"] = {"status": "captured", "path": config_path.name}
    if include_ai_config:
        components["ai_configuration"] = {
            "status": "captured",
            "model_root": Path(runtime.ai_model_root).as_posix(),
        }

    # Evidence metadata index (paths/hashes only — not bulk binary originals)
    evidence_meta = {
        "storage_root": Path(runtime.storage_root).as_posix(),
        "storage_backend": runtime.storage_backend,
        "note": (
            "Binary evidence originals remain under storage_root; "
            "operators must back up object storage / PVC separately."
        ),
    }
    evidence_path = dest / "evidence-metadata.json"
    file_index.append(
        {
            "path": evidence_path.name,
            "sha256": _write_json(evidence_path, evidence_meta),
            "bytes": evidence_path.stat().st_size,
            "component": "evidence_metadata",
        }
    )
    components["evidence_metadata"] = {"status": "captured", "path": evidence_path.name}

    # Reports
    if include_reports:
        reports_src = Path(runtime.storage_root) / "reports"
        report_artifacts = _copy_tree_if_exists(reports_src, dest / "reports")
        for item in report_artifacts:
            item["component"] = "reports"
        file_index.extend(report_artifacts)
        components["reports"] = {
            "status": "captured" if report_artifacts else "empty",
            "count": len(report_artifacts),
        }

    # Investigation exports
    if include_exports:
        exports_src = Path(runtime.storage_root) / "exports"
        export_artifacts = _copy_tree_if_exists(exports_src, dest / "exports")
        for item in export_artifacts:
            item["component"] = "exports"
        file_index.extend(export_artifacts)
        components["exports"] = {
            "status": "captured" if export_artifacts else "empty",
            "count": len(export_artifacts),
        }

    # Optional DB / Redis dump artifacts provided by scripts
    if database_dump_path and database_dump_path.is_file():
        target = dest / "postgres.dump.sql"
        if database_dump_path.resolve() != target.resolve():
            shutil.copy2(database_dump_path, target)
        file_index.append(
            {
                "path": target.name,
                "sha256": _sha256_file(target),
                "bytes": target.stat().st_size,
                "component": "postgresql",
            }
        )
        components["postgresql"] = {"status": "captured", "path": target.name}
    else:
        components["postgresql"] = {
            "status": "pending_operator",
            "note": "Run pg_dump via deployment/scripts/backup.sh",
        }

    if redis_dump_path and redis_dump_path.is_file():
        target = dest / "redis.rdb"
        if redis_dump_path.resolve() != target.resolve():
            shutil.copy2(redis_dump_path, target)
        file_index.append(
            {
                "path": target.name,
                "sha256": _sha256_file(target),
                "bytes": target.stat().st_size,
                "component": "redis",
            }
        )
        components["redis"] = {"status": "captured", "path": target.name}
    else:
        components["redis"] = {
            "status": "pending_operator",
            "note": "Optional redis-cli --rdb or BGSAVE snapshot",
        }

    manifest = {
        "id": str(uuid4()),
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "stamp": stamp_value,
        "backup_engine_version": BACKUP_ENGINE_VERSION,
        "application_version": runtime.app_version,
        "schema_version": EXPECTED_MIGRATION_HEAD,
        "environment": runtime.app_env,
        "components": components,
        "files": sorted(file_index, key=lambda item: item["path"]),
        "bundle_dir": dest.as_posix(),
    }
    # Manifest checksum excludes itself; stored separately for verify.
    manifest_body = json.dumps(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"},
        sort_keys=True,
        indent=2,
    ).encode("utf-8")
    manifest["manifest_sha256"] = _sha256_bytes(manifest_body)
    (dest / MANIFEST_NAME).write_bytes(
        json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8")
    )
    return manifest
