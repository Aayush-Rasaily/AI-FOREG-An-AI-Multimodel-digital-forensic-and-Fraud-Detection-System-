"""Orchestrates individual platform validation checks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from backend.app.core.config import Settings
from backend.app.deployment.configuration import verify_configuration
from backend.app.platform_validation.api_checker import (
    check_api_compatibility,
    check_openapi_generation,
)
from backend.app.platform_validation.compatibility import (
    check_module_imports,
    collect_compatibility,
)
from backend.app.platform_validation.consistency import (
    check_orm_consistency,
    check_required_tables,
)
from backend.app.platform_validation.migration_checker import check_migrations
from backend.app.platform_validation.models import CheckOutcome, CheckStatus
from backend.app.platform_validation.policy import CHECK_CATALOG, REQUIRED_TABLES


def check_configuration(settings: Settings) -> CheckOutcome:
    """Validate configuration findings without mutating environment."""

    findings = verify_configuration(settings)
    statuses = {str(item.get("status", "FAIL")).upper() for item in findings}
    if "FAIL" in statuses:
        status = CheckStatus.FAIL
        message = "Configuration has failing checks."
    elif "WARN" in statuses:
        status = CheckStatus.WARN
        message = "Configuration has warnings."
    else:
        status = CheckStatus.PASS
        message = "Configuration checks passed."
    return CheckOutcome(
        key="configuration",
        category="platform",
        label="Configuration",
        status=status,
        message=message,
        details={"findings": findings},
    )


def check_storage_accessibility(settings: Settings) -> CheckOutcome:
    """Check storage root accessibility without write probes."""

    root = Path(settings.storage_root)
    details: dict[str, Any] = {
        "storage_root": root.as_posix(),
        "exists": root.exists(),
        "is_dir": root.is_dir() if root.exists() else False,
        "readable": False,
        "mutated": False,
    }
    if not root.exists():
        return CheckOutcome(
            key="storage_accessibility",
            category="platform",
            label="Storage accessibility",
            status=CheckStatus.WARN,
            message="Storage root does not exist yet (read-only check).",
            details=details,
        )
    if not root.is_dir():
        return CheckOutcome(
            key="storage_accessibility",
            category="platform",
            label="Storage accessibility",
            status=CheckStatus.FAIL,
            message="Storage root is not a directory.",
            details=details,
        )
    readable = os.access(root, os.R_OK)
    details["readable"] = readable
    if not readable:
        return CheckOutcome(
            key="storage_accessibility",
            category="platform",
            label="Storage accessibility",
            status=CheckStatus.FAIL,
            message="Storage root is not readable.",
            details=details,
        )
    return CheckOutcome(
        key="storage_accessibility",
        category="platform",
        label="Storage accessibility",
        status=CheckStatus.PASS,
        message="Storage root is accessible (read-only).",
        details=details,
    )


def run_all_checks(
    *,
    settings: Settings,
    app: FastAPI,
) -> list[CheckOutcome]:
    """Execute the full deterministic check catalog in fixed order."""

    by_key: dict[str, CheckOutcome] = {}
    by_key["migrations"] = check_migrations()
    by_key["orm_consistency"] = check_orm_consistency()
    by_key["api_compatibility"] = check_api_compatibility(
        app,
        api_prefix=settings.api_v1_prefix,
    )
    by_key["openapi_generation"] = check_openapi_generation(app)

    # Module imports establish AI/timeline/etc. presence without re-running AI.
    for outcome in check_module_imports():
        by_key[outcome.key] = outcome

    # Overlay table-presence checks for modules that declare REQUIRED_TABLES.
    catalog_meta = {item["key"]: item for item in CHECK_CATALOG}
    for key, tables in REQUIRED_TABLES.items():
        if key == "orm_consistency" or not tables:
            continue
        meta = catalog_meta.get(key)
        if meta is None:
            continue
        table_outcome = check_required_tables(
            key,
            label=meta["label"],
            category=meta["category"],
        )
        import_outcome = by_key.get(key)
        if import_outcome and import_outcome.status == CheckStatus.FAIL:
            continue
        if table_outcome.status == CheckStatus.FAIL:
            by_key[key] = table_outcome
        elif import_outcome is None:
            by_key[key] = table_outcome
        else:
            details = dict(import_outcome.details)
            details["tables"] = table_outcome.details
            by_key[key] = CheckOutcome(
                key=key,
                category=import_outcome.category,
                label=import_outcome.label,
                status=CheckStatus.PASS,
                message=f"{import_outcome.label} module and tables verified.",
                details=details,
            )

    by_key["configuration"] = check_configuration(settings)
    by_key["storage_accessibility"] = check_storage_accessibility(settings)

    ordered: list[CheckOutcome] = []
    for item in CHECK_CATALOG:
        maybe_outcome = by_key.get(item["key"])
        if maybe_outcome is None:
            ordered.append(
                CheckOutcome(
                    key=item["key"],
                    category=item["category"],
                    label=item["label"],
                    status=CheckStatus.FAIL,
                    message="Check was not executed.",
                    details={},
                )
            )
        else:
            ordered.append(maybe_outcome)
    return ordered


def compatibility_panel() -> dict[str, Any]:
    return collect_compatibility()
