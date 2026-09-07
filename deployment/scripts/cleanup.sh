#!/usr/bin/env bash
# Phase 10F retention cleanup for backups/reports/temp/logs/exports/ai cache.
# Defaults to dry-run. Set APPLY=YES to delete.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

DRY_RUN=1
if [[ "${APPLY:-}" == "YES" ]]; then
  DRY_RUN=0
fi

export AI_FORGE_CLEANUP_DRY_RUN="$DRY_RUN"
python - <<'PY'
import os

from backend.app.core.config import get_settings
from backend.app.recovery.retention import enforce_retention

dry_run = os.environ.get("AI_FORGE_CLEANUP_DRY_RUN", "1") != "0"
result = enforce_retention(get_settings(), dry_run=dry_run)
print(f"[cleanup] dry_run={result['dry_run']}")
print(f"[cleanup] removed={len(result['removed'])} skipped={len(result['skipped'])}")
for path in result["removed"][:50]:
    print(f"[cleanup] {path}")
for policy in result["policies"]:
    print(
        f"[cleanup] policy {policy['target']} retain_days={policy['retain_days']}"
    )
PY

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[cleanup] Dry-run only. Re-run with APPLY=YES to delete expired artifacts."
fi
