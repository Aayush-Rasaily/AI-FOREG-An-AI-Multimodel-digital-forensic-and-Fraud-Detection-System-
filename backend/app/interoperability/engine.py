"""Snapshot assembly engine for investigation packages."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.interoperability.models import InvestigationSnapshot
from backend.app.interoperability.policy import (
    INTEROP_ENGINE_VERSION,
    INTEROP_POLICY_VERSION,
)
from backend.app.models.case import Case
from backend.app.models.correlation import CorrelationAnalysisRun
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.forensics import AnalysisRun
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.timeline import InvestigationTimeline, TimelineEventRecord


def _dt(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _collect_policy_versions() -> dict[str, str]:
    versions: dict[str, str] = {
        "interop_policy": INTEROP_POLICY_VERSION,
        "interop_engine": INTEROP_ENGINE_VERSION,
    }
    try:
        from backend.app.workflow.policy import WORKFLOW_POLICY_VERSION

        versions["workflow_policy"] = WORKFLOW_POLICY_VERSION
    except Exception:  # noqa: BLE001
        pass
    try:
        from backend.app.security.policy import SECURITY_POLICY_VERSION

        versions["security_policy"] = SECURITY_POLICY_VERSION
    except Exception:  # noqa: BLE001
        pass
    try:
        from backend.app.deployment.release import DEPLOYMENT_POLICY_VERSION

        versions["deployment_policy"] = DEPLOYMENT_POLICY_VERSION
    except Exception:  # noqa: BLE001
        pass
    return versions


class InteropEngine:
    """Assemble a deterministic investigation snapshot from persisted data."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def build_snapshot(
        self,
        case: Case,
        *,
        evidence_ids: list[UUID] | None = None,
    ) -> InvestigationSnapshot:
        evidence_rows = await self._evidence(case.id, evidence_ids)
        evidence_id_set = {row.id for row in evidence_rows}
        custody = await self._custody(evidence_id_set)
        extractions = await self._extractions(evidence_id_set)
        ai_summaries = await self._ai_summaries(evidence_id_set)
        fusion = await self._fusion(evidence_id_set)
        correlation = await self._correlation(case.id)
        timeline = await self._timeline(case.id)
        reports = await self._reports(case.id)
        workflow = await self._workflow(case.id)
        security = await self._security(case.id)

        case_payload = {
            "id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": (
                case.status.value
                if hasattr(case.status, "value")
                else str(case.status)
            ),
            "priority": (
                case.priority.value
                if hasattr(case.priority, "value")
                else str(case.priority)
            ),
            "created_by": case.created_by,
            "created_at": _dt(case.created_at),
            "updated_at": _dt(case.updated_at),
        }
        evidence_payload = [
            {
                "id": str(row.id),
                "case_id": str(row.case_id),
                "evidence_number": row.evidence_number,
                "original_filename": row.original_filename,
                "stored_filename": row.stored_filename,
                "mime_type": row.mime_type,
                "file_size": row.file_size,
                "sha256_hash": row.sha256_hash,
                "storage_key": row.storage_key,
                "status": (
                    row.status.value
                    if hasattr(row.status, "value")
                    else str(row.status)
                ),
                "created_at": _dt(row.created_at),
            }
            for row in sorted(evidence_rows, key=lambda item: str(item.id))
        ]
        return InvestigationSnapshot(
            case=case_payload,
            evidence=evidence_payload,
            custody=custody,
            extractions=extractions,
            ai_summaries=ai_summaries,
            fusion_summaries=fusion,
            correlation_summaries=correlation,
            timeline=timeline,
            reports=reports,
            workflow=workflow,
            security=security,
            policy_versions=_collect_policy_versions(),
            ai_engine_versions={},
        )

    async def _evidence(
        self, case_id: UUID, evidence_ids: list[UUID] | None,
    ) -> list[Evidence]:
        stmt = select(Evidence).where(Evidence.case_id == case_id)
        if evidence_ids:
            stmt = stmt.where(Evidence.id.in_(evidence_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _custody(self, evidence_ids: set[UUID]) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        stmt = select(ChainOfCustodyEvent).where(
            ChainOfCustodyEvent.evidence_id.in_(evidence_ids),
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "event_type": (
                    row.event_type.value
                    if hasattr(row.event_type, "value")
                    else str(row.event_type)
                ),
                "timestamp": _dt(row.timestamp),
                "actor_type": (
                    row.actor_type.value
                    if hasattr(row.actor_type, "value")
                    else str(row.actor_type)
                ),
                "actor_id": row.actor_id,
                "description": row.description,
                "sha256_hash": row.sha256_hash,
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _extractions(self, evidence_ids: set[UUID]) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        stmt = select(ExtractionRecord).where(
            ExtractionRecord.evidence_id.in_(evidence_ids),
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "extraction_type": (
                    row.extraction_type.value
                    if hasattr(row.extraction_type, "value")
                    else str(row.extraction_type)
                ),
                "method": row.method,
                "version": row.version,
                "created_at": _dt(row.created_at),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _ai_summaries(self, evidence_ids: set[UUID]) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        stmt = select(AnalysisRun).where(AnalysisRun.evidence_id.in_(evidence_ids))
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "status": str(getattr(row, "status", "")),
                "engine_version": str(getattr(row, "engine_version", "") or ""),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _fusion(self, evidence_ids: set[UUID]) -> list[dict[str, Any]]:
        if not evidence_ids:
            return []
        stmt = select(FusionAnalysisRun).where(
            FusionAnalysisRun.evidence_id.in_(evidence_ids),
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "status": str(getattr(row, "status", "")),
                "engine_version": str(getattr(row, "engine_version", "") or ""),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _correlation(self, case_id: UUID) -> list[dict[str, Any]]:
        stmt = select(CorrelationAnalysisRun).where(
            CorrelationAnalysisRun.case_id == case_id,
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "status": str(getattr(row, "status", "")),
                "engine_version": str(getattr(row, "engine_version", "") or ""),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _timeline(self, case_id: UUID) -> dict[str, Any] | None:
        stmt = (
            select(InvestigationTimeline)
            .where(InvestigationTimeline.case_id == case_id)
            .order_by(InvestigationTimeline.created_at.desc())
        )
        result = await self.session.execute(stmt)
        timeline = result.scalars().first()
        if timeline is None:
            return None
        events_result = await self.session.execute(
            select(TimelineEventRecord).where(
                TimelineEventRecord.timeline_id == timeline.id,
            )
        )
        events = list(events_result.scalars().all())
        return {
            "id": str(timeline.id),
            "status": str(getattr(timeline, "status", "")),
            "engine_version": str(getattr(timeline, "engine_version", "") or ""),
            "policy_version": str(getattr(timeline, "policy_version", "") or ""),
            "event_count": len(events),
            "events": [
                {
                    "id": str(event.id),
                    "event_type": str(getattr(event, "event_type", "")),
                    "description": getattr(event, "description", None),
                }
                for event in sorted(events, key=lambda item: str(item.id))
            ],
        }

    async def _reports(self, case_id: UUID) -> list[dict[str, Any]]:
        stmt = select(ForensicReport).where(ForensicReport.case_id == case_id)
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return [
            {
                "id": str(row.id),
                "status": str(getattr(row, "status", "")),
                "report_version": str(getattr(row, "report_version", "") or ""),
                "pdf_storage_key": getattr(row, "pdf_storage_key", None),
                "pdf_sha256": getattr(row, "pdf_sha256", None),
                "report_checksum": getattr(row, "report_checksum", None),
            }
            for row in sorted(rows, key=lambda item: str(item.id))
        ]

    async def _workflow(self, case_id: UUID) -> dict[str, Any] | None:
        try:
            from backend.app.models.workflow import InvestigationWorkflow
        except Exception:  # noqa: BLE001
            return None
        stmt = select(InvestigationWorkflow).where(
            InvestigationWorkflow.case_id == case_id,
        )
        result = await self.session.execute(stmt)
        row = result.scalars().first()
        if row is None:
            return None
        return {
            "id": str(row.id),
            "status": str(getattr(row, "status", "")),
        }

    async def _security(self, case_id: UUID) -> dict[str, Any] | None:
        try:
            from backend.app.models.security import CaseAccessRecord
        except Exception:  # noqa: BLE001
            return None
        stmt = select(CaseAccessRecord).where(CaseAccessRecord.case_id == case_id)
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())
        return {
            "access_count": len(rows),
            "access": [
                {
                    "id": str(row.id),
                    "user_id": str(row.user_id),
                    "access_level": row.access_level,
                    "active": row.active,
                }
                for row in sorted(rows, key=lambda item: str(item.id))
            ],
        }

    async def existing_case_identifiers(self) -> tuple[set[str], set[str]]:
        result = await self.session.execute(select(Case.id, Case.case_number))
        ids: set[str] = set()
        numbers: set[str] = set()
        for case_id, case_number in result.all():
            ids.add(str(case_id))
            numbers.add(case_number)
        return numbers, ids
