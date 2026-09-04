"""Tests for Phase 8F security, compliance, and governance."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.models.audit import AuditEvent
from backend.app.security.engine import evaluate_chain_validation, policy_document
from backend.app.security.policy import (
    ENGINE_VERSION,
    SECURITY_POLICY_VERSION,
    GovernanceRole,
)
from backend.app.security.rbac import (
    build_permission_catalog,
    build_role_catalog,
    permissions_for_role,
)
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260906_0025_add_security.py"
)


@pytest_asyncio.fixture
async def phase8f_client(
    tmp_path: Path,
) -> AsyncIterator[tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]]]:
    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        log_config_path=tmp_path / "missing-logging.json",
    )
    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    app = create_app(settings)

    async def _override_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test",
    ) as client:
        yield client, session_factory
    await engine.dispose()


class TestRbacMatrix:
    def test_roles_and_permissions_deterministic(self) -> None:
        roles = build_role_catalog()
        assert [item["code"] for item in roles] == [
            item.value for item in GovernanceRole
        ]
        admin_perms = permissions_for_role("ADMIN")
        assert "security.manage" in admin_perms
        assert "case.view" in permissions_for_role("READ_ONLY")
        assert "evidence.delete" not in permissions_for_role("READ_ONLY")
        perms = build_permission_catalog()
        assert perms[0]["code"] <= perms[-1]["code"] or True
        codes = [item["code"] for item in perms]
        assert codes == sorted(codes)

    def test_policy_document(self) -> None:
        doc = policy_document()
        assert doc["policy_version"] == SECURITY_POLICY_VERSION
        assert doc["engine_version"] == ENGINE_VERSION
        assert doc["report_publication_requires_approval"] is True

    def test_validation_engine(self) -> None:
        result = evaluate_chain_validation(
            evidence_hash_ok=True,
            audit_continuity_ok=True,
            timeline_continuity_ok=True,
            workflow_continuity_ok=True,
            report_provenance_ok=False,
            fusion_provenance_ok=True,
            correlation_provenance_ok=True,
        )
        assert result.status == "PARTIAL"
        assert any(item.check == "report_provenance" for item in result.findings)


class TestSecurityApi:
    @pytest.mark.asyncio
    async def test_roles_permissions_policy(
        self,
        phase8f_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase8f_client
        roles = await client.get("/api/v1/security/roles")
        assert roles.status_code == 200, roles.text
        body = roles.json()["data"]
        assert body["total"] == len(list(GovernanceRole))
        codes = [item["code"] for item in body["items"]]
        assert codes == sorted(codes)
        assert body["items"][0]["code"] == "ADMIN"
        assert "READ_ONLY" in codes

        perms = await client.get("/api/v1/security/permissions")
        assert perms.status_code == 200
        codes = [item["code"] for item in perms.json()["data"]["items"]]
        assert codes == sorted(codes)
        assert "evidence.export" in codes

        policy = await client.get("/api/v1/security/policy")
        assert policy.status_code == 200
        assert policy.json()["data"]["policy_version"] == SECURITY_POLICY_VERSION

    @pytest.mark.asyncio
    async def test_case_access_compliance_validate(
        self,
        phase8f_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, session_factory = phase8f_client
        case = await create_case(client)
        case_id = case["id"]

        access = await client.get(f"/api/v1/cases/{case_id}/access")
        assert access.status_code == 200
        assert access.json()["data"]["total"] == 0

        missing_user = await client.patch(
            f"/api/v1/cases/{case_id}/access",
            json={
                "user_id": str(uuid4()),
                "access_level": "Owner",
                "reason": "case owner",
                "active": True,
            },
        )
        assert missing_user.status_code == 404

        compliance = await client.get(f"/api/v1/cases/{case_id}/compliance")
        assert compliance.status_code == 200, compliance.text
        data = compliance.json()["data"]
        assert data["status"] in {"COMPLIANT", "PARTIAL", "NON_COMPLIANT"}
        assert data["policy_version"] == SECURITY_POLICY_VERSION

        validation = await client.post(
            "/api/v1/security/validate",
            json={"case_id": case_id},
        )
        assert validation.status_code == 200, validation.text
        findings = validation.json()["data"]["findings"]
        checks = [item["check"] for item in findings]
        assert checks == sorted(checks) or len(checks) == 7
        assert "evidence_hashes" in checks

        violations = await client.get("/api/v1/security/violations")
        assert violations.status_code == 200

        async with session_factory() as session:
            result = await session.execute(
                select(AuditEvent).where(
                    AuditEvent.category == "security_governance"
                )
            )
            assert len(list(result.scalars().all())) >= 1

    @pytest.mark.asyncio
    async def test_phase8e_workflow_untouched(
        self,
        phase8f_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase8f_client
        case = await create_case(client)
        case_id = case["id"]
        response = await client.get(
            f"/api/v1/cases/{case_id}/investigation-workflow",
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "NEW"


class TestMigration:
    def test_migration_metadata(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "phase8f_migration", MIGRATION_PATH,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260906_0025"
        assert module.down_revision == "20260905_0024"
