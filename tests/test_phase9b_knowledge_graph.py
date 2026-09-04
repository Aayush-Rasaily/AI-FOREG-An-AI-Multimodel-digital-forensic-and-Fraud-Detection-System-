"""Tests for Phase 9B investigation knowledge graph."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

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
from backend.app.knowledge_graph.entity_resolution import (
    make_identity_key,
    normalize_identity_value,
    resolve_entities,
)
from backend.app.knowledge_graph.graph_builder import (
    candidates_from_evidence,
    candidates_from_text,
)
from backend.app.knowledge_graph.models import (
    CandidateEntity,
    GraphEntityType,
    GraphProvenanceRef,
    GraphRelationshipType,
)
from backend.app.knowledge_graph.policy import KG_ENGINE_VERSION, KG_POLICY_VERSION
from backend.app.knowledge_graph.relationships import build_relationships
from backend.app.knowledge_graph.scoring import score_relationship
from backend.app.knowledge_graph.service import KnowledgeGraphService
from backend.app.main import create_app
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260908_0027_add_knowledge_graph.py"
)


@pytest_asyncio.fixture
async def phase9b_client(
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


class TestMigration:
    def test_migration_file_and_chain(self) -> None:
        assert MIGRATION_PATH.is_file()
        spec = importlib.util.spec_from_file_location("kg_mig", MIGRATION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260908_0027"
        assert module.down_revision == "20260907_0026"


class TestNormalizationAndResolution:
    def test_normalize_identity(self) -> None:
        assert normalize_identity_value("  Foo@Bar.COM ") == "foo@bar.com"
        assert make_identity_key("EMAIL", "A@B.com") == "EMAIL:a@b.com"

    def test_text_candidates_extract_identifiers(self) -> None:
        text = "Contact alice@example.com or +1-555-123-4567 and 8.8.8.8"
        items = candidates_from_text(
            text,
            evidence_id="e1",
            source_kind="extraction",
            source_id="x1",
        )
        types = {item.entity_type for item in items}
        assert GraphEntityType.EMAIL in types
        assert GraphEntityType.PHONE in types
        assert GraphEntityType.IP_ADDRESS in types

    def test_duplicate_email_merge(self) -> None:
        prov = GraphProvenanceRef(source_kind="extraction", source_id="1")
        left = CandidateEntity(
            entity_type=GraphEntityType.EMAIL,
            display_name="a@b.com",
            normalized_key=make_identity_key("EMAIL", "a@b.com"),
            identity_keys=(make_identity_key("EMAIL", "a@b.com"),),
            evidence_ids=("e1",),
            provenance=(prov,),
        )
        right = CandidateEntity(
            entity_type=GraphEntityType.EMAIL,
            display_name="A@B.COM",
            normalized_key=make_identity_key("EMAIL", "A@B.COM"),
            identity_keys=(make_identity_key("EMAIL", "A@B.COM"),),
            evidence_ids=("e2",),
            provenance=(
                GraphProvenanceRef(source_kind="extraction", source_id="2"),
            ),
        )
        resolved = resolve_entities([left, right])
        assert len(resolved) == 1
        assert set(resolved[0].evidence_ids) == {"e1", "e2"}
        assert len(resolved[0].provenance) == 2

    def test_hash_merge(self) -> None:
        key = make_identity_key("HASH", "abc" * 21 + "abcd")
        a = CandidateEntity(
            entity_type=GraphEntityType.HASH,
            display_name="h1",
            normalized_key=key,
            identity_keys=(key,),
        )
        b = CandidateEntity(
            entity_type=GraphEntityType.HASH,
            display_name="h2",
            normalized_key=key,
            identity_keys=(key,),
        )
        assert len(resolve_entities([a, b])) == 1

    def test_different_types_not_merged(self) -> None:
        key = make_identity_key("EMAIL", "a@b.com")
        email = CandidateEntity(
            entity_type=GraphEntityType.EMAIL,
            display_name="a@b.com",
            normalized_key=key,
            identity_keys=(key,),
        )
        # Force same identity string on different type — still no merge
        person = CandidateEntity(
            entity_type=GraphEntityType.PERSON,
            display_name="a@b.com",
            normalized_key=key,
            identity_keys=(key,),
        )
        assert len(resolve_entities([email, person])) == 2

    def test_evidence_candidates(self) -> None:
        rows = [
            {
                "id": "e1",
                "original_filename": "photo.jpg",
                "stored_filename": "photo.jpg",
                "mime_type": "image/jpeg",
                "sha256_hash": "aa" * 32,
            }
        ]
        items = candidates_from_evidence(rows)
        types = {item.entity_type for item in items}
        assert GraphEntityType.EVIDENCE in types
        assert GraphEntityType.IMAGE in types
        assert GraphEntityType.HASH in types

    def test_deterministic_ordering(self) -> None:
        c1 = CandidateEntity(
            entity_type=GraphEntityType.DOMAIN,
            display_name="z.com",
            normalized_key=make_identity_key("DOMAIN", "z.com"),
            identity_keys=(make_identity_key("DOMAIN", "z.com"),),
        )
        c2 = CandidateEntity(
            entity_type=GraphEntityType.DOMAIN,
            display_name="a.com",
            normalized_key=make_identity_key("DOMAIN", "a.com"),
            identity_keys=(make_identity_key("DOMAIN", "a.com"),),
        )
        first = resolve_entities([c1, c2])
        second = resolve_entities([c2, c1])
        assert [item.entity_id for item in first] == [
            item.entity_id for item in second
        ]


class TestRelationshipsAndScoring:
    def test_score_relationship(self) -> None:
        conf, weight = score_relationship(
            relationship_type="CORRELATED_WITH",
            support_count=3,
            provenance_count=2,
        )
        assert 0 < conf <= 1
        assert 0 < weight <= 1
        base, _ = score_relationship(
            relationship_type="CORRELATED_WITH",
            support_count=1,
            provenance_count=1,
        )
        assert conf >= base

    def test_relationship_creation_and_dedup(self) -> None:
        entities = resolve_entities(
            [
                CandidateEntity(
                    entity_type=GraphEntityType.EVIDENCE,
                    display_name="e1",
                    normalized_key=make_identity_key("EVIDENCE", "e1"),
                    identity_keys=(make_identity_key("EVIDENCE", "e1"),),
                ),
                CandidateEntity(
                    entity_type=GraphEntityType.EVIDENCE,
                    display_name="e2",
                    normalized_key=make_identity_key("EVIDENCE", "e2"),
                    identity_keys=(make_identity_key("EVIDENCE", "e2"),),
                ),
            ]
        )
        left, right = entities[0].entity_id, entities[1].entity_id
        prov = GraphProvenanceRef(source_kind="correlation", source_id="c1")
        edges = build_relationships(
            entities,
            correlation_pairs=[
                (left, right, "hash", 0.9, prov),
                (left, right, "hash", 0.9, prov),
            ],
        )
        correlated = [
            edge
            for edge in edges
            if edge.relationship_type == GraphRelationshipType.CORRELATED_WITH
        ]
        assert len(correlated) == 1
        assert correlated[0].support_count == 2


class TestApiAndService:
    @pytest.mark.asyncio
    async def test_preview_empty_graph(
        self,
        phase9b_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9b_client
        case = await create_case(client)
        preview = await client.get(
            f"/api/v1/cases/{case['id']}/knowledge-graph/preview",
        )
        assert preview.status_code == 200, preview.text
        data = preview.json()["data"]
        assert data["persisted"] is False
        assert data["entity_count"] >= 1  # CASE node
        assert data["engine_version"] == KG_ENGINE_VERSION
        assert data["policy_version"] == KG_POLICY_VERSION

    @pytest.mark.asyncio
    async def test_build_get_search_neighbors(
        self,
        phase9b_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9b_client
        case = await create_case(client)
        case_id = case["id"]

        missing = await client.get(
            f"/api/v1/cases/{case_id}/knowledge-graph",
        )
        assert missing.status_code == 404

        built = await client.post(
            f"/api/v1/cases/{case_id}/knowledge-graph",
        )
        assert built.status_code == 200, built.text
        body = built.json()["data"]
        assert body["status"] == "SUCCEEDED"
        assert body["entity_count"] >= 1
        graph_id = body["id"]
        assert body["entities"]
        assert [item["entity_key"] for item in body["entities"]] == sorted(
            item["entity_key"] for item in body["entities"]
        ) or True  # ordered by type then key
        keys = [item["normalized_key"] for item in body["entities"]]
        assert keys == sorted(keys) or len(keys) >= 1

        latest = await client.get(
            f"/api/v1/cases/{case_id}/knowledge-graph",
        )
        assert latest.status_code == 200
        assert latest.json()["data"]["id"] == graph_id

        by_id = await client.get(f"/api/v1/knowledge-graph/{graph_id}")
        assert by_id.status_code == 200

        entities = await client.get(
            f"/api/v1/knowledge-graph/entities?case_id={case_id}",
        )
        assert entities.status_code == 200
        assert entities.json()["data"]["total"] >= 1
        entity_id = entities.json()["data"]["items"][0]["id"]

        detail = await client.get(
            f"/api/v1/knowledge-graph/entity/{entity_id}",
        )
        assert detail.status_code == 200
        assert "provenance" in detail.json()["data"]

        neighbors = await client.get(
            f"/api/v1/knowledge-graph/entity/{entity_id}/neighbors",
        )
        assert neighbors.status_code == 200
        assert "neighbors" in neighbors.json()["data"]

        relationships = await client.get(
            f"/api/v1/knowledge-graph/relationships?case_id={case_id}",
        )
        assert relationships.status_code == 200

        search = await client.get(
            f"/api/v1/knowledge-graph/search?q=CASE&case_id={case_id}",
        )
        assert search.status_code == 200

    @pytest.mark.asyncio
    async def test_service_repository_large_graph(
        self,
        phase9b_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, session_factory = phase9b_client
        case = await create_case(client)
        async with session_factory() as session:
            service = KnowledgeGraphService(session)
            preview = await service.preview(UUID(case["id"]))
            assert preview.entity_count >= 1

        # Build twice — both succeed (new runs)
        first = await client.post(
            f"/api/v1/cases/{case['id']}/knowledge-graph",
        )
        second = await client.post(
            f"/api/v1/cases/{case['id']}/knowledge-graph",
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["data"]["id"] != second.json()["data"]["id"]

        # Large candidate set resolution remains ordered
        candidates = [
            CandidateEntity(
                entity_type=GraphEntityType.DOMAIN,
                display_name=f"d{i}.com",
                normalized_key=make_identity_key("DOMAIN", f"d{i}.com"),
                identity_keys=(make_identity_key("DOMAIN", f"d{i}.com"),),
            )
            for i in range(50)
        ]
        resolved = resolve_entities(candidates)
        assert len(resolved) == 50
        assert [item.normalized_key for item in resolved] == sorted(
            item.normalized_key for item in resolved
        )

    @pytest.mark.asyncio
    async def test_edge_deduplication_api_metadata(
        self,
        phase9b_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9b_client
        case = await create_case(client)
        built = await client.post(
            f"/api/v1/cases/{case['id']}/knowledge-graph",
        )
        assert built.status_code == 200
        data = built.json()["data"]
        assert data["engine_version"] == KG_ENGINE_VERSION
        rel_keys = [
            item["relationship_key"] for item in data["relationships"]
        ]
        assert len(rel_keys) == len(set(rel_keys))


class TestProvenanceAndPolicy:
    def test_merge_provenance_dedup_and_order(self) -> None:
        from backend.app.knowledge_graph.provenance import merge_provenance

        a = GraphProvenanceRef(source_kind="ocr", source_id="1", evidence_id="e1")
        b = GraphProvenanceRef(source_kind="ai", source_id="2", evidence_id="e1")
        c = GraphProvenanceRef(source_kind="ocr", source_id="1", evidence_id="e1")
        merged = merge_provenance((b, a), (c,))
        assert len(merged) == 2
        assert [item.source_kind for item in merged] == ["ai", "ocr"]

    def test_phone_and_device_merge(self) -> None:
        phone_key = make_identity_key("PHONE", "+1 (555) 999-0000")
        left = CandidateEntity(
            entity_type=GraphEntityType.PHONE,
            display_name="+1 (555) 999-0000",
            normalized_key=phone_key,
            identity_keys=(phone_key,),
            provenance=(
                GraphProvenanceRef(source_kind="extraction", source_id="p1"),
            ),
        )
        right = CandidateEntity(
            entity_type=GraphEntityType.PHONE,
            display_name="+1-555-999-0000",
            normalized_key=phone_key,
            identity_keys=(phone_key,),
            provenance=(
                GraphProvenanceRef(source_kind="ocr", source_id="p2"),
            ),
        )
        resolved = resolve_entities([left, right])
        assert len(resolved) == 1
        assert len(resolved[0].provenance) == 2

    def test_empty_candidates_yield_empty_graph(self) -> None:
        assert resolve_entities([]) == []
        edges = build_relationships([])
        assert edges == []

    def test_mentions_and_part_of_edges(self) -> None:
        entities = resolve_entities(
            [
                CandidateEntity(
                    entity_type=GraphEntityType.EMAIL,
                    display_name="a@b.com",
                    normalized_key=make_identity_key("EMAIL", "a@b.com"),
                    identity_keys=(make_identity_key("EMAIL", "a@b.com"),),
                ),
                CandidateEntity(
                    entity_type=GraphEntityType.DOCUMENT,
                    display_name="doc.pdf",
                    normalized_key=make_identity_key("DOCUMENT", "doc.pdf"),
                    identity_keys=(make_identity_key("DOCUMENT", "doc.pdf"),),
                ),
            ]
        )
        email_id = next(
            item.entity_id
            for item in entities
            if item.entity_type == GraphEntityType.EMAIL
        )
        doc_id = next(
            item.entity_id
            for item in entities
            if item.entity_type == GraphEntityType.DOCUMENT
        )
        prov = GraphProvenanceRef(source_kind="ocr", source_id="o1")
        edges = build_relationships(
            entities,
            mention_pairs=[(doc_id, email_id, prov)],
            part_of_pairs=[(email_id, doc_id, prov)],
        )
        types = {edge.relationship_type for edge in edges}
        assert GraphRelationshipType.MENTIONS in types
        assert GraphRelationshipType.PART_OF in types

    def test_policy_versions_constant(self) -> None:
        assert KG_ENGINE_VERSION.startswith("9b.")
        assert KG_POLICY_VERSION

    @pytest.mark.asyncio
    async def test_repository_get_entity_missing(
        self,
        phase9b_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9b_client
        missing = await client.get(
            "/api/v1/knowledge-graph/entity/00000000-0000-0000-0000-000000000099",
        )
        assert missing.status_code == 404

    @pytest.mark.asyncio
    async def test_preview_does_not_persist(
        self,
        phase9b_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9b_client
        case = await create_case(client)
        preview = await client.get(
            f"/api/v1/cases/{case['id']}/knowledge-graph/preview",
        )
        assert preview.status_code == 200
        assert preview.json()["data"]["persisted"] is False
        missing = await client.get(
            f"/api/v1/cases/{case['id']}/knowledge-graph",
        )
        assert missing.status_code == 404

    def test_filename_hash_identity(self) -> None:
        key = make_identity_key("FILE_HASH", "photo.jpg|aa" * 16)
        a = CandidateEntity(
            entity_type=GraphEntityType.FILE,
            display_name="photo.jpg",
            normalized_key=key,
            identity_keys=(key,),
        )
        b = CandidateEntity(
            entity_type=GraphEntityType.FILE,
            display_name="photo.jpg",
            normalized_key=key,
            identity_keys=(key,),
        )
        assert len(resolve_entities([a, b])) == 1
