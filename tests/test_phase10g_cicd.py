"""Tests for Phase 10G CI/CD and release engineering."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from backend.app.cicd.gates import (
    RELEASE_ENGINE_VERSION,
    fail_on_critical_advisories,
    parse_semver,
    read_project_version,
    validate_alembic_heads,
    validate_openapi_schema,
)
from backend.app.cicd.packaging import build_version_metadata, write_version_metadata
from backend.app.cicd.release_notes import generate_changelog_section, prepend_changelog
from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


class TestSemVer:
    def test_parse_and_project_version(self) -> None:
        parsed = parse_semver("1.2.3-rc.1+build.9")
        assert parsed["major"] == "1"
        assert parsed["minor"] == "2"
        assert parsed["patch"] == "3"
        assert parsed["pre"] == "rc.1"
        version = read_project_version(REPO_ROOT)
        parse_semver(version)
        with pytest.raises(ValueError):
            parse_semver("1.2")


class TestGates:
    def test_alembic_head_matches_release(self) -> None:
        result = validate_alembic_heads(repo_root=REPO_ROOT)
        assert result["status"] == "PASSED"
        assert result["heads"] == [EXPECTED_MIGRATION_HEAD]

    def test_openapi_requires_paths(self) -> None:
        ok = validate_openapi_schema(
            {
                "openapi": "3.1.0",
                "info": {"title": "AI_Forge"},
                "paths": {"/health": {"get": {}}},
            }
        )
        assert ok["status"] == "PASSED"
        bad = validate_openapi_schema({"openapi": "2.0", "info": {}})
        assert bad["status"] == "FAILED"

    def test_critical_advisories_fail_gate(self) -> None:
        passed = fail_on_critical_advisories({"dependencies": []})
        assert passed["status"] == "PASSED"
        failed = fail_on_critical_advisories(
            {
                "dependencies": [
                    {
                        "name": "example",
                        "vulns": [{"id": "CVE-0000", "severity": "CRITICAL"}],
                    }
                ]
            }
        )
        assert failed["status"] == "FAILED"
        assert failed["count"] == 1


class TestPackagingAndNotes:
    def test_version_metadata_and_changelog(self, tmp_path: Path) -> None:
        metadata = build_version_metadata(
            version="0.1.0",
            git_sha="abcdef1234567890",
            image_namespace="ghcr.io/example/ai-forge",
            repo_root=REPO_ROOT,
        )
        assert metadata["schema_version"] == EXPECTED_MIGRATION_HEAD
        assert metadata["images"]["api"]["latest"].endswith(":latest")
        assert metadata["images"]["api"]["semver"].endswith(":0.1.0")
        assert metadata["images"]["api"]["sha"].endswith(":abcdef123456")
        path = write_version_metadata(tmp_path / "version.json", metadata)
        assert path.is_file()

        section = generate_changelog_section(
            "0.2.0",
            ["feat: add CI", "fix: ruff", "docs: notes"],
            released_at=datetime(2026, 9, 7, tzinfo=UTC),
        )
        assert "## 0.2.0" in section
        assert "### Features" in section
        merged = prepend_changelog("# Changelog\n\n## 0.1.0\n", section)
        assert merged.startswith("# Changelog")
        assert merged.index("0.2.0") < merged.index("0.1.0")
        assert RELEASE_ENGINE_VERSION.startswith("10g")


class TestArtifacts:
    def test_github_workflows_and_templates_exist(self) -> None:
        for name in (
            "ci.yml",
            "backend.yml",
            "frontend.yml",
            "security.yml",
            "release.yml",
            "docker.yml",
        ):
            path = WORKFLOWS / name
            assert path.is_file(), path
            docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            assert docs and docs[0]["name"]

        ci = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
        jobs = ci["jobs"]
        assert "backend" in jobs
        assert "frontend" in jobs
        assert "security" in jobs
        assert "docker" in jobs
        assert jobs["quality-gate"]["needs"] == [
            "backend",
            "frontend",
            "docs",
            "security",
            "docker",
        ]

        assert (REPO_ROOT / ".github" / "dependabot.yml").is_file()
        assert (WORKFLOWS / "docs.yml").is_file()
        assert (REPO_ROOT / ".github" / "CODEOWNERS").is_file()
        assert (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").is_file()
        assert (REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug.yml").is_file()
        assert (REPO_ROOT / "docs" / "release-engineering.md").is_file()
        assert (REPO_ROOT / "CHANGELOG.md").is_file()
        docker = yaml.safe_load((WORKFLOWS / "docker.yml").read_text(encoding="utf-8"))
        build_step = docker["jobs"]["images"]["steps"]
        files = [
            step.get("with", {}).get("file")
            for step in build_step
            if isinstance(step, dict)
        ]
        assert "deployment/docker/backend.Dockerfile" in files
        assert "deployment/docker/frontend.Dockerfile" in files
        assert "deployment/docker/worker.Dockerfile" in files
