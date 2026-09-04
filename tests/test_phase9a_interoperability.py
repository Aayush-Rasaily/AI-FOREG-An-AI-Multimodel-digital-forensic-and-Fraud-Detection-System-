"""Tests for Phase 9A digital evidence exchange and interoperability."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.interoperability.archive import build_deterministic_zip
from backend.app.interoperability.exporters import export_json_package
from backend.app.interoperability.hashing import (
    package_checksum_from_files,
    sha256_bytes,
)
from backend.app.interoperability.manifest import build_manifest, finalize_manifest
from backend.app.interoperability.models import InvestigationSnapshot
from backend.app.interoperability.policy import (
    INTEROP_ENGINE_VERSION,
    PACKAGE_SCHEMA_VERSION,
)
from backend.app.interoperability.validators import validate_package
from backend.app.main import create_app
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260907_0026_add_interoperability.py"
)


def _snapshot(*, case_id: str, case_number: str) -> InvestigationSnapshot:
    return InvestigationSnapshot(
        case={
            "id": case_id,
            "case_number": case_number,
            "title": "Interop Case",
            "description": None,
            "status": "OPEN",
            "priority": "MEDIUM",
            "created_by": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        evidence=[
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "case_id": case_id,
                "evidence_number": "E-1",
                "original_filename": "a.jpg",
                "stored_filename": "a.jpg",
                "mime_type": "image/jpeg",
                "file_size": 10,
                "sha256_hash": "abc",
                "storage_key": "evidence/x",
                "status": "STORED",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
        custody=[],
        extractions=[],
        ai_summaries=[],
        fusion_summaries=[],
        correlation_summaries=[],
        timeline=None,
        reports=[],
        workflow=None,
        security=None,
        policy_versions={"interop_policy": "1.0"},
        ai_engine_versions={},
    )


@pytest_asyncio.fixture
async def phase9a_client(
    tmp_path: Path,
) -> AsyncIterator[httpx.AsyncClient]:
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
        yield client
    await engine.dispose()


class TestMigration:
    def test_migration_chain(self) -> None:
        assert MIGRATION_PATH.is_file()
        spec = importlib.util.spec_from_file_location(
            "interop_migration", MIGRATION_PATH,
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260907_0026"
        assert module.down_revision == "20260906_0025"


class TestDeterministicPackage:
    def test_manifest_and_checksums(self) -> None:
        case_id = str(uuid4())
        snapshot = _snapshot(case_id=case_id, case_number="CASE-9A-1")
        files, manifest = export_json_package(
            snapshot, created_at="2026-01-01T00:00:00Z",
        )
        assert "manifest.json" in files
        assert manifest["schema_version"] == PACKAGE_SCHEMA_VERSION
        assert manifest["engine_version"] == INTEROP_ENGINE_VERSION
        assert manifest["evidence_count"] == 1
        paths = [item["path"] for item in manifest["files"]]
        assert paths == sorted(paths)
        checksums = {
            path: sha256_bytes(payload)
            for path, payload in files.items()
            if path != "manifest.json"
        }
        assert package_checksum_from_files(checksums) == manifest[
            "package_checksum"
        ]
        assert "manifest_checksum" in manifest
        assert manifest["provenance"]["package_checksum"] == manifest[
            "package_checksum"
        ]

    def test_archive_deterministic(self) -> None:
        files = {"b.txt": b"b", "a.txt": b"a"}
        first = build_deterministic_zip(files)
        second = build_deterministic_zip(files)
        assert first == second
        assert sha256_bytes(first) == sha256_bytes(second)

    def test_invalid_manifest_and_duplicates(self) -> None:
        case_id = str(uuid4())
        snapshot = _snapshot(case_id=case_id, case_number="CASE-DUP")
        files, _manifest = export_json_package(
            snapshot, created_at="2026-01-01T00:00:00Z",
        )
        result = validate_package(
            members=files,
            existing_case_numbers={"CASE-DUP"},
            existing_case_ids=set(),
        )
        assert result.valid is False
        assert result.integrity_status == "CONFLICTS"
        assert any(item.startswith("case_number:") for item in result.conflicts)

        broken = dict(files)
        broken.pop("manifest.json")
        invalid = validate_package(
            members=broken,
            existing_case_numbers=set(),
            existing_case_ids=set(),
        )
        assert invalid.integrity_status == "INVALID"

        tampered = dict(files)
        tampered["case.json"] = b'{"tampered":true}'
        bad_hash = validate_package(
            members=tampered,
            existing_case_numbers=set(),
            existing_case_ids=set(),
        )
        assert bad_hash.valid is False
        assert any(
            item.check == "hashes" and item.status == "FAIL"
            for item in bad_hash.findings
        )

    def test_build_manifest_ordering(self) -> None:
        manifest = build_manifest(
            created_at="2026-01-01T00:00:00Z",
            case_id="c1",
            case_number="N1",
            format_name="json_package",
            file_checksums={"z.json": "aa", "a.json": "bb"},
            evidence_count=0,
            report_count=0,
            timeline_count=0,
            policy_versions={"b": "1", "a": "1"},
            ai_engine_versions={},
            evidence_ids=[],
            report_versions=[],
            timeline_version=None,
        )
        finalized = finalize_manifest(manifest)
        assert [item["path"] for item in finalized["files"]] == [
            "a.json",
            "z.json",
        ]
        assert list(finalized["policy_versions"].keys()) == ["a", "b"]


class TestInteropApi:
    @pytest.mark.asyncio
    async def test_export_list_manifest_download(
        self, phase9a_client: httpx.AsyncClient,
    ) -> None:
        case = await create_case(phase9a_client)
        case_id = case["id"]

        export = await phase9a_client.post(
            f"/api/v1/cases/{case_id}/export",
            json={"format": "json_package", "include_binaries": False},
        )
        assert export.status_code == 200, export.text
        body = export.json()["data"]
        assert body["status"] == "COMPLETED"
        assert body["package_checksum"]
        assert body["manifest_checksum"]
        export_id = body["id"]

        listed = await phase9a_client.get(
            f"/api/v1/exports?case_id={case_id}",
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] >= 1

        detail = await phase9a_client.get(f"/api/v1/exports/{export_id}")
        assert detail.status_code == 200
        assert detail.json()["data"]["format"] == "json_package"

        manifest = await phase9a_client.get(
            f"/api/v1/exports/{export_id}/manifest",
        )
        assert manifest.status_code == 200
        data = manifest.json()["data"]
        assert data["manifest"]["schema_version"] == PACKAGE_SCHEMA_VERSION
        assert data["package_checksum"] == body["package_checksum"]

        download = await phase9a_client.get(
            f"/api/v1/exports/{export_id}/download",
        )
        assert download.status_code == 200
        assert download.headers["content-type"].startswith("application/zip")
        assert download.content[:2] == b"PK"

        csv_export = await phase9a_client.post(
            f"/api/v1/cases/{case_id}/export",
            json={"format": "csv"},
        )
        assert csv_export.status_code == 200
        assert csv_export.json()["data"]["status"] == "COMPLETED"

        bad = await phase9a_client.post(
            f"/api/v1/cases/{case_id}/export",
            json={"format": "not_a_format"},
        )
        assert bad.status_code == 400

    @pytest.mark.asyncio
    async def test_import_validation_and_conflicts(
        self, phase9a_client: httpx.AsyncClient,
    ) -> None:
        case = await create_case(phase9a_client)
        case_id = case["id"]
        case_number = case["case_number"]

        export = await phase9a_client.post(
            f"/api/v1/cases/{case_id}/export",
            json={"format": "manifest"},
        )
        assert export.status_code == 200
        export_id = export.json()["data"]["id"]
        package = await phase9a_client.get(
            f"/api/v1/exports/{export_id}/download",
        )
        assert package.status_code == 200

        # Importing a package for an existing case_number → CONFLICTS
        conflict = await phase9a_client.post(
            "/api/v1/cases/import",
            files={"file": ("pkg.zip", package.content, "application/zip")},
        )
        assert conflict.status_code == 200, conflict.text
        conflict_body = conflict.json()["data"]
        assert conflict_body["status"] == "CONFLICTS"
        assert conflict_body["integrity_status"] == "CONFLICTS"
        assert any(
            f"case_number:{case_number}" == item
            or item.startswith("case_id:")
            for item in conflict_body["conflicts"]
        )

        listed = await phase9a_client.get("/api/v1/imports")
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] >= 1

        detail = await phase9a_client.get(
            f"/api/v1/imports/{conflict_body['id']}",
        )
        assert detail.status_code == 200

        # Fresh package with unknown identifiers should validate
        fresh_id = str(uuid4())
        snapshot = _snapshot(case_id=fresh_id, case_number="CASE-FRESH-9A")
        files, _ = export_json_package(
            snapshot, created_at="2026-01-01T00:00:00Z",
        )
        archive = build_deterministic_zip(files)
        ok = await phase9a_client.post(
            "/api/v1/cases/import",
            files={"file": ("fresh.zip", archive, "application/zip")},
        )
        assert ok.status_code == 200, ok.text
        assert ok.json()["data"]["status"] == "COMPLETED"
        assert ok.json()["data"]["integrity_status"] in {"VALID", "DEGRADED"}
        assert ok.json()["data"]["target_case_id"] is None  # no auto-create
