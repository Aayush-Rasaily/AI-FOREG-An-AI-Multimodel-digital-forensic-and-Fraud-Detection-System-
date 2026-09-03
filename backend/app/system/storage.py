"""Storage utilization monitoring."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from backend.app.core.config import Settings


def _dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total


def collect_storage_stats(
    settings: Settings,
) -> dict[str, Any]:
    """Collect storage usage from configured backend."""
    root = settings.storage_root.resolve()
    used_bytes = _dir_size(root)
    disk_total: int | None = None
    disk_free: int | None = None
    disk_percent: float | None = None
    try:
        import shutil

        usage = shutil.disk_usage(root)
        disk_total = usage.total
        disk_free = usage.free
        disk_percent = round(
            (usage.used / usage.total) * 100, 2,
        ) if usage.total else None
    except OSError:
        pass
    return {
        "backend": settings.storage_backend,
        "root_configured": True,
        "used_bytes": used_bytes,
        "used_mb": round(used_bytes / (1024 * 1024), 2),
        "disk_total_bytes": disk_total,
        "disk_free_bytes": disk_free,
        "disk_percent": disk_percent,
        "max_upload_size_mb": settings.max_upload_size_mb,
    }
