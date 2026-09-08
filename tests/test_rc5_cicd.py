"""RC5 CI/CD automation checks (no application feature changes)."""

from __future__ import annotations

from pathlib import Path

import yaml

from backend.app.cicd.gates import (
    extract_changelog_section,
    validate_declared_versions,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestVersionAndChangelog:
    def test_declared_versions_match(self) -> None:
        result = validate_declared_versions(REPO_ROOT)
        assert result["status"] == "PASSED"

    def test_extract_changelog_section(self) -> None:
        text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        section = extract_changelog_section(text, "1.0.0")
        assert section.startswith("## 1.0.0")
        assert "RC5" in section
        assert extract_changelog_section(text, "9.9.9") == ""


class TestWorkflows:
    def test_dependabot_and_docs_workflow(self) -> None:
        dependabot = yaml.safe_load(
            (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        )
        ecosystems = {item["package-ecosystem"] for item in dependabot["updates"]}
        assert {"pip", "npm", "github-actions", "docker"} <= ecosystems

        docs = yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "docs.yml").read_text(
                encoding="utf-8"
            )
        )
        assert docs["name"] == "Documentation"

    def test_backend_has_alembic_roundtrip(self) -> None:
        text = (REPO_ROOT / ".github" / "workflows" / "backend.yml").read_text(
            encoding="utf-8"
        )
        assert "downgrade -1" in text
        assert "postgres:16-alpine" in text
        assert "uv lock --check" in text

    def test_frontend_typecheck_and_bundle(self) -> None:
        text = (REPO_ROOT / ".github" / "workflows" / "frontend.yml").read_text(
            encoding="utf-8"
        )
        assert "npm run lint" in text
        assert "Bundle verification" in text

    def test_secret_scan_and_gitleaks_config(self) -> None:
        security = (REPO_ROOT / ".github" / "workflows" / "security.yml").read_text(
            encoding="utf-8"
        )
        assert "gitleaks detect" in security
        assert (REPO_ROOT / ".gitleaks.toml").is_file()
