"""Backup integrity verification (Phase 10F)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD
from backend.app.recovery.backup import BACKUP_ENGINE_VERSION, MANIFEST_NAME


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(bundle_dir: Path) -> dict[str, Any]:
    path = bundle_dir / MANIFEST_NAME
    if not path.is_file():
        raise FileNotFoundError(f"Backup manifest missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_backup_bundle(bundle_dir: Path | str) -> dict[str, Any]:
    """Verify SHA-256 checksums and version metadata before restore."""

    root = Path(bundle_dir)
    checks: list[dict[str, Any]] = []
    try:
        manifest = load_manifest(root)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
        return {
            "status": "FAILED",
            "valid": False,
            "checks": [
                {
                    "check": "manifest_present",
                    "status": "FAIL",
                    "message": str(exc),
                }
            ],
        }

    checks.append(
        {
            "check": "manifest_present",
            "status": "PASS",
            "message": "Manifest loaded.",
        }
    )

    # Recompute manifest body checksum excluding manifest_sha256 field.
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    expected = manifest.get("manifest_sha256")
    actual = hashlib.sha256(
        json.dumps(body, sort_keys=True, indent=2).encode("utf-8")
    ).hexdigest()
    checks.append(
        {
            "check": "manifest_checksum",
            "status": "PASS" if expected == actual else "FAIL",
            "message": (
                "Manifest checksum matches."
                if expected == actual
                else "Manifest checksum mismatch."
            ),
        }
    )

    schema = manifest.get("schema_version")
    checks.append(
        {
            "check": "schema_version",
            "status": "PASS" if schema == EXPECTED_MIGRATION_HEAD else "WARN",
            "message": (
                f"Schema version {schema} "
                f"(expected head {EXPECTED_MIGRATION_HEAD})."
            ),
        }
    )
    engine = manifest.get("backup_engine_version")
    checks.append(
        {
            "check": "backup_engine_version",
            "status": "PASS" if engine == BACKUP_ENGINE_VERSION else "WARN",
            "message": f"Backup engine version {engine}.",
        }
    )

    for item in manifest.get("files", []):
        relative = str(item.get("path", ""))
        target = root / relative
        if not target.is_file():
            checks.append(
                {
                    "check": f"file:{relative}",
                    "status": "FAIL",
                    "message": "Missing file referenced by manifest.",
                }
            )
            continue
        digest = _sha256_file(target)
        ok = digest == item.get("sha256")
        checks.append(
            {
                "check": f"file:{relative}",
                "status": "PASS" if ok else "FAIL",
                "message": (
                    "Checksum matches." if ok else "Checksum mismatch."
                ),
            }
        )

    failed = [item for item in checks if item["status"] == "FAIL"]
    warned = [item for item in checks if item["status"] == "WARN"]
    status = "PASSED" if not failed else "FAILED"
    if not failed and warned:
        status = "PASSED_WITH_WARNINGS"
    return {
        "status": status,
        "valid": not failed,
        "stamp": manifest.get("stamp"),
        "created_at": manifest.get("created_at"),
        "application_version": manifest.get("application_version"),
        "schema_version": schema,
        "backup_engine_version": engine,
        "checks": checks,
        "fail_count": len(failed),
        "warn_count": len(warned),
        "bundle_dir": root.as_posix(),
    }
