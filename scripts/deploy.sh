#!/usr/bin/env bash
# Production deploy: build images, migrate, start stack, verify readiness.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file ${ENV_FILE}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing ${ENV_FILE}. Copy .env.production.example and set secrets." >&2
  exit 1
fi

export GIT_COMMIT="${GIT_COMMIT:-$(git rev-parse HEAD 2>/dev/null || true)}"
export BUILD_ID="${BUILD_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

echo "[deploy] Building production images (GIT_COMMIT=${GIT_COMMIT:-unknown})..."
$COMPOSE build

echo "[deploy] Running migrations then starting services..."
$COMPOSE up -d --remove-orphans

echo "[deploy] Waiting for API health..."
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${API_PORT:-8000}/api/v1/system/liveness" >/dev/null 2>&1; then
    echo "[deploy] Liveness OK."
    break
  fi
  sleep 2
done

echo "[deploy] Readiness probe:"
curl -fsS "http://127.0.0.1:${API_PORT:-8000}/api/v1/system/readiness" || true
echo
echo "[deploy] Complete. Review /system/readiness and Administration → Deployment Status."
