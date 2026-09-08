"""RC6 production operations checks (no application feature changes)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestProductionImagesAndCompose:
    def test_worker_dockerfile_is_non_root_celery(self) -> None:
        text = (REPO_ROOT / "deployment" / "docker" / "worker.Dockerfile").read_text(
            encoding="utf-8"
        )
        assert "USER appuser" in text
        assert "celery" in text
        assert "DEBUG=false" in text
        assert "AS builder" in text
        assert "AS runtime" in text

    def test_production_compose_has_required_services(self) -> None:
        path = REPO_ROOT / "deployment" / "compose" / "docker-compose.production.yml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        services = data["services"]
        for name in (
            "api",
            "migrate",
            "worker",
            "frontend",
            "nginx",
            "postgres",
            "redis",
            "rabbitmq",
        ):
            assert name in services
        assert (
            services["worker"]["build"]["dockerfile"]
            == "deployment/docker/worker.Dockerfile"
        )
        volumes = data["volumes"]
        for volume in (
            "postgres-data",
            "redis-data",
            "rabbitmq-data",
            "evidence-data",
        ):
            assert volume in volumes

    def test_tls_redirect_and_rate_limit(self) -> None:
        tls = (REPO_ROOT / "deployment" / "nginx" / "nginx-tls.conf.example").read_text(
            encoding="utf-8"
        )
        assert "return 301 https://$host$request_uri" in tls
        assert "limit_req_zone" in tls
        assert "ssl_protocols       TLSv1.2 TLSv1.3" in tls

    def test_production_env_template_is_hardened(self) -> None:
        env = (REPO_ROOT / ".env.production.example").read_text(encoding="utf-8")
        assert "APP_ENV=production" in env
        assert "DEBUG=false" in env
        assert "APP_VERSION=1.0.0" in env
        assert "JWT_SECRET=" in env

    def test_readiness_doc_exists(self) -> None:
        assert (REPO_ROOT / "docs" / "production-readiness.md").is_file()
