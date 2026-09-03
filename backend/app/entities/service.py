"""Application service for entity resolution analysis."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import ConflictError, ResourceNotFoundError
from backend.app.entities.exceptions import EntityResolutionError
from backend.app.entities.models import EntityRunStatus
from backend.app.entities.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.entities.repository import EntityRepository
from backend.app.entities.resolver import EntityResolver
from backend.app.entities.schemas import (
    CanonicalEntityResponse,
    EntityDetailResponse,
    EntityRelationshipResponse,
    EntityRunListResponse,
    EntityRunResponse,
    EntitySupportResponse,
    InvestigationGraphResponse,
)
from backend.app.models.case import Case
from backend.app.models.entity import (
    EntityRelationshipRecord,
    EntityResolutionRun,
    EntitySupportRecord,
    InvestigationEntityRecord,
)

logger = logging.getLogger(__name__)


class EntityService:
    """Queue and execute deterministic entity-resolution analysis."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        resolver: EntityResolver | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.resolver = resolver or EntityResolver()
        self.repository = EntityRepository(session)

    async def create_analysis(self, case_id: UUID) -> EntityRunResponse:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")
        active = await self.repository.get_active_for_case(case_id)
        if active is not None:
            raise ConflictError("An active entity-resolution analysis already exists.")
        run = EntityResolutionRun(
            id=uuid4(),
            case_id=case_id,
            status=EntityRunStatus.QUEUED,
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
            entity_count=0,
            relationship_count=0,
            evidence_count=0,
            metadata_json={"case_number": case.case_number},
            provenance_json={"case_id": str(case_id), "case_number": case.case_number},
        )
        try:
            await self.repository.add_run(run)
            await self.session.commit()
            await self.session.refresh(run)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active entity-resolution analysis already exists.",
            ) from exc
        return self._run_response(run)

    async def run(self, analysis_id: UUID) -> None:
        run = await self.repository.get_run(analysis_id)
        if run is None or run.status != EntityRunStatus.QUEUED:
            return
        case = await self.session.get(Case, run.case_id)
        if case is None:
            await self._fail_run(
                analysis_id,
                "CASE_NOT_FOUND",
                "The case record is no longer available.",
            )
            return
        run.status = EntityRunStatus.RUNNING
        run.started_at = datetime.now(UTC)
        try:
            await self.session.commit()
            result = await self.resolver.resolve(self.session, case)
            for item in result.entities:
                entity_record = InvestigationEntityRecord(
                    id=uuid4(),
                    analysis_run_id=run.id,
                    case_id=item.case_id,
                    canonical_id=item.canonical_id,
                    entity_type=item.entity_type,
                    display_name=item.display_name,
                    normalized_key=item.normalized_key,
                    confidence=item.confidence,
                    support_count=item.support_count,
                    evidence_ids_json=[str(value) for value in item.evidence_ids],
                    attributes_json=dict(item.attributes),
                    provenance_json=dict(item.provenance),
                )
                await self.repository.add_entity(entity_record)
                for support in item.supports:
                    await self.repository.add_support(
                        EntitySupportRecord(
                            id=uuid4(),
                            entity_id=entity_record.id,
                            relationship_id=None,
                            support_kind=support.support_kind,
                            support_ref=support.support_id,
                            label=support.label,
                            value=support.value,
                            metadata_json=dict(support.metadata),
                        )
                    )
            for edge in result.relationships:
                relationship_record = EntityRelationshipRecord(
                    id=uuid4(),
                    analysis_run_id=run.id,
                    case_id=edge.case_id,
                    relationship_id=edge.relationship_id,
                    source_canonical_id=edge.source_canonical_id,
                    target_canonical_id=edge.target_canonical_id,
                    relationship_type=edge.relationship_type,
                    confidence=edge.confidence,
                    support_count=edge.support_count,
                    explanation=edge.explanation,
                    evidence_ids_json=[str(value) for value in edge.evidence_ids],
                    provenance_json=dict(edge.provenance),
                )
                await self.repository.add_relationship(relationship_record)
                for support in edge.supports:
                    await self.repository.add_support(
                        EntitySupportRecord(
                            id=uuid4(),
                            entity_id=None,
                            relationship_id=relationship_record.id,
                            support_kind=support.support_kind,
                            support_ref=support.support_id,
                            label=support.label,
                            value=support.value,
                            metadata_json=dict(support.metadata),
                        )
                    )
            run.status = EntityRunStatus.SUCCEEDED
            run.entity_count = len(result.entities)
            run.relationship_count = len(result.relationships)
            run.evidence_count = int(result.metadata.get("evidence_count", 0))
            run.completed_at = datetime.now(UTC)
            run.provenance_json = result.provenance
            run.metadata_json = {**run.metadata_json, **result.metadata}
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if isinstance(exc, EntityResolutionError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "ENTITY_RESOLUTION_FAILED"
                safe_message = "The entity-resolution pipeline failed."
            await self._fail_run(analysis_id, error_code, safe_message)
            logger.exception(
                "Entity resolution failed",
                extra={
                    "analysis_id": str(analysis_id),
                    "case_id": str(run.case_id),
                },
            )

    async def list_runs(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> EntityRunListResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        items, total = await self.repository.list_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        return EntityRunListResponse(
            items=[self._run_response(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_latest(self, case_id: UUID) -> EntityDetailResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        run = await self.repository.get_latest_for_case(case_id)
        if run is None:
            raise ResourceNotFoundError(
                "No entity-resolution analysis exists for this case.",
            )
        return self._detail_response(run)

    async def get_run(self, analysis_id: UUID) -> EntityDetailResponse:
        run = await self.repository.get_run_with_details(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested entity-resolution analysis was not found.",
            )
        return self._detail_response(run)

    async def get_entity(self, entity_id: UUID) -> CanonicalEntityResponse:
        record = await self.repository.get_entity(entity_id)
        if record is None:
            raise ResourceNotFoundError("The requested entity was not found.")
        return self._entity_response(record)

    async def get_entity_graph(self, entity_id: UUID) -> InvestigationGraphResponse:
        record = await self.repository.get_entity(entity_id)
        if record is None:
            raise ResourceNotFoundError("The requested entity was not found.")
        run = await self.repository.get_run_with_details(record.analysis_run_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested entity-resolution analysis was not found.",
            )
        related_ids = {record.canonical_id}
        edges: list[EntityRelationshipRecord] = []
        for edge in run.relationships:
            if (
                edge.source_canonical_id == record.canonical_id
                or edge.target_canonical_id == record.canonical_id
            ):
                edges.append(edge)
                related_ids.add(edge.source_canonical_id)
                related_ids.add(edge.target_canonical_id)
        nodes = [
            item for item in run.entities if item.canonical_id in related_ids
        ]
        node_responses = [
            self._entity_response(item)
            for item in sorted(
                nodes,
                key=lambda item: (
                    item.entity_type.value,
                    item.normalized_key,
                    item.canonical_id,
                ),
            )
        ]
        edge_responses = [
            self._relationship_response(item)
            for item in sorted(
                edges,
                key=lambda item: (
                    -item.confidence,
                    item.relationship_type.value,
                    item.source_canonical_id,
                    item.target_canonical_id,
                ),
            )
        ]
        return InvestigationGraphResponse(
            nodes=node_responses,
            edges=edge_responses,
            provenance={
                "center_canonical_id": record.canonical_id,
                "node_count": len(node_responses),
            },
            metadata={"edge_count": len(edge_responses)},
        )

    async def get_entity_relationships(
        self,
        entity_id: UUID,
    ) -> list[EntityRelationshipResponse]:
        record = await self.repository.get_entity(entity_id)
        if record is None:
            raise ResourceNotFoundError("The requested entity was not found.")
        items = await self.repository.list_relationships_for_entity(record)
        return [self._relationship_response(item) for item in items]

    async def delete_run(self, analysis_id: UUID) -> None:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested entity-resolution analysis was not found.",
            )
        await self.repository.delete_run(analysis_id)
        await self.session.commit()

    async def _fail_run(
        self,
        analysis_id: UUID,
        error_code: str,
        message: str,
    ) -> None:
        run = await self.repository.get_run(analysis_id)
        if run is not None:
            run.status = EntityRunStatus.FAILED
            run.error_code = error_code
            run.error_message = message
            run.completed_at = datetime.now(UTC)
        await self.session.commit()

    @staticmethod
    def _run_response(run: EntityResolutionRun) -> EntityRunResponse:
        return EntityRunResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            entity_count=run.entity_count,
            relationship_count=run.relationship_count,
            evidence_count=run.evidence_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
            provenance=run.provenance_json,
        )

    def _detail_response(self, run: EntityResolutionRun) -> EntityDetailResponse:
        base = self._run_response(run)
        entities = sorted(
            run.entities,
            key=lambda item: (
                item.entity_type.value,
                item.normalized_key,
                item.canonical_id,
            ),
        )
        relationships = sorted(
            run.relationships,
            key=lambda item: (
                -item.confidence,
                item.relationship_type.value,
                item.source_canonical_id,
                item.target_canonical_id,
            ),
        )
        entity_responses = [self._entity_response(item) for item in entities]
        relationship_responses = [
            self._relationship_response(item) for item in relationships
        ]
        return EntityDetailResponse(
            **base.model_dump(),
            entities=entity_responses,
            relationships=relationship_responses,
            graph=InvestigationGraphResponse(
                nodes=entity_responses,
                edges=relationship_responses,
                provenance=dict(run.provenance_json),
                metadata=dict(run.metadata_json),
            ),
        )

    @staticmethod
    def _support_response(support: EntitySupportRecord) -> EntitySupportResponse:
        return EntitySupportResponse(
            id=support.id,
            support_kind=support.support_kind,
            support_ref=support.support_ref,
            label=support.label,
            value=support.value,
            metadata=dict(support.metadata_json),
        )

    def _entity_response(
        self,
        record: InvestigationEntityRecord,
    ) -> CanonicalEntityResponse:
        return CanonicalEntityResponse(
            id=record.id,
            analysis_run_id=record.analysis_run_id,
            case_id=record.case_id,
            canonical_id=record.canonical_id,
            entity_type=record.entity_type,
            display_name=record.display_name,
            normalized_key=record.normalized_key,
            confidence=record.confidence,
            support_count=record.support_count,
            evidence_ids=[UUID(value) for value in record.evidence_ids_json],
            attributes=dict(record.attributes_json),
            provenance=dict(record.provenance_json),
            supports=[
                self._support_response(support) for support in record.support_records
            ],
            created_at=record.created_at,
        )

    def _relationship_response(
        self,
        record: EntityRelationshipRecord,
    ) -> EntityRelationshipResponse:
        return EntityRelationshipResponse(
            id=record.id,
            analysis_run_id=record.analysis_run_id,
            case_id=record.case_id,
            relationship_id=record.relationship_id,
            source_canonical_id=record.source_canonical_id,
            target_canonical_id=record.target_canonical_id,
            relationship_type=record.relationship_type,
            confidence=record.confidence,
            support_count=record.support_count,
            explanation=record.explanation,
            evidence_ids=[UUID(value) for value in record.evidence_ids_json],
            provenance=dict(record.provenance_json),
            supports=[
                self._support_response(support) for support in record.support_records
            ],
            created_at=record.created_at,
        )
