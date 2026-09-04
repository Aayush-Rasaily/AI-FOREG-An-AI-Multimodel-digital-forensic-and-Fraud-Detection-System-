#!/usr/bin/env bash
# Apply Alembic migrations to head. Idempotent and safe to re-run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-.env.production}"
if [[ -f "$ENV_FILE" ]]; then
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
