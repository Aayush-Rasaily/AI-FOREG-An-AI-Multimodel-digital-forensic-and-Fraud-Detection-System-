"""Application service for cross-evidence correlation analysis."""

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
from backend.app.correlation.engine import CorrelationEngine
from backend.app.correlation.exceptions import CorrelationError
from backend.app.correlation.models import CorrelationRunStatus
from backend.app.correlation.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.correlation.repository import CorrelationRepository
from backend.app.correlation.schemas import (
    CorrelationDetailResponse,
    CorrelationRunListResponse,
    CorrelationRunResponse,
    CorrelationSupportResponse,
    EvidenceCorrelationResponse,
)
from backend.app.models.case import Case
from backend.app.models.correlation import (
    CorrelationAnalysisRun,
    CorrelationSupportRecord,
    EvidenceCorrelationRecord,
)
from backend.app.models.evidence import Evidence

logger = logging.getLogger(__name__)


class CorrelationService:
    """Queue and execute cross-evidence correlation analysis."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: CorrelationEngine | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.engine = engine or CorrelationEngine()
        self.repository = CorrelationRepository(session)

    async def create_analysis(self, case_id: UUID) -> CorrelationRunResponse:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")
        active = await self.repository.get_active_for_case(case_id)
        if active is not None:
            raise ConflictError("An active correlation analysis already exists.")
        run = CorrelationAnalysisRun(
            id=uuid4(),
            case_id=case_id,
            status=CorrelationRunStatus.QUEUED,
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
            correlation_count=0,
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
                "An active correlation analysis already exists.",
            ) from exc
        return self._run_response(run)

    async def run(self, analysis_id: UUID) -> None:
        run = await self.repository.get_run(analysis_id)
        if run is None or run.status != CorrelationRunStatus.QUEUED:
            return
        case = await self.session.get(Case, run.case_id)
        if case is None:
            await self._fail_run(
                analysis_id,
                "CASE_NOT_FOUND",
                "The case record is no longer available.",
            )
            return
        run.status = CorrelationRunStatus.RUNNING
        run.started_at = datetime.now(UTC)
        try:
            await self.session.commit()
            result = await self.engine.build(self.session, case)
            for item in result.correlations:
                record = EvidenceCorrelationRecord(
                    id=uuid4(),
                    analysis_run_id=run.id,
                    case_id=item.case_id,
                    left_evidence_id=item.left_evidence_id,
                    right_evidence_id=item.right_evidence_id,
                    correlation_id=item.correlation_id,
                    correlation_type=item.correlation_type,
                    score=item.score,
                    confidence=item.confidence,
                    explanation=item.explanation,
                    supporting_findings_json=list(item.supporting_findings),
                    supporting_metadata_json=dict(item.supporting_metadata),
                    supporting_entities_json=list(item.supporting_entities),
                    provenance_json=dict(item.provenance),
                )
                await self.repository.add_correlation(record)
                for support in item.supports:
                    await self.repository.add_support(
                        CorrelationSupportRecord(
                            id=uuid4(),
                            correlation_id=record.id,
                            support_kind=support.support_kind,
                            support_ref=support.support_id,
                            label=support.label,
                            value=support.value,
                            metadata_json=dict(support.metadata),
                        )
                    )
            run.status = CorrelationRunStatus.SUCCEEDED
            run.correlation_count = len(result.correlations)
            run.evidence_count = int(result.metadata.get("evidence_count", 0))
            run.completed_at = datetime.now(UTC)
            run.provenance_json = result.provenance
            run.metadata_json = {**run.metadata_json, **result.metadata}
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if isinstance(exc, CorrelationError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "CORRELATION_ANALYSIS_FAILED"
                safe_message = "The correlation analysis pipeline failed."
            await self._fail_run(analysis_id, error_code, safe_message)
            logger.exception(
                "Correlation analysis failed",
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
    ) -> CorrelationRunListResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        items, total = await self.repository.list_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        return CorrelationRunListResponse(
            items=[self._run_response(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_latest(self, case_id: UUID) -> CorrelationDetailResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        run = await self.repository.get_latest_for_case(case_id)
        if run is None:
            raise ResourceNotFoundError(
                "No correlation analysis exists for this case.",
            )
        return self._detail_response(run)

    async def get_run(self, analysis_id: UUID) -> CorrelationDetailResponse:
        run = await self.repository.get_run_with_details(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested correlation analysis was not found.",
            )
        return self._detail_response(run)

    async def get_correlation(
        self,
        correlation_id: UUID,
    ) -> EvidenceCorrelationResponse:
        record = await self.repository.get_correlation(correlation_id)
        if record is None:
            raise ResourceNotFoundError("The requested correlation was not found.")
        return self._correlation_response(record)

    async def list_for_evidence(
        self,
        evidence_id: UUID,
    ) -> list[EvidenceCorrelationResponse]:
        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        latest = await self.repository.get_latest_for_case(evidence.case_id)
        if latest is None:
            return []
        items = [
            item
            for item in latest.correlations
            if item.left_evidence_id == evidence_id
            or item.right_evidence_id == evidence_id
        ]
        return [self._correlation_response(item) for item in items]

    async def delete_run(self, analysis_id: UUID) -> None:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested correlation analysis was not found.",
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
            run.status = CorrelationRunStatus.FAILED
            run.error_code = error_code
            run.error_message = message
            run.completed_at = datetime.now(UTC)
        await self.session.commit()

    @staticmethod
    def _run_response(run: CorrelationAnalysisRun) -> CorrelationRunResponse:
        return CorrelationRunResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            correlation_count=run.correlation_count,
            evidence_count=run.evidence_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
            provenance=run.provenance_json,
        )

    def _detail_response(
        self,
        run: CorrelationAnalysisRun,
    ) -> CorrelationDetailResponse:
        base = self._run_response(run)
        correlations = sorted(
            run.correlations,
            key=lambda item: (
                -item.score,
                item.correlation_type.value,
                str(item.left_evidence_id),
                str(item.right_evidence_id),
            ),
        )
        return CorrelationDetailResponse(
            **base.model_dump(),
            correlations=[self._correlation_response(item) for item in correlations],
        )

    @staticmethod
    def _correlation_response(
        record: EvidenceCorrelationRecord,
    ) -> EvidenceCorrelationResponse:
        return EvidenceCorrelationResponse(
            id=record.id,
            analysis_run_id=record.analysis_run_id,
            case_id=record.case_id,
            left_evidence_id=record.left_evidence_id,
            right_evidence_id=record.right_evidence_id,
            correlation_id=record.correlation_id,
            correlation_type=record.correlation_type,
            score=record.score,
            confidence=record.confidence,
            explanation=record.explanation,
            supporting_findings=list(record.supporting_findings_json),
            supporting_metadata=dict(record.supporting_metadata_json),
            supporting_entities=list(record.supporting_entities_json),
            provenance=dict(record.provenance_json),
            supports=[
                CorrelationSupportResponse(
                    id=support.id,
                    support_kind=support.support_kind,
                    support_ref=support.support_ref,
                    label=support.label,
                    value=support.value,
                    metadata=dict(support.metadata_json),
                )
                for support in record.support_records
            ],
            created_at=record.created_at,
        )
