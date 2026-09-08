"""Restore validation helpers (Phase 10F)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.core.config import Settings, get_settings
from backend.app.recovery.verification import verify_backup_bundle

REQUIRED_COMPONENTS = (
    "configuration",
    "evidence_metadata",
)


def validate_restore_bundle(
    bundle_dir: Path | str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Validate integrity and component readiness before applying a restore."""

    runtime = settings or get_settings()
    root = Path(bundle_dir)
    verification = verify_backup_bundle(root)
    checks = list(verification.get("checks", []))

    if not verification.get("valid"):
        return {
            "status": "FAILED",
            "restore_allowed": False,
            "verification": verification,
            "checks": checks,
            "message": "Integrity verification failed; restore blocked.",
        }

    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    components = manifest.get("components", {})

    for name in REQUIRED_COMPONENTS:
        present = name in components and components[name].get("status") == "captured"
        checks.append(
            {
                "check": f"component:{name}",
                "status": "PASS" if present else "FAIL",
                "message": (
                    f"Component {name} is ready."
                    if present
                    else f"Component {name} is missing."
                ),
            }
        )

    for name in ("postgresql", "reports", "configuration"):
        status = components.get(name, {}).get("status")
        if status == "captured":
            checks.append(
                {
                    "check": f"restore_target:{name}",
                    "status": "PASS",
                    "message": f"{name} artifact present for restore.",
                }
            )
        elif status in {"empty", "pending_operator"}:
            checks.append(
                {
                    "check": f"restore_target:{name}",
                    "status": "WARN",
                    "message": f"{name} artifact not captured in this bundle.",
                }
            )

    # Configuration compatibility
    config_file = root / "configuration.json"
    if config_file.is_file():
        payload = json.loads(config_file.read_text(encoding="utf-8"))
        exported_env = payload.get("configuration", {}).get("app_env") or payload.get(
            "release", {}
        ).get("environment")
        checks.append(
            {
                "check": "configuration_readable",
                "status": "PASS",
                "message": f"Configuration export readable (env={exported_env}).",
            }
        )
        if exported_env and exported_env != runtime.app_env:
            checks.append(
                {
                    "check": "environment_match",
                    "status": "WARN",
                    "message": (
                        f"Bundle env={exported_env} differs from "
                        f"runtime env={runtime.app_env}."
                    ),
                }
            )

    failed = [item for item in checks if item["status"] == "FAIL"]
    return {
        "status": "READY" if not failed else "FAILED",
        "restore_allowed": not failed,
        "verification": verification,
        "checks": checks,
        "fail_count": len(failed),
        "bundle_dir": root.as_posix(),
        "message": (
            "Restore validation passed." if not failed else "Restore validation failed."
        ),
    }


def plan_restore(bundle_dir: Path | str) -> dict[str, Any]:
    """Return an ordered, non-destructive restore plan for operators."""

    validation = validate_restore_bundle(bundle_dir)
    steps = [
        "1. Put API/workers in maintenance (stop writers).",
        "2. Verify backup bundle checksums (verify_backup.sh).",
        "3. Restore PostgreSQL from postgres.dump.sql if present.",
        "4. Restore Redis from redis.rdb only if intentionally persisted.",
        "5. Restore reports/exports trees from the bundle.",
        "6. Re-apply configuration secrets from vault (never from plaintext dumps).",
        "7. Run migrations if schema_version requires it.",
        "8. Run platform readiness + release-check.",
        "9. Resume traffic.",
    ]
    return {
        "validation": validation,
        "steps": steps,
        "destructive": True,
        "note": "This helper never mutates production data; scripts perform restores.",
    }
