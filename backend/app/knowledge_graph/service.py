"""Application service for investigation knowledge graphs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.knowledge_graph.engine import KnowledgeGraphEngine
from backend.app.knowledge_graph.exceptions import (
    EntityNotFoundError,
    GraphNotFoundError,
)
from backend.app.knowledge_graph.models import GraphRunStatus
from backend.app.knowledge_graph.policy import KG_ENGINE_VERSION, KG_POLICY_VERSION
from backend.app.knowledge_graph.provenance import provenance_to_dict
from backend.app.knowledge_graph.repository import KnowledgeGraphRepository
from backend.app.knowledge_graph.schemas import (
    GraphEntityListResponse,
    GraphEntityResponse,
    GraphPreviewResponse,
    GraphRelationshipListResponse,
    GraphRelationshipResponse,
    KnowledgeGraphResponse,
    NeighborResponse,
    ProvenanceItem,
)
from backend.app.models.knowledge_graph import (
    GraphEntity,
    GraphEntityAlias,
    GraphProvenance,
    GraphRelationship,
    KnowledgeGraphRun,
)


class KnowledgeGraphService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = KnowledgeGraphRepository(session)
        self.engine = KnowledgeGraphEngine(session)

    def _entity_response(
        self,
        row: GraphEntity,
        *,
        aliases: list[str] | None = None,
        provenance: list[ProvenanceItem] | None = None,
    ) -> GraphEntityResponse:
        return GraphEntityResponse(
            id=row.id,
            graph_id=row.graph_id,
            case_id=row.case_id,
            entity_key=row.entity_key,
            entity_type=row.entity_type,
            display_name=row.display_name,
            normalized_key=row.normalized_key,
            confidence=row.confidence,
            attributes=dict(row.attributes_json or {}),
            evidence_ids=[str(item) for item in (row.evidence_ids_json or [])],
            aliases=aliases or [],
            provenance=provenance or [],
        )

    def _relationship_response(
        self,
        row: GraphRelationship,
        *,
        provenance: list[ProvenanceItem] | None = None,
    ) -> GraphRelationshipResponse:
        return GraphRelationshipResponse(
            id=row.id,
            graph_id=row.graph_id,
            case_id=row.case_id,
            relationship_key=row.relationship_key,
            source_entity_key=row.source_entity_key,
            target_entity_key=row.target_entity_key,
            relationship_type=row.relationship_type,
            confidence=row.confidence,
            support_count=row.support_count,
            provenance_count=row.provenance_count,
            relationship_weight=row.relationship_weight,
            creation_source=row.creation_source,
            evidence_ids=[str(item) for item in (row.evidence_ids_json or [])],
            attributes=dict(row.attributes_json or {}),
            provenance=provenance or [],
        )

    def _run_response(
        self,
        run: KnowledgeGraphRun,
        *,
        entities: list[GraphEntityResponse] | None = None,
        relationships: list[GraphRelationshipResponse] | None = None,
    ) -> KnowledgeGraphResponse:
        return KnowledgeGraphResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            entity_count=run.entity_count,
            relationship_count=run.relationship_count,
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            metadata=dict(run.metadata_json or {}),
            provenance=dict(run.provenance_json or {}),
            created_at=run.created_at,
            completed_at=run.completed_at,
            entities=entities or [],
            relationships=relationships or [],
        )

    async def build_graph(self, case_id: UUID) -> KnowledgeGraphResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")

        run = KnowledgeGraphRun(
            case_id=case_id,
            status=GraphRunStatus.RUNNING.value,
            entity_count=0,
            relationship_count=0,
            engine_version=KG_ENGINE_VERSION,
            policy_version=KG_POLICY_VERSION,
            metadata_json={},
            provenance_json={},
        )
        await self.repository.add(run)
        await self.session.flush()

        try:
            result = await self.engine.build(case)
            for entity in result.entities:
                await self.repository.add(
                    GraphEntity(
                        graph_id=run.id,
                        case_id=case_id,
                        entity_key=entity.entity_id,
                        entity_type=entity.entity_type.value,
                        display_name=entity.display_name,
                        normalized_key=entity.normalized_key,
                        confidence=entity.confidence,
                        attributes_json=entity.attributes,
                        evidence_ids_json=list(entity.evidence_ids),
                    )
                )
                for alias in entity.aliases:
                    await self.repository.add(
                        GraphEntityAlias(
                            graph_id=run.id,
                            entity_key=entity.entity_id,
                            alias=alias,
                        )
                    )
                for ref in entity.provenance:
                    payload = provenance_to_dict(ref)
                    await self.repository.add(
                        GraphProvenance(
                            graph_id=run.id,
                            target_kind="entity",
                            target_key=entity.entity_id,
                            source_kind=payload["source_kind"],
                            source_id=payload["source_id"],
                            evidence_id=payload.get("evidence_id"),
                            finding_id=payload.get("finding_id"),
                            timeline_id=payload.get("timeline_id"),
                            correlation_id=payload.get("correlation_id"),
                            fusion_id=payload.get("fusion_id"),
                            ocr_field=payload.get("ocr_field"),
                            metadata_field=payload.get("metadata_field"),
                            timestamp=payload.get("timestamp"),
                            detail=payload.get("detail"),
                            engine_version=KG_ENGINE_VERSION,
                            policy_version=KG_POLICY_VERSION,
                        )
                    )

            for edge in result.relationships:
                await self.repository.add(
                    GraphRelationship(
                        graph_id=run.id,
                        case_id=case_id,
                        relationship_key=edge.relationship_id,
                        source_entity_key=edge.source_entity_id,
                        target_entity_key=edge.target_entity_id,
                        relationship_type=edge.relationship_type.value,
                        confidence=edge.confidence,
                        support_count=edge.support_count,
                        provenance_count=edge.provenance_count,
                        relationship_weight=edge.relationship_weight,
                        creation_source=edge.creation_source,
                        evidence_ids_json=list(edge.evidence_ids),
                        attributes_json=edge.attributes,
                    )
                )
                for ref in edge.provenance:
                    payload = provenance_to_dict(ref)
                    await self.repository.add(
                        GraphProvenance(
                            graph_id=run.id,
                            target_kind="relationship",
                            target_key=edge.relationship_id,
                            source_kind=payload["source_kind"],
                            source_id=payload["source_id"],
                            evidence_id=payload.get("evidence_id"),
                            finding_id=payload.get("finding_id"),
                            timeline_id=payload.get("timeline_id"),
                            correlation_id=payload.get("correlation_id"),
                            fusion_id=payload.get("fusion_id"),
                            ocr_field=payload.get("ocr_field"),
                            metadata_field=payload.get("metadata_field"),
                            timestamp=payload.get("timestamp"),
                            detail=payload.get("detail"),
                            engine_version=KG_ENGINE_VERSION,
                            policy_version=KG_POLICY_VERSION,
                        )
                    )

            run.status = GraphRunStatus.SUCCEEDED.value
            run.entity_count = len(result.entities)
            run.relationship_count = len(result.relationships)
            run.metadata_json = result.metadata
            run.provenance_json = result.provenance_summary
            run.completed_at = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(run)
            return await self.get_graph(run.id)
        except Exception as exc:  # noqa: BLE001
            run.status = GraphRunStatus.FAILED.value
            run.error_message = f"{type(exc).__name__}: {exc}"
            run.completed_at = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(run)
            return self._run_response(run)

    async def preview(self, case_id: UUID) -> GraphPreviewResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        result = await self.engine.build(case)
        return GraphPreviewResponse(
            case_id=case_id,
            entity_count=len(result.entities),
            relationship_count=len(result.relationships),
            entities=[
                {
                    "entity_key": item.entity_id,
                    "entity_type": item.entity_type.value,
                    "display_name": item.display_name,
                    "normalized_key": item.normalized_key,
                    "confidence": item.confidence,
                    "evidence_ids": list(item.evidence_ids),
                }
                for item in result.entities
            ],
            relationships=[
                {
                    "relationship_key": item.relationship_id,
                    "source_entity_key": item.source_entity_id,
                    "target_entity_key": item.target_entity_id,
                    "relationship_type": item.relationship_type.value,
                    "confidence": item.confidence,
                    "support_count": item.support_count,
                    "creation_source": item.creation_source,
                }
                for item in result.relationships
            ],
            provenance=result.provenance_summary,
            engine_version=KG_ENGINE_VERSION,
            policy_version=KG_POLICY_VERSION,
            persisted=False,
        )

    async def get_case_graph(self, case_id: UUID) -> KnowledgeGraphResponse:
        run = await self.repository.latest_run(case_id)
        if run is None:
            raise GraphNotFoundError("No knowledge graph for this case.")
        return await self.get_graph(run.id)

    async def get_graph(self, graph_id: UUID) -> KnowledgeGraphResponse:
        run = await self.repository.get_run(graph_id)
        if run is None:
            raise GraphNotFoundError("Knowledge graph not found.")
        entities = await self.repository.list_entities(graph_id=graph_id)
        relationships = await self.repository.list_relationships(graph_id=graph_id)
        entity_responses = [
            self._entity_response(row) for row in entities
        ]
        rel_responses = [
            self._relationship_response(row) for row in relationships
        ]
        return self._run_response(
            run, entities=entity_responses, relationships=rel_responses,
        )

    async def list_entities(
        self,
        *,
        graph_id: UUID | None = None,
        case_id: UUID | None = None,
        entity_type: str | None = None,
        query: str | None = None,
    ) -> GraphEntityListResponse:
        rows = await self.repository.list_entities(
            graph_id=graph_id,
            case_id=case_id,
            entity_type=entity_type,
            query=query,
        )
        items = [self._entity_response(row) for row in rows]
        return GraphEntityListResponse(items=items, total=len(items))

    async def list_relationships(
        self,
        *,
        graph_id: UUID | None = None,
        case_id: UUID | None = None,
        relationship_type: str | None = None,
    ) -> GraphRelationshipListResponse:
        rows = await self.repository.list_relationships(
            graph_id=graph_id,
            case_id=case_id,
            relationship_type=relationship_type,
        )
        items = [self._relationship_response(row) for row in rows]
        return GraphRelationshipListResponse(items=items, total=len(items))

    async def get_entity(self, entity_id: UUID) -> GraphEntityResponse:
        row = await self.repository.get_entity(entity_id)
        if row is None:
            raise EntityNotFoundError("Graph entity not found.")
        aliases = await self.repository.aliases_for(row.graph_id, row.entity_key)
        prov_rows = await self.repository.provenance_for(
            row.graph_id, row.entity_key,
        )
        return self._entity_response(
            row,
            aliases=[item.alias for item in aliases],
            provenance=[
                ProvenanceItem(
                    source_kind=item.source_kind,
                    source_id=item.source_id,
                    evidence_id=item.evidence_id,
                    finding_id=item.finding_id,
                    timeline_id=item.timeline_id,
                    correlation_id=item.correlation_id,
                    fusion_id=item.fusion_id,
                    ocr_field=item.ocr_field,
                    metadata_field=item.metadata_field,
                    timestamp=item.timestamp,
                    detail=item.detail,
                    engine_version=item.engine_version,
                    policy_version=item.policy_version,
                )
                for item in prov_rows
            ],
        )

    async def get_neighbors(self, entity_id: UUID) -> NeighborResponse:
        entity = await self.get_entity(entity_id)
        edges = await self.repository.neighbors(
            entity.graph_id, entity.entity_key,
        )
        neighbor_keys = sorted(
            {
                (
                    edge.target_entity_key
                    if edge.source_entity_key == entity.entity_key
                    else edge.source_entity_key
                )
                for edge in edges
            }
        )
        neighbors: list[GraphEntityResponse] = []
        for key in neighbor_keys:
            row = await self.repository.get_entity_by_key(entity.graph_id, key)
            if row is not None:
                neighbors.append(self._entity_response(row))
        return NeighborResponse(
            entity=entity,
            relationships=[self._relationship_response(edge) for edge in edges],
            neighbors=neighbors,
        )

    async def search(
        self, *, query: str, case_id: UUID | None = None,
    ) -> GraphEntityListResponse:
        return await self.list_entities(case_id=case_id, query=query)
