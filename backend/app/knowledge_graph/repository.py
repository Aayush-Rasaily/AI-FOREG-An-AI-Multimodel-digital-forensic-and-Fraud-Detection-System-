"""Persistence helpers for knowledge graph runs and nodes."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.knowledge_graph import (
    GraphEntity,
    GraphEntityAlias,
    GraphProvenance,
    GraphRelationship,
    KnowledgeGraphRun,
)


class KnowledgeGraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entity: object) -> None:
        self.session.add(entity)

    async def get_run(self, graph_id: UUID) -> KnowledgeGraphRun | None:
        return await self.session.get(KnowledgeGraphRun, graph_id)

    async def latest_run(self, case_id: UUID) -> KnowledgeGraphRun | None:
        result = await self.session.execute(
            select(KnowledgeGraphRun)
            .where(KnowledgeGraphRun.case_id == case_id)
            .order_by(KnowledgeGraphRun.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def list_entities(
        self,
        *,
        graph_id: UUID | None = None,
        case_id: UUID | None = None,
        entity_type: str | None = None,
        query: str | None = None,
        limit: int = 200,
    ) -> list[GraphEntity]:
        stmt = select(GraphEntity)
        if graph_id is not None:
            stmt = stmt.where(GraphEntity.graph_id == graph_id)
        if case_id is not None:
            stmt = stmt.where(GraphEntity.case_id == case_id)
        if entity_type:
            stmt = stmt.where(GraphEntity.entity_type == entity_type)
        if query:
            pattern = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    GraphEntity.display_name.ilike(pattern),
                    GraphEntity.normalized_key.ilike(pattern),
                    GraphEntity.entity_key.ilike(pattern),
                )
            )
        stmt = stmt.order_by(
            GraphEntity.entity_type.asc(),
            GraphEntity.normalized_key.asc(),
        ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_relationships(
        self,
        *,
        graph_id: UUID | None = None,
        case_id: UUID | None = None,
        relationship_type: str | None = None,
        limit: int = 500,
    ) -> list[GraphRelationship]:
        stmt = select(GraphRelationship)
        if graph_id is not None:
            stmt = stmt.where(GraphRelationship.graph_id == graph_id)
        if case_id is not None:
            stmt = stmt.where(GraphRelationship.case_id == case_id)
        if relationship_type:
            stmt = stmt.where(
                GraphRelationship.relationship_type == relationship_type
            )
        stmt = stmt.order_by(
            GraphRelationship.relationship_type.asc(),
            GraphRelationship.source_entity_key.asc(),
            GraphRelationship.target_entity_key.asc(),
        ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_entity_by_key(
        self, graph_id: UUID, entity_key: str,
    ) -> GraphEntity | None:
        result = await self.session.execute(
            select(GraphEntity).where(
                GraphEntity.graph_id == graph_id,
                GraphEntity.entity_key == entity_key,
            )
        )
        return result.scalars().first()

    async def get_entity(self, entity_id: UUID) -> GraphEntity | None:
        return await self.session.get(GraphEntity, entity_id)

    async def neighbors(
        self, graph_id: UUID, entity_key: str,
    ) -> list[GraphRelationship]:
        result = await self.session.execute(
            select(GraphRelationship).where(
                GraphRelationship.graph_id == graph_id,
                or_(
                    GraphRelationship.source_entity_key == entity_key,
                    GraphRelationship.target_entity_key == entity_key,
                ),
            ).order_by(GraphRelationship.relationship_type.asc())
        )
        return list(result.scalars().all())

    async def aliases_for(
        self, graph_id: UUID, entity_key: str,
    ) -> list[GraphEntityAlias]:
        result = await self.session.execute(
            select(GraphEntityAlias)
            .where(
                GraphEntityAlias.graph_id == graph_id,
                GraphEntityAlias.entity_key == entity_key,
            )
            .order_by(GraphEntityAlias.alias.asc())
        )
        return list(result.scalars().all())

    async def provenance_for(
        self, graph_id: UUID, target_key: str,
    ) -> list[GraphProvenance]:
        result = await self.session.execute(
            select(GraphProvenance)
            .where(
                GraphProvenance.graph_id == graph_id,
                GraphProvenance.target_key == target_key,
            )
            .order_by(
                GraphProvenance.source_kind.asc(),
                GraphProvenance.source_id.asc(),
            )
        )
        return list(result.scalars().all())
