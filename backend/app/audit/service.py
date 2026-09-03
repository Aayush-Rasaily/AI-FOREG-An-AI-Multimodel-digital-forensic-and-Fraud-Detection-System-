"""Application service for audit, compliance, and integrity."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.exporters import export_json
from backend.app.audit.integrity import (
    verify_case_integrity,
    verify_evidence_integrity,
    verify_report_checksum,
)
from backend.app.audit.models import (
    AuditExportResult,
    IntegrityResult,
    IntegrityStatus,
)
from backend.app.audit.recorder import AuditRecorder
from backend.app.audit.repository import AuditRepository
from backend.app.audit.schemas import (
    AuditEventListResponse,
    AuditEventResponse,
    IntegrityResultResponse,
    IntegrityVerifyResponse,
)
from backend.app.core.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)


class AuditService:
    """Manage audit events, integrity verification, and export."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AuditRepository(session)
        self.recorder = AuditRecorder(session)

    async def record_event(
        self,
        *,
        operation: str,
        category: str,
        user: str = "system",
        case_id: UUID | None = None,
        evidence_id: UUID | None = None,
        previous_state: Any = None,
        new_state: Any = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        sha256_checksum: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Record an audit event and commit."""
        event_id = await self.recorder.record(
            operation=operation,
            category=category,
            user=user,
            case_id=case_id,
            evidence_id=evidence_id,
            previous_state=previous_state,
            new_state=new_state,
            client_ip=client_ip,
            user_agent=user_agent,
            sha256_checksum=sha256_checksum,
            metadata=metadata,
        )
        await self.session.commit()
        return event_id

    async def get_event(
        self, event_id: UUID,
    ) -> AuditEventResponse:
        event = await self.repository.get_event(event_id)
        if event is None:
            raise ResourceNotFoundError(
                "The requested audit event was not found.",
            )
        return self._event_response(event)

    async def list_events(
        self,
        *,
        case_id: UUID | None = None,
        evidence_id: UUID | None = None,
        operation: str | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditEventListResponse:
        events, total = await self.repository.list_events(
            case_id=case_id,
            evidence_id=evidence_id,
            operation=operation,
            category=category,
            limit=limit,
            offset=offset,
        )
        return AuditEventListResponse(
            items=[self._event_response(e) for e in events],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def verify_integrity(
        self,
        *,
        case_id: UUID | None = None,
        evidence_id: UUID | None = None,
        report_id: UUID | None = None,
    ) -> IntegrityVerifyResponse:
        results: list[IntegrityResult] = []
        if evidence_id:
            results.append(
                await verify_evidence_integrity(
                    self.session, evidence_id,
                ),
            )
        if report_id:
            results.append(
                await verify_report_checksum(
                    self.session, report_id,
                ),
            )
        if case_id:
            results.extend(
                await verify_case_integrity(
                    self.session, case_id,
                ),
            )
        verified = sum(
            1 for r in results
            if r.status == IntegrityStatus.VERIFIED
        )
        mismatched = sum(
            1 for r in results
            if r.status == IntegrityStatus.MISMATCH
        )
        unavailable = sum(
            1 for r in results
            if r.status == IntegrityStatus.UNAVAILABLE
        )
        overall = "VERIFIED"
        if mismatched > 0:
            overall = "MISMATCH"
        elif unavailable > 0 and verified == 0:
            overall = "UNAVAILABLE"
        return IntegrityVerifyResponse(
            results=[
                IntegrityResultResponse(
                    target_type=r.target_type,
                    target_id=r.target_id,
                    status=r.status.value,
                    expected_hash=r.expected_hash,
                    computed_hash=r.computed_hash,
                    detail=r.detail,
                )
                for r in results
            ],
            overall_status=overall,
            verified_count=verified,
            mismatch_count=mismatched,
            unavailable_count=unavailable,
        )

    async def export_audit_log(
        self,
        *,
        case_id: UUID | None = None,
        limit: int = 10000,
    ) -> AuditExportResult:
        events, _ = await self.repository.list_events(
            case_id=case_id, limit=limit, offset=0,
        )
        return export_json(events)

    @staticmethod
    def _event_response(
        event: Any,
    ) -> AuditEventResponse:
        return AuditEventResponse(
            id=event.id,
            timestamp=event.timestamp,
            user=event.user,
            operation=event.operation,
            category=event.category,
            case_id=event.case_id,
            evidence_id=event.evidence_id,
            previous_state=event.previous_state_json,
            new_state=event.new_state_json,
            client_ip=event.client_ip,
            user_agent=event.user_agent,
            engine_version=event.engine_version,
            policy_version=event.policy_version,
            sha256_checksum=event.sha256_checksum,
            integrity_hash=event.integrity_hash,
            metadata=event.metadata_json or {},
        )
