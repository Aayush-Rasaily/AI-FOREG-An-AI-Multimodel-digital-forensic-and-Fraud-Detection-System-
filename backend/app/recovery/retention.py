"""Retention policies for backups and operational artifacts (Phase 10F)."""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from backend.app.core.config import Settings, get_settings
from backend.app.recovery.backup import MANIFEST_NAME, backup_root

RetentionTarget = Literal[
    "backups",
    "reports",
    "temporary_files",
    "logs",
    "exports",
    "ai_cache",
]


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    target: RetentionTarget
    retain_days: int
    enabled: bool = True


DEFAULT_POLICIES: tuple[RetentionPolicy, ...] = (
    RetentionPolicy("backups", retain_days=30),
    RetentionPolicy("reports", retain_days=90),
    RetentionPolicy("temporary_files", retain_days=1),
    RetentionPolicy("logs", retain_days=14),
    RetentionPolicy("exports", retain_days=60),
    RetentionPolicy("ai_cache", retain_days=7),
)


def policies_from_settings(settings: Settings | None = None) -> list[RetentionPolicy]:
    """Build retention policies from settings with safe defaults."""

    runtime = settings or get_settings()
    return [
        RetentionPolicy(
            "backups",
            retain_days=int(getattr(runtime, "backup_retain_days", 30)),
        ),
        RetentionPolicy(
            "reports",
            retain_days=int(getattr(runtime, "report_retain_days", 90)),
        ),
        RetentionPolicy(
            "temporary_files",
            retain_days=int(getattr(runtime, "temp_retain_days", 1)),
        ),
        RetentionPolicy(
            "logs",
            retain_days=int(getattr(runtime, "log_retain_days", 14)),
        ),
        RetentionPolicy(
            "exports",
            retain_days=int(getattr(runtime, "export_retain_days", 60)),
        ),
        RetentionPolicy(
            "ai_cache",
            retain_days=int(getattr(runtime, "ai_cache_retain_days", 7)),
        ),
    ]


def _is_older_than(path: Path, retain_days: int, *, now: float) -> bool:
    age_seconds = now - path.stat().st_mtime
    return age_seconds > retain_days * 86400


def enforce_retention(
    settings: Settings | None = None,
    *,
    dry_run: bool = True,
    now: float | None = None,
) -> dict[str, Any]:
    """Delete expired operational artifacts according to retention policies.

    Defaults to dry-run. Never deletes evidence originals under evidence/.
    """

    runtime = settings or get_settings()
    clock = now if now is not None else time.time()
    removed: list[str] = []
    skipped: list[str] = []

    for policy in policies_from_settings(runtime):
        if not policy.enabled:
            continue
        targets: list[Path] = []
        if policy.target == "backups":
            root = backup_root(runtime)
            targets = [
                path
                for path in root.iterdir()
                if path.is_dir() and (path / MANIFEST_NAME).exists()
            ]
        elif policy.target == "reports":
            root = Path(runtime.storage_root) / "reports"
            targets = list(root.glob("*")) if root.exists() else []
        elif policy.target == "temporary_files":
            root = Path(runtime.temp_storage_path)
            targets = list(root.glob("*")) if root.exists() else []
        elif policy.target == "logs":
            root = Path(runtime.storage_root) / "logs"
            targets = list(root.glob("*")) if root.exists() else []
        elif policy.target == "exports":
            root = Path(runtime.storage_root) / "exports"
            targets = list(root.glob("*")) if root.exists() else []
        elif policy.target == "ai_cache":
            root = Path(runtime.ai_model_root) / "cache"
            targets = list(root.glob("*")) if root.exists() else []

        for path in targets:
            # Never touch evidence originals.
            if "evidence" in path.parts:
                skipped.append(path.as_posix())
                continue
            try:
                if not path.exists():
                    continue
                if not _is_older_than(path, policy.retain_days, now=clock):
                    continue
            except OSError:
                skipped.append(path.as_posix())
                continue
            if dry_run:
                removed.append(f"DRY_RUN:{path.as_posix()}")
                continue
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink(missing_ok=True)
                removed.append(path.as_posix())
            except OSError:
                skipped.append(path.as_posix())

    return {
        "dry_run": dry_run,
        "removed": sorted(removed),
        "skipped": sorted(skipped),
        "policies": [
            {
                "target": policy.target,
                "retain_days": policy.retain_days,
                "enabled": policy.enabled,
            }
            for policy in policies_from_settings(runtime)
        ],
    }
