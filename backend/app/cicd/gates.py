"""Quality-gate helpers for CI (Phase 10G). No forensic/AI logic."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD

RELEASE_ENGINE_VERSION = "10g.1.0"
SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+(?P<build>[0-9A-Za-z.-]+))?$"
)


def parse_semver(version: str) -> dict[str, str | None]:
    """Parse a Semantic Versioning 2.0 string."""

    match = SEMVER_RE.fullmatch(version.strip())
    if match is None:
        raise ValueError(f"Invalid SemVer: {version}")
    return match.groupdict()


def read_project_version(repo_root: Path | None = None) -> str:
    """Return the version declared in pyproject.toml."""

    root = repo_root or Path(__file__).resolve().parents[3]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("version"):
            _, _, raw = line.partition("=")
            version = raw.strip().strip('"').strip("'")
            parse_semver(version)
            return version
    raise ValueError("pyproject.toml does not declare version.")


def validate_alembic_heads(
    *,
    repo_root: Path | None = None,
    expected: str | None = None,
) -> dict[str, Any]:
    """Fail if Alembic does not have a single expected head."""

    root = repo_root or Path(__file__).resolve().parents[3]
    want = expected or EXPECTED_MIGRATION_HEAD
    completed = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "heads"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout or "").strip()
    heads = [
        line.split()[0]
        for line in output.splitlines()
        if line.strip() and not line.startswith("FAILED")
    ]
    ok = completed.returncode == 0 and heads == [want]
    return {
        "status": "PASSED" if ok else "FAILED",
        "expected": want,
        "heads": heads,
        "exit_code": completed.returncode,
        "stderr": (completed.stderr or "")[-2000:],
    }


def validate_openapi_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Validate a generated OpenAPI document without starting a server."""

    checks: list[dict[str, str]] = []
    version = str(schema.get("openapi", ""))
    if version.startswith("3."):
        checks.append(
            {"check": "openapi_version", "status": "PASS", "message": version}
        )
    else:
        checks.append(
            {
                "check": "openapi_version",
                "status": "FAIL",
                "message": f"Expected OpenAPI 3.x, got {version!r}",
            }
        )
    paths = schema.get("paths")
    if isinstance(paths, dict) and paths:
        checks.append(
            {
                "check": "paths_present",
                "status": "PASS",
                "message": f"{len(paths)} paths",
            }
        )
    else:
        checks.append(
            {
                "check": "paths_present",
                "status": "FAIL",
                "message": "OpenAPI paths are missing.",
            }
        )
    info_raw = schema.get("info")
    info: dict[str, Any] = info_raw if isinstance(info_raw, dict) else {}
    title = str(info.get("title", ""))
    if title:
        checks.append({"check": "info_title", "status": "PASS", "message": title})
    else:
        checks.append(
            {
                "check": "info_title",
                "status": "FAIL",
                "message": "info.title is required.",
            }
        )
    failed = [item for item in checks if item["status"] == "FAIL"]
    return {
        "status": "PASSED" if not failed else "FAILED",
        "checks": checks,
        "path_count": len(paths) if isinstance(paths, dict) else 0,
    }


def _advisory_severity(item: dict[str, Any]) -> str:
    raw = item.get("severity")
    if isinstance(raw, str) and raw.strip():
        return raw.strip().upper()
    database = item.get("database_specific")
    if isinstance(database, dict):
        nested = database.get("severity")
        if isinstance(nested, str) and nested.strip():
            return nested.strip().upper()
    return ""


def _collect_vuln_dicts(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    top = payload.get("vulnerabilities")
    if isinstance(top, list):
        for item in top:
            if isinstance(item, dict):
                ident = str(item.get("id") or item.get("name") or "unknown")
                found.append((ident, item))
    deps = payload.get("dependencies")
    if isinstance(deps, list):
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            name = str(dep.get("name") or "unknown")
            vulns = dep.get("vulns") or dep.get("vulnerabilities") or []
            if isinstance(vulns, list) and vulns:
                for vuln in vulns:
                    if isinstance(vuln, dict):
                        found.append((name, vuln))
            elif _advisory_severity(dep) or dep.get("id"):
                found.append((name, dep))
    return found


def fail_on_critical_advisories(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail when pip-audit / OSV-style findings include critical severity."""

    critical: list[str] = []
    for name, item in _collect_vuln_dicts(payload):
        severity = _advisory_severity(item)
        blob = json.dumps(item.get("aliases") or []).upper()
        if severity == "CRITICAL" or "CRITICAL" in blob:
            ident = str(item.get("id") or name)
            critical.append(ident)
    return {
        "status": "FAILED" if critical else "PASSED",
        "critical": critical,
        "count": len(critical),
    }


def validate_declared_versions(repo_root: Path | None = None) -> dict[str, Any]:
    """Require pyproject.toml, VERSION, and frontend package.json to match."""

    root = repo_root or Path(__file__).resolve().parents[3]
    pyproject = read_project_version(root)
    file_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    package = json.loads(
        (root / "frontend" / "package.json").read_text(encoding="utf-8")
    )
    npm_version = str(package.get("version", ""))
    ok = pyproject == file_version == npm_version
    return {
        "status": "PASSED" if ok else "FAILED",
        "pyproject": pyproject,
        "VERSION": file_version,
        "frontend": npm_version,
    }


def extract_changelog_section(changelog: str, version: str) -> str:
    """Return the markdown section for one SemVer heading from CHANGELOG.md."""

    marker = f"## {version}"
    lines = changelog.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith(marker):
            start = index
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    section = "\n".join(lines[start:end]).strip()
    return f"{section}\n" if section else ""
