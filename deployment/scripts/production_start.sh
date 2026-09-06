#!/usr/bin/env bash
# Start the Phase 10A production stack.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="deployment/compose/docker-compose.production.yml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy .env.production.example and set secrets." >&2
  exit 1
fi

export GIT_COMMIT="${GIT_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}"
export BUILD_ID="${BUILD_ID:-local-$(date +%Y%m%d%H%M%S)}"

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build "$@"

echo "Waiting for API liveness..."
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${API_PORT:-8000}/api/v1/system/liveness" >/dev/null 2>&1; then
    echo "API is live."
    exit 0
  fi
  sleep 2
done

echo "API liveness check timed out." >&2
exit 1
