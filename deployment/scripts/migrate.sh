#!/usr/bin/env bash
# Run Alembic migrations against the production database URL.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="deployment/compose/docker-compose.production.yml"

if [[ -f "$ENV_FILE" ]] && command -v docker >/dev/null 2>&1; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm migrate
else
  # Host-side fallback when compose is unavailable.
  # shellcheck disable=SC1090
  set -a
  [[ -f "$ENV_FILE" ]] && source "$ENV_FILE"
  set +a
  uv run --no-dev alembic -c backend/alembic.ini upgrade head
fi

echo "Migrations applied."
