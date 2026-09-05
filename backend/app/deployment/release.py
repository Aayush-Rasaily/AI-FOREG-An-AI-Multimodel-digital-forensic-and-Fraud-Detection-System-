"""Release and build metadata constants."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

DEPLOYMENT_ENGINE_VERSION = "8g.1.0"
DEPLOYMENT_POLICY_VERSION = "1.0"

# Canonical schema / migration head expected for this release train.
EXPECTED_MIGRATION_HEAD = "20260914_0033"


def _git_commit(repo_root: Path | None = None) -> str | None:
    """Return the current git commit hash when available."""

    root = repo_root or Path.cwd()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    commit = completed.stdout.strip()
    return commit or None


def collect_policy_versions() -> dict[str, str]:
    """Collect known policy/engine versions from prior phases."""

    versions: dict[str, str] = {
        "deployment_policy": DEPLOYMENT_POLICY_VERSION,
        "deployment_engine": DEPLOYMENT_ENGINE_VERSION,
    }
    try:
        from backend.app.workflow.policy import WORKFLOW_POLICY_VERSION

        versions["workflow_policy"] = WORKFLOW_POLICY_VERSION
    except Exception:  # noqa: BLE001 — optional import for release info
        pass
    try:
        from backend.app.security.policy import SECURITY_POLICY_VERSION

        versions["security_policy"] = SECURITY_POLICY_VERSION
    except Exception:  # noqa: BLE001
        pass
    try:
        from backend.app.monitoring.policy import POLICY_VERSION as MON_POL

        versions["monitoring_policy"] = MON_POL
    except Exception:  # noqa: BLE001
        pass
    try:
        from backend.app.audit.policy import POLICY_VERSION as AUD_POL

        versions["audit_policy"] = AUD_POL
    except Exception:  # noqa: BLE001
        pass
    try:
        from backend.app.interoperability.policy import (
            INTEROP_ENGINE_VERSION,
            INTEROP_POLICY_VERSION,
        )

        versions["interop_policy"] = INTEROP_POLICY_VERSION
        versions["interop_engine"] = INTEROP_ENGINE_VERSION
    except Exception:  # noqa: BLE001
        pass
    try:
        from backend.app.knowledge_graph.policy import (
            KG_ENGINE_VERSION,
            KG_POLICY_VERSION,
        )

        versions["knowledge_graph_policy"] = KG_POLICY_VERSION
        versions["knowledge_graph_engine"] = KG_ENGINE_VERSION
    except Exception:  # noqa: BLE001
        pass
    return versions


def collect_ai_engine_versions(app_state: Any | None = None) -> dict[str, str]:
    """Return registered AI stack version markers when present."""

    versions: dict[str, str] = {}
    if app_state is None:
        return versions
    for key, label in (
        ("ai_stack", "ai"),
        ("image_ai_stack", "image_ai"),
        ("document_ai_stack", "document_ai"),
        ("video_ai_stack", "video_ai"),
        ("audio_ai_stack", "audio_ai"),
    ):
        stack = getattr(app_state, key, None)
        if not isinstance(stack, dict):
            continue
        settings = stack.get("settings")
        version = getattr(settings, "engine_version", None) or getattr(
            settings, "policy_version", None
        )
        if version is not None:
            versions[label] = str(version)
        else:
            versions[label] = "registered"
    return versions


def build_release_metadata(
    *,
    app_version: str,
    environment: str,
    app_state: Any | None = None,
    migration_version: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Assemble deterministic release metadata for API responses."""

    commit = os.environ.get("GIT_COMMIT") or _git_commit(repo_root)
    build_id = os.environ.get("BUILD_ID") or os.environ.get("CI_BUILD_ID")
    return {
        "application_version": app_version,
        "schema_version": migration_version or EXPECTED_MIGRATION_HEAD,
        "migration_version": migration_version or EXPECTED_MIGRATION_HEAD,
        "environment": environment,
        "policy_versions": collect_policy_versions(),
        "ai_engine_versions": collect_ai_engine_versions(app_state),
        "build_metadata": {
            "build_id": build_id,
            "deployment_engine": DEPLOYMENT_ENGINE_VERSION,
            "deployment_policy": DEPLOYMENT_POLICY_VERSION,
        },
        "git_commit": commit,
    }
