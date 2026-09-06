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
    """Verify Phase 9H migration remains present and release head is current."""

    root = repo_root or Path(__file__).resolve().parents[2]
    versions = root / "alembic" / "versions"
    phase9h_file = versions / "20260914_0033_add_platform_validation.py"
    head_file = versions / "20260915_0034_add_performance_indexes.py"
    details: dict[str, Any] = {
        "expected_head": EXPECTED_MIGRATION_HEAD,
        "phase9h_path": phase9h_file.as_posix(),
        "head_path": head_file.as_posix(),
    }
    if not phase9h_file.is_file():
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Platform validation migration file is missing.",
            details=details,
        )
    if not head_file.is_file():
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Performance index migration file is missing.",
            details=details,
        )
    phase9h = _load_migration_module(phase9h_file)
    head = _load_migration_module(head_file)
    details.update(
        {
            "phase9h_revision": getattr(phase9h, "revision", None),
            "phase9h_down_revision": getattr(phase9h, "down_revision", None),
            "head_revision": getattr(head, "revision", None),
            "head_down_revision": getattr(head, "down_revision", None),
        }
    )
    if getattr(phase9h, "revision", None) != "20260914_0033":
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Platform validation migration revision is incorrect.",
            details=details,
        )
    if getattr(phase9h, "down_revision", None) != "20260913_0032":
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Platform validation down_revision chain is incorrect.",
            details=details,
        )
    if getattr(head, "revision", None) != EXPECTED_MIGRATION_HEAD:
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Migration revision does not match expected release head.",
            details=details,
        )
    if getattr(head, "down_revision", None) != "20260914_0033":
        return CheckOutcome(
            key="migrations",
            category="migrations",
            label="Database migrations",
            status=CheckStatus.FAIL,
            message="Performance migration down_revision chain is incorrect.",
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
