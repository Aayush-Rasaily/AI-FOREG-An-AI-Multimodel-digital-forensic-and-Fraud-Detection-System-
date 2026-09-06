#!/usr/bin/env bash
# Create a local backup metadata marker + optional postgres dump.
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
  source "$ENV_FILE"
  set +a
fi

META="${DEST}/backup-metadata.json"
cat >"$META" <<EOF
{
  "created_at": "${STAMP}",
  "app_env": "${APP_ENV:-production}",
  "app_version": "${APP_VERSION:-unknown}",
  "git_commit": "${GIT_COMMIT:-unknown}",
  "database_url_present": $([ -n "${DATABASE_URL:-}" ] && echo true || echo false),
  "notes": "Phase 10A local backup marker. Restore requires a DB dump artifact."
}
EOF

if command -v docker >/dev/null 2>&1; then
  COMPOSE_FILE="deployment/compose/docker-compose.production.yml"
  if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --status running 2>/dev/null | grep -q postgres; then
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres \
      pg_dump -U "${POSTGRES_USER:-ai_forge}" "${POSTGRES_DB:-ai_forge}" \
      >"${DEST}/postgres.dump.sql" || true
  fi
fi

echo "Backup written to ${DEST}"
