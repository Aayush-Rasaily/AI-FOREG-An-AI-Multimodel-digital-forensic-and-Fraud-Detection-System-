"""RC7 release-candidate certification artifacts (no product changes)."""

from __future__ import annotations

from pathlib import Path

from backend.app.cicd.gates import validate_declared_versions

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestReleaseCandidateArtifacts:
    def test_version_is_1_0_0(self) -> None:
        result = validate_declared_versions(REPO_ROOT)
        assert result["status"] == "PASSED"
        assert result["pyproject"] == "1.0.0"

    def test_public_release_files_exist(self) -> None:
        for relative in (
            "LICENSE",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "ROADMAP.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "RELEASE_NOTES.md",
            "docs/rc7-certification.md",
            "docs/uat-checklist.md",
            "docs/support.md",
            "docs/github-release-v1.0.0.md",
            "samples/README.md",
            "samples/SHA256SUMS",
            "samples/evidence/sample-invoice.pdf",
        ):
            path = REPO_ROOT / relative
            assert path.is_file(), relative

    def test_gitignore_keeps_production_env_example(self) -> None:
        text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "!.env.production.example" in text
