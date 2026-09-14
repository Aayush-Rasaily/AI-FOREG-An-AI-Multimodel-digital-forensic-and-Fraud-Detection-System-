#!/usr/bin/env bash
# Apply Alembic migrations to head. Idempotent and safe to re-run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer local .env for native development; fall back to production env file.
if [[ -n "${ENV_FILE:-}" ]]; then
  :
elif [[ -f .env ]]; then
  ENV_FILE=".env"
elif [[ -f .env.production ]]; then
  ENV_FILE=".env.production"
else
  ENV_FILE=""
fi

if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
  echo "[migrate] Loading $ENV_FILE"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

echo "[migrate] Upgrading database to Alembic head..."
uv run --no-dev alembic -c backend/alembic.ini upgrade head
echo "[migrate] Current revision:"
uv run --no-dev alembic -c backend/alembic.ini current
echo "[migrate] Done."
