"""ORM and table consistency checks (read-only)."""

from __future__ import annotations

from typing import Any

from backend.app.infrastructure.database.base import Base
from backend.app.platform_validation.models import CheckOutcome, CheckStatus
from backend.app.platform_validation.policy import REQUIRED_TABLES


def _metadata_tables() -> set[str]:
    return set(Base.metadata.tables.keys())


def check_orm_consistency() -> CheckOutcome:
    """Ensure required platform validation tables exist in ORM metadata."""

    tables = _metadata_tables()
    required = REQUIRED_TABLES["orm_consistency"]
    missing = [name for name in required if name not in tables]
    details: dict[str, Any] = {
        "required": list(required),
        "missing": missing,
        "orm_table_count": len(tables),
    }
    if missing:
        return CheckOutcome(
            key="orm_consistency",
            category="orm",
            label="ORM consistency",
            status=CheckStatus.FAIL,
            message=f"Missing ORM tables: {', '.join(missing)}",
            details=details,
        )
    return CheckOutcome(
        key="orm_consistency",
        category="orm",
        label="ORM consistency",
        status=CheckStatus.PASS,
        message="Required ORM tables are registered.",
        details=details,
    )


def check_required_tables(key: str, *, label: str, category: str) -> CheckOutcome:
    """Verify module-specific tables are present in ORM metadata."""

    tables = _metadata_tables()
    required = REQUIRED_TABLES.get(key, ())
    missing = [name for name in required if name not in tables]
    details: dict[str, Any] = {
        "required": list(required),
        "missing": missing,
    }
    if missing:
        return CheckOutcome(
            key=key,
            category=category,
            label=label,
            status=CheckStatus.FAIL,
            message=f"Missing tables for {label}: {', '.join(missing)}",
            details=details,
        )
    return CheckOutcome(
        key=key,
        category=category,
        label=label,
        status=CheckStatus.PASS,
        message=f"{label} tables are present.",
        details=details,
    )
