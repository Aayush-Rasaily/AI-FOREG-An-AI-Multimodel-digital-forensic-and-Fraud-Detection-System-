#!/usr/bin/env bash
# Stop the Phase 10A production stack (graceful).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="deployment/compose/docker-compose.production.yml"

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans

echo "Production stack stopped."
