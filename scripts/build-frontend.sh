#!/usr/bin/env bash
# Static asset production build for the AI-Forge frontend.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/frontend"

echo "[build-frontend] Installing dependencies..."
npm ci

echo "[build-frontend] Building static assets..."
node ./scripts/build.mjs

echo "[build-frontend] Output: frontend/dist"
