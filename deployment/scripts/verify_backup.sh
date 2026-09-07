#!/usr/bin/env bash
# Phase 10F backup integrity verification.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

BUNDLE="${1:-}"
if [[ -z "$BUNDLE" ]]; then
  echo "Usage: $0 <backup-bundle-dir>" >&2
  exit 2
fi

export AI_FORGE_VERIFY_BUNDLE="$BUNDLE"
python - <<'PY'
import os
import sys
from pathlib import Path

from backend.app.recovery.verification import verify_backup_bundle

result = verify_backup_bundle(Path(os.environ["AI_FORGE_VERIFY_BUNDLE"]))
print(f"[verify] status={result['status']} valid={result['valid']}")
print(f"[verify] stamp={result.get('stamp')} schema={result.get('schema_version')}")
for check in result["checks"]:
    if check["status"] != "PASS":
        print(f"[verify] {check['status']} {check['check']}: {check['message']}")
if not result["valid"]:
    sys.exit(1)
PY
