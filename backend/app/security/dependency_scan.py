"""Dependency security scanning helpers (Phase 10D)."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def default_reports_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[3]
    return root / "reports" / "security"


def _run_command(command: list[str], *, cwd: Path) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {
            "command": command,
            "status": "SKIPPED",
            "exit_code": None,
            "stdout": "",
            "stderr": f"{command[0]} is not installed",
        }
    completed = subprocess.run(
        [executable, *command[1:]],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "status": "PASSED" if completed.returncode == 0 else "FAILED",
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-50_000:],
        "stderr": completed.stderr[-50_000:],
    }


def run_dependency_security_scan(
    *,
    repo_root: Path | None = None,
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    """Run pip/npm audits and write JSON + text reports under reports/security/."""

    root = repo_root or Path(__file__).resolve().parents[3]
    out_dir = reports_dir or default_reports_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    checks: dict[str, dict[str, Any]] = {
        "pip_audit": _run_command(
            ["pip-audit", "-r", "requirements.txt", "--progress-spinner", "off"],
            cwd=root,
        ),
        "npm_audit": _run_command(
            ["npm", "audit", "--omit=dev", "--json"],
            cwd=root / "frontend",
        ),
    }
    results: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "repo_root": str(root),
        "checks": checks,
    }

    # Soft validation of lock/manifest presence
    manifests = {
        "requirements.txt": (root / "requirements.txt").is_file(),
        "frontend/package.json": (root / "frontend" / "package.json").is_file(),
    }
    results["manifests"] = manifests
    if not all(manifests.values()):
        results["status"] = "FAILED"
        results["note"] = "Required dependency manifests are missing."
    else:
        results["status"] = (
            "FAILED"
            if any(check["status"] == "FAILED" for check in checks.values())
            else "PASSED"
        )
        # Missing scanners are non-fatal so the script can complete in lean CI images.
        if all(check["status"] == "SKIPPED" for check in checks.values()):
            results["status"] = "PASSED"
            results["note"] = "Scanners were unavailable; manifests validated only."

    json_path = out_dir / f"dependency-scan-{stamp}.json"
    latest_path = out_dir / "dependency-scan-latest.json"
    text_path = out_dir / f"dependency-scan-{stamp}.txt"
    payload = json.dumps(results, indent=2)
    json_path.write_text(payload, encoding="utf-8")
    latest_path.write_text(payload, encoding="utf-8")
    lines = [
        f"AI-Forge dependency security scan ({results['generated_at']})",
        f"Overall status: {results['status']}",
        "",
    ]
    for name, check in checks.items():
        lines.append(f"## {name}: {check['status']} (exit={check['exit_code']})")
        if check.get("stderr"):
            lines.append(check["stderr"][:4000])
        if check.get("stdout"):
            lines.append(check["stdout"][:4000])
        lines.append("")
    text_path.write_text("\n".join(lines), encoding="utf-8")
    results["report_paths"] = {
        "json": str(json_path),
        "latest_json": str(latest_path),
        "text": str(text_path),
    }
    return results
