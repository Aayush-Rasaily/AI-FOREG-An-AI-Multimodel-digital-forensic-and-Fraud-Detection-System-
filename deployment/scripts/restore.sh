#!/usr/bin/env bash
# Phase 10F restore helper — validates integrity then applies DB/report restore.
# Requires CONFIRM=YES for destructive steps.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

BUNDLE="${1:-}"
if [[ -z "$BUNDLE" ]]; then
  echo "Usage: $0 <backup-bundle-dir>" >&2
  exit 2
fi

ENV_FILE="${ENV_FILE:-.env.production}"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

export AI_FORGE_RESTORE_BUNDLE="$BUNDLE"
python - <<'PY'
import os
import sys
from pathlib import Path

from backend.app.recovery.restore import plan_restore, validate_restore_bundle

bundle = Path(os.environ["AI_FORGE_RESTORE_BUNDLE"])
validation = validate_restore_bundle(bundle)
print(f"[restore] status={validation['status']} allowed={validation['restore_allowed']}")
if not validation["restore_allowed"]:
    for check in validation["checks"]:
        if check["status"] == "FAIL":
            print(f"[restore] FAIL {check['check']}: {check['message']}")
    sys.exit(1)
plan = plan_restore(bundle)
for step in plan["steps"]:
    print(step)
PY

if [[ "${CONFIRM:-}" != "YES" ]]; then
  echo "[restore] Validation OK. Re-run with CONFIRM=YES to apply destructive restore."
  exit 0
fi

COMPOSE_FILE="deployment/compose/docker-compose.production.yml"
if [[ -f "${BUNDLE}/postgres.dump.sql" ]] && command -v docker >/dev/null 2>&1; then
  echo "[restore] applying postgres.dump.sql"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
    psql -U "${POSTGRES_USER:-ai_forge}" -d "${POSTGRES_DB:-ai_forge}" \
    <"${BUNDLE}/postgres.dump.sql"
fi

STORAGE_ROOT="${STORAGE_ROOT:-./data}"
if [[ -d "${BUNDLE}/reports" ]]; then
  mkdir -p "${STORAGE_ROOT}/reports"
  cp -a "${BUNDLE}/reports/." "${STORAGE_ROOT}/reports/"
  echo "[restore] reports restored"
fi
if [[ -d "${BUNDLE}/exports" ]]; then
  mkdir -p "${STORAGE_ROOT}/exports"
  cp -a "${BUNDLE}/exports/." "${STORAGE_ROOT}/exports/"
  echo "[restore] exports restored"
fi

echo "[restore] complete — run readiness/release-check before enabling traffic"
