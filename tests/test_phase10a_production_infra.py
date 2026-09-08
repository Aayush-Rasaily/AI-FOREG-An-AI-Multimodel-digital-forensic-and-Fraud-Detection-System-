"""Tests for Phase 10A production infrastructure and environment validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.app.core.config import (
    DevelopmentSettings,
    ProductionSettings,
    Settings,
    TestingSettings,
    settings_class_for_env,
)
from backend.app.core.environment import (
    cleanup_temporary_files,
    detect_missing_secrets,
    production_safety_checks,
    validate_environment,
    verify_storage_layout,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT = REPO_ROOT / "deployment"


class TestInfrastructureArtifacts:
    def test_required_paths_exist(self) -> None:
        required = [
            DEPLOYMENT / "docker" / "backend.Dockerfile",
            DEPLOYMENT / "docker" / "frontend.Dockerfile",
            DEPLOYMENT / "docker" / "worker.Dockerfile",
            DEPLOYMENT / "compose" / "docker-compose.production.yml",
            DEPLOYMENT / "compose" / "docker-compose.monitoring.yml",
            DEPLOYMENT / "k8s" / "namespace.yaml",
            DEPLOYMENT / "k8s" / "backend-deployment.yaml",
            DEPLOYMENT / "k8s" / "backend-service.yaml",
            DEPLOYMENT / "k8s" / "frontend-deployment.yaml",
            DEPLOYMENT / "k8s" / "frontend-service.yaml",
            DEPLOYMENT / "k8s" / "postgres.yaml",
            DEPLOYMENT / "k8s" / "redis.yaml",
            DEPLOYMENT / "k8s" / "ingress.yaml",
            DEPLOYMENT / "nginx" / "nginx.conf",
            DEPLOYMENT / "nginx" / "frontend.conf",
            DEPLOYMENT / "scripts" / "production_start.sh",
            DEPLOYMENT / "scripts" / "production_stop.sh",
            DEPLOYMENT / "scripts" / "migrate.sh",
            DEPLOYMENT / "scripts" / "backup.sh",
            REPO_ROOT / "docs" / "deployment.md",
            REPO_ROOT / ".env.production.example",
            REPO_ROOT / "frontend" / ".env.production",
            REPO_ROOT / "frontend" / ".env.development",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        assert missing == []

    def test_dockerfiles_are_multi_stage(self) -> None:
        backend = (DEPLOYMENT / "docker" / "backend.Dockerfile").read_text(
            encoding="utf-8"
        )
        frontend = (DEPLOYMENT / "docker" / "frontend.Dockerfile").read_text(
            encoding="utf-8"
        )
        assert "AS builder" in backend or "AS build" in backend
        assert "AS runtime" in backend
        assert "AS build" in frontend
        assert "AS runtime" in frontend
        assert "system/liveness" in backend
        assert "nginx" in frontend.lower()

        path = DEPLOYMENT / "compose" / "docker-compose.production.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "services" in data
        for name in ("api", "migrate", "worker", "frontend", "postgres", "redis"):
            assert name in data["services"]
        assert (
            data["services"]["api"]["build"]["dockerfile"]
            == "deployment/docker/backend.Dockerfile"
        )

    def test_k8s_manifests_parse(self) -> None:
        for name in (
            "namespace.yaml",
            "backend-deployment.yaml",
            "ingress.yaml",
            "postgres.yaml",
            "redis.yaml",
        ):
            docs = list(
                yaml.safe_load_all(
                    (DEPLOYMENT / "k8s" / name).read_text(encoding="utf-8")
                )
            )
            assert docs
            assert all(doc is not None for doc in docs)


class TestSettingsProfiles:
    def test_profile_classes(self) -> None:
        assert settings_class_for_env("development") is DevelopmentSettings
        assert settings_class_for_env("test") is TestingSettings
        assert settings_class_for_env("production") is ProductionSettings
        assert settings_class_for_env("local") is Settings

    def test_testing_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        settings = TestingSettings(
            storage_root=tmp_path / "storage",
            temp_storage_path=tmp_path / "tmp",
            ai_model_root=tmp_path / "models",
        )
        assert settings.app_env == "test"
        assert settings.debug is True
        assert "sqlite" in settings.database_url

    def test_production_defaults_hardended(self) -> None:
        settings = ProductionSettings(
            jwt_secret="not-a-placeholder-value-abc123",
            database_url="postgresql+psycopg://u:p@db:5432/ai_forge",
            redis_url="redis://redis:6379/0",
        )
        assert settings.app_env == "production"
        assert settings.debug is False


class TestEnvironmentValidation:
    def test_validate_environment_local(self, tmp_path: Path) -> None:
        settings = Settings(
            app_env="local",
            storage_root=tmp_path / "data",
            temp_storage_path=tmp_path / "data" / "tmp",
            ai_model_root=tmp_path / "models",
        )
        report = validate_environment(settings)
        assert report["status"] == "PASSED"
        assert report["fail_count"] == 0

    def test_production_safety_fails_with_debug(
        self,
        tmp_path: Path,
    ) -> None:
        settings = Settings(
            app_env="production",
            debug=True,
            jwt_secret=None,
            storage_root=tmp_path / "data",
            temp_storage_path=tmp_path / "tmp",
            ai_model_root=tmp_path / "models",
        )
        findings = production_safety_checks(settings)
        assert any(
            item["check"] == "production_debug" and item["status"] == "FAIL"
            for item in findings
        )

    def test_missing_jwt_detected(self) -> None:
        settings = Settings(app_env="production", jwt_secret=None, debug=False)
        findings = detect_missing_secrets(settings)
        assert any(
            item["check"] == "secret_jwt_secret" and item["status"] == "FAIL"
            for item in findings
        )

    def test_storage_layout_and_cleanup(self, tmp_path: Path) -> None:
        settings = Settings(
            app_env="local",
            storage_root=tmp_path / "data",
            temp_storage_path=tmp_path / "tmp",
            ai_model_root=tmp_path / "models",
        )
        findings = verify_storage_layout(settings)
        assert all(item["status"] == "PASS" for item in findings)
        assert (tmp_path / "data").is_dir()
        cleanup = cleanup_temporary_files(settings)
        assert cleanup["removed"] >= 0


class TestEnvironmentModuleImport:
    def test_environment_module_exports(self) -> None:
        from backend.app.core import environment as env

        assert callable(env.validate_environment)
        assert callable(env.verify_startup_dependencies)
        assert callable(env.cleanup_temporary_files)
