"""Disaster recovery verification utilities (metadata-level only)."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import Settings
from backend.app.deployment.backup import list_backup_metadata
from backend.app.deployment.configuration import export_configuration
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
)


def verify_disaster_recovery(settings: Settings) -> dict[str, Any]:
    """Verify DR prerequisites using local backup metadata."""

    records = list_backup_metadata(settings)
    kinds = {item.get("kind") for item in records}
    checks = [
        {
            "check": "database_backup_metadata",
            "status": "PASS" if "database" in kinds else "WARN",
            "message": (
                "Database backup metadata present."
                if "database" in kinds
                else "No database backup metadata recorded yet."
            ),
        },
        {
            "check": "report_archive_metadata",
            "status": "PASS" if "report_archive" in kinds else "WARN",
            "message": (
                "Report archive metadata present."
                if "report_archive" in kinds
                else "No report archive metadata recorded yet."
            ),
        },
        {
            "check": "configuration_export",
            "status": "PASS" if "configuration_export" in kinds else "WARN",
            "message": (
                "Configuration export present."
                if "configuration_export" in kinds
                else "No configuration export recorded yet."
            ),
        },
    ]
    checks = sorted(checks, key=lambda item: item["check"])
    warned = [item for item in checks if item["status"] != "PASS"]
    return {
        "status": "READY" if not warned else "PARTIAL",
        "checks": checks,
        "backup_record_count": len(records),
        "configuration_snapshot": export_configuration(settings),
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
    }


def validate_restore_readiness(settings: Settings) -> dict[str, Any]:
    """Validate that restore prerequisites are documented and consistent."""

    dr = verify_disaster_recovery(settings)
    config = export_configuration(settings)
    return {
        "status": dr["status"],
        "restore_validated": dr["status"] == "READY",
        "requires": [
            "database backup artifact referenced by metadata",
            "report archive path available",
            "configuration export available",
        ],
        "disaster_recovery": dr,
        "configuration": {
            "app_env": config["app_env"],
            "app_version": config["app_version"],
            "storage_backend": config["storage_backend"],
        },
        "policy_version": DEPLOYMENT_POLICY_VERSION,
        "engine_version": DEPLOYMENT_ENGINE_VERSION,
    }
