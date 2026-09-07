#!/usr/bin/env bash
# Phase 10F enterprise backup: PostgreSQL dump, optional Redis snapshot,
# configuration/report/export capture via Python recovery.backup.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.production}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="${BACKUP_ROOT:-./data/deployment/backups}"
DEST="${BACKUP_ROOT}/${STAMP}"
mkdir -p "$DEST"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  # shellcheck disable=SC1091
  source "$ENV_FILE"
  set +a
fi

DB_DUMP=""
REDIS_DUMP=""
COMPOSE_FILE="deployment/compose/docker-compose.production.yml"

if command -v docker >/dev/null 2>&1; then
  if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --status running 2>/dev/null | grep -q postgres; then
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
      pg_dump -U "${POSTGRES_USER:-ai_forge}" "${POSTGRES_DB:-ai_forge}" \
      >"${DEST}/postgres.dump.sql"; then
      DB_DUMP="${DEST}/postgres.dump.sql"
      echo "[backup] postgres dump written"
    else
      echo "[backup] postgres dump skipped/failed" >&2
      rm -f "${DEST}/postgres.dump.sql"
    fi
  fi

  if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --status running 2>/dev/null | grep -q redis; then
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis \
      redis-cli BGSAVE >/dev/null 2>&1; then
      sleep 2
      if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" cp \
        "redis:/data/dump.rdb" "${DEST}/redis.rdb" 2>/dev/null; then
        REDIS_DUMP="${DEST}/redis.rdb"
        echo "[backup] redis snapshot copied"
      fi
    fi
  fi
fi

export AI_FORGE_BACKUP_STAMP="$STAMP"
export AI_FORGE_BACKUP_DB_DUMP="${DB_DUMP}"
export AI_FORGE_BACKUP_REDIS_DUMP="${REDIS_DUMP}"

python - <<'PY'
import os
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.recovery.backup import create_backup_bundle

settings = get_settings()
stamp = os.environ.get("AI_FORGE_BACKUP_STAMP")
db = os.environ.get("AI_FORGE_BACKUP_DB_DUMP") or ""
rd = os.environ.get("AI_FORGE_BACKUP_REDIS_DUMP") or ""
manifest = create_backup_bundle(
    settings,
    stamp=stamp,
    database_dump_path=Path(db) if db else None,
    redis_dump_path=Path(rd) if rd else None,
)
print(f"[backup] bundle={manifest['bundle_dir']}")
print(f"[backup] manifest_sha256={manifest['manifest_sha256']}")
print(f"[backup] files={len(manifest['files'])}")
PY

echo "Backup written to ${DEST}"
