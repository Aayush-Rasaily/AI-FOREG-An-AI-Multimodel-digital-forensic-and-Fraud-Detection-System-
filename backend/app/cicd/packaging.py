"""Release packaging metadata (Phase 10G). No application behavior changes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.cicd.gates import parse_semver, read_project_version
from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD


def build_version_metadata(
    *,
    version: str | None = None,
    git_sha: str = "",
    image_namespace: str = "ghcr.io/example/ai-forge",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build SemVer + image tag metadata for release artifacts."""

    resolved = version or read_project_version(repo_root)
    parse_semver(resolved)
    sha = git_sha[:12] if git_sha else "unknown"
    api = f"{image_namespace}-api"
    web = f"{image_namespace}-frontend"
    return {
        "version": resolved,
        "git_sha": git_sha or sha,
        "schema_version": EXPECTED_MIGRATION_HEAD,
        "images": {
            "api": {
                "latest": f"{api}:latest",
                "semver": f"{api}:{resolved}",
                "sha": f"{api}:{sha}",
            },
            "frontend": {
                "latest": f"{web}:latest",
                "semver": f"{web}:{resolved}",
                "sha": f"{web}:{sha}",
            },
        },
        "tags": ["latest", resolved, sha],
    }


def write_version_metadata(path: Path, metadata: dict[str, Any]) -> Path:
    """Write version metadata JSON for CI artifacts."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return path
