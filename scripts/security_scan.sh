#!/usr/bin/env bash
# Phase 10D dependency security scan.
# Runs pip-audit + npm audit and writes reports under reports/security/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p reports/security

echo "[security_scan] repository: $ROOT"

STATUS=0

if command -v python >/dev/null 2>&1; then
  python - <<'PY' || STATUS=$?
from pathlib import Path
from backend.app.security.dependency_scan import run_dependency_security_scan

result = run_dependency_security_scan(repo_root=Path(".").resolve())
print(f"[security_scan] status={result['status']}")
for name, check in result["checks"].items():
    print(f"[security_scan] {name}: {check['status']}")
for key, path in result.get("report_paths", {}).items():
    print(f"[security_scan] report[{key}]={path}")
if result["status"] == "FAILED" and not result.get("note"):
    raise SystemExit(1)
PY
else
  echo "[security_scan] python not found" >&2
  STATUS=1
fi

# Direct scanner invocations for operator visibility (best-effort).
if command -v pip-audit >/dev/null 2>&1; then
  echo "[security_scan] running pip-audit..."
  pip-audit -r requirements.txt --progress-spinner off \
    | tee "reports/security/pip-audit-latest.txt" \
    || true
else
  echo "[security_scan] pip-audit not installed (optional)"
fi

if command -v npm >/dev/null 2>&1; then
  echo "[security_scan] running npm audit..."
  (cd frontend && npm audit --omit=dev) \
    | tee "reports/security/npm-audit-latest.txt" \
    || true
else
  echo "[security_scan] npm not installed (optional)"
fi

echo "[security_scan] complete"
exit "$STATUS"
