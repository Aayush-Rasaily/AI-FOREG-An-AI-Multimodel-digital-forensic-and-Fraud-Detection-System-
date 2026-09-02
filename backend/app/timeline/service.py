"""Application service for investigation timeline reconstruction."""

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
from backend.app.models.case import Case
from backend.app.models.timeline import (
    InvestigationTimeline,
    TimelineConflictRecord,
    TimelineEventRecord,
)
from backend.app.timeline.engine import TimelineEngine
from backend.app.timeline.exceptions import TimelineError
from backend.app.timeline.models import TimelineRunStatus
from backend.app.timeline.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.timeline.repository import TimelineRepository
from backend.app.timeline.schemas import (
    TimelineConflictResponse,
    TimelineDetailResponse,
    TimelineEventResponse,
    TimelineRunListResponse,
    TimelineRunResponse,
)

logger = logging.getLogger(__name__)


class TimelineService:
    """Queue and execute investigation timeline reconstruction."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: TimelineEngine | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.engine = engine or TimelineEngine()
        self.repository = TimelineRepository(session)

    async def create_timeline(self, case_id: UUID) -> TimelineRunResponse:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")
        active = await self.repository.get_active_for_case(case_id)
        if active is not None:
            raise ConflictError("An active timeline reconstruction already exists.")
        timeline = InvestigationTimeline(
            id=uuid4(),
            case_id=case_id,
            status=TimelineRunStatus.QUEUED,
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
            event_count=0,
            conflicts_count=0,
            metadata_json={"case_number": case.case_number},
            provenance_json={"case_id": str(case_id), "case_number": case.case_number},
        )
        try:
            await self.repository.add_timeline(timeline)
            await self.session.commit()
            await self.session.refresh(timeline)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active timeline reconstruction already exists.",
            ) from exc
        return self._run_response(timeline)

    async def run(self, timeline_id: UUID) -> None:
        timeline = await self.repository.get_timeline(timeline_id)
        if timeline is None or timeline.status != TimelineRunStatus.QUEUED:
            return
        case = await self.session.get(Case, timeline.case_id)
        if case is None:
            await self._fail_timeline(
                timeline_id,
                "CASE_NOT_FOUND",
                "The case record is no longer available.",
            )
            return
        timeline.status = TimelineRunStatus.RUNNING
        timeline.started_at = datetime.now(UTC)
        try:
            await self.session.commit()
            result = await self.engine.build(self.session, case)
            for event in result.events:
                await self.repository.add_event(
                    TimelineEventRecord(
                        id=uuid4(),
                        timeline_id=timeline.id,
                        case_id=event.case_id,
                        evidence_id=event.evidence_id,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        timestamp=event.timestamp,
                        timezone=event.timezone,
                        normalized_timestamp=event.normalized_timestamp,
                        confidence=event.confidence,
                        uncertainty_ms=event.uncertainty_ms,
                        description=event.description,
                        source=event.source,
                        source_id=event.source_id,
                        provenance_json=event.provenance,
                        metadata_json=event.metadata,
                        supporting_artifacts_json=list(event.supporting_artifacts),
                    )
                )
            for conflict in result.conflicts:
                await self.repository.add_conflict(
                    TimelineConflictRecord(
                        id=uuid4(),
                        timeline_id=timeline.id,
                        case_id=case.id,
                        conflict_id=conflict.conflict_id,
                        conflict_type=conflict.conflict_type,
                        evidence_id=conflict.evidence_id,
                        involved_event_ids_json=list(conflict.involved_event_ids),
                        explanation=conflict.explanation,
                        metadata_json=conflict.metadata,
                    )
                )
            timeline.status = TimelineRunStatus.SUCCEEDED
            timeline.event_count = len(result.events)
            timeline.conflicts_count = len(result.conflicts)
            timeline.completed_at = datetime.now(UTC)
            timeline.provenance_json = result.provenance
            timeline.metadata_json = {
                **timeline.metadata_json,
                **result.metadata,
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if isinstance(exc, TimelineError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "TIMELINE_RECONSTRUCTION_FAILED"
                safe_message = "The timeline reconstruction pipeline failed."
            await self._fail_timeline(timeline_id, error_code, safe_message)
            logger.exception(
                "Timeline reconstruction failed",
                extra={
                    "timeline_id": str(timeline_id),
                    "case_id": str(timeline.case_id),
                },
            )

    async def list_timelines(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> TimelineRunListResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        items, total = await self.repository.list_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        return TimelineRunListResponse(
            items=[self._run_response(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_latest(self, case_id: UUID) -> TimelineDetailResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        timeline = await self.repository.get_latest_for_case(case_id)
        if timeline is None:
            raise ResourceNotFoundError(
                "No investigation timeline exists for this case.",
            )
        return self._detail_response(timeline)

    async def get_timeline(self, timeline_id: UUID) -> TimelineDetailResponse:
        timeline = await self.repository.get_timeline_with_details(timeline_id)
        if timeline is None:
            raise ResourceNotFoundError("The requested timeline was not found.")
        return self._detail_response(timeline)

    async def list_conflicts(self, timeline_id: UUID) -> list[TimelineConflictResponse]:
        timeline = await self.repository.get_timeline(timeline_id)
        if timeline is None:
            raise ResourceNotFoundError("The requested timeline was not found.")
        conflicts = await self.repository.list_conflicts(timeline_id)
        return [self._conflict_response(item) for item in conflicts]

    async def delete_timeline(self, timeline_id: UUID) -> None:
        timeline = await self.repository.get_timeline(timeline_id)
        if timeline is None:
            raise ResourceNotFoundError("The requested timeline was not found.")
        await self.repository.delete_timeline(timeline_id)
        await self.session.commit()

    async def _fail_timeline(
        self,
        timeline_id: UUID,
        error_code: str,
        message: str,
    ) -> None:
        timeline = await self.repository.get_timeline(timeline_id)
        if timeline is not None:
            timeline.status = TimelineRunStatus.FAILED
            timeline.error_code = error_code
            timeline.error_message = message
            timeline.completed_at = datetime.now(UTC)
        await self.session.commit()

    @staticmethod
    def _run_response(timeline: InvestigationTimeline) -> TimelineRunResponse:
        return TimelineRunResponse(
            id=timeline.id,
            case_id=timeline.case_id,
            status=timeline.status,
            engine_version=timeline.engine_version,
            policy_version=timeline.policy_version,
            event_count=timeline.event_count,
            conflicts_count=timeline.conflicts_count,
            created_at=timeline.created_at,
            started_at=timeline.started_at,
            completed_at=timeline.completed_at,
            error_code=timeline.error_code,
            error_message=timeline.error_message,
            metadata=timeline.metadata_json,
            provenance=timeline.provenance_json,
        )

    def _detail_response(
        self, timeline: InvestigationTimeline
    ) -> TimelineDetailResponse:
        base = self._run_response(timeline)
        events = sorted(
            timeline.events,
            key=lambda item: (
                item.normalized_timestamp is None,
                item.normalized_timestamp or datetime.min.replace(tzinfo=UTC),
                -item.confidence,
                item.event_id,
            ),
        )
        return TimelineDetailResponse(
            **base.model_dump(),
            events=[self._event_response(item) for item in events],
            conflicts=[self._conflict_response(item) for item in timeline.conflicts],
        )

    @staticmethod
    def _event_response(record: TimelineEventRecord) -> TimelineEventResponse:
        return TimelineEventResponse(
            id=record.id,
            timeline_id=record.timeline_id,
            case_id=record.case_id,
            evidence_id=record.evidence_id,
            event_id=record.event_id,
            event_type=record.event_type,
            timestamp=record.timestamp,
            timezone=record.timezone,
            normalized_timestamp=record.normalized_timestamp,
            confidence=record.confidence,
            uncertainty_ms=record.uncertainty_ms,
            description=record.description,
            source=record.source,
            source_id=record.source_id,
            provenance=record.provenance_json,
            metadata=record.metadata_json,
            supporting_artifacts=list(record.supporting_artifacts_json),
            created_at=record.created_at,
        )

    @staticmethod
    def _conflict_response(record: TimelineConflictRecord) -> TimelineConflictResponse:
        return TimelineConflictResponse(
            id=record.id,
            timeline_id=record.timeline_id,
            case_id=record.case_id,
            conflict_id=record.conflict_id,
            conflict_type=record.conflict_type,
            evidence_id=record.evidence_id,
            involved_event_ids=list(record.involved_event_ids_json),
            explanation=record.explanation,
            metadata=record.metadata_json,
            created_at=record.created_at,
        )
