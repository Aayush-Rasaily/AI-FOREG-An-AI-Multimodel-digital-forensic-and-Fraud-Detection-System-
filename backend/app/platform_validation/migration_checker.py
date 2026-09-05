"""Migration chain checks for platform validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD
from backend.app.platform_validation.models import CheckOutcome, CheckStatus


def _load_migration_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_migrations(*, repo_root: Path | None = None) -> CheckOutcome:
    """Verify Phase 9H migration file and revision chain tip."""

    root = repo_root or Path(__file__).resolve().parents[2]
    versions = root / "alembic" / "versions"
    expected_file = versions / "20260914_0033_add_platform_validation.py"
    details: dict[str, Any] = {
        "expected_head": EXPECTED_MIGRATION_HEAD,
        "migration_path": expected_file.as_posix(),
    }
    if not expected_file.is_file():
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Platform validation migration file is missing.",
            details=details,
        )
    module = _load_migration_module(expected_file)
    revision = getattr(module, "revision", None)
    down_revision = getattr(module, "down_revision", None)
    details.update(
        {
            "revision": revision,
            "down_revision": down_revision,
        }
    )
    if revision != EXPECTED_MIGRATION_HEAD:
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message=("Migration revision does not match expected release head."),
            details=details,
        )
    if down_revision != "20260913_0032":
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Migration down_revision chain is incorrect.",
            details=details,
        )
    return CheckOutcome(
        key="migrations",
        category="migrations",
        label="Database migrations",
        status=CheckStatus.PASS,
        message="Migration chain tip matches expected release head.",
        details=details,
    )
