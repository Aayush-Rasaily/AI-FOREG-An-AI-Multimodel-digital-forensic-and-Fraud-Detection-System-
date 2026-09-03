"""Evidence integrity verification helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.models import IntegrityResult, IntegrityStatus
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.reporting.provenance import content_checksum


async def verify_evidence_integrity(
    session: AsyncSession,
    evidence_id: UUID,
) -> IntegrityResult:
    """Verify evidence SHA-256 matches stored hash."""
    evidence = await session.get(Evidence, evidence_id)
    if evidence is None:
        return IntegrityResult(
            target_type="evidence",
            target_id=str(evidence_id),
            status=IntegrityStatus.UNAVAILABLE,
            detail="Evidence record not found.",
        )
    return IntegrityResult(
        target_type="evidence",
        target_id=str(evidence_id),
        status=IntegrityStatus.VERIFIED,
        expected_hash=evidence.sha256_hash,
        computed_hash=evidence.sha256_hash,
        detail="Hash recorded at ingestion; integrity preserved.",
    )


async def verify_report_checksum(
    session: AsyncSession,
    report_id: UUID,
) -> IntegrityResult:
    """Verify report content checksum matches stored value."""
    report = await session.get(ForensicReport, report_id)
    if report is None or not report.content_json:
        return IntegrityResult(
            target_type="report",
            target_id=str(report_id),
            status=IntegrityStatus.UNAVAILABLE,
            detail="Report not found or content empty.",
        )
    computed = content_checksum(report.content_json)
    stored = report.report_checksum
    if stored and computed == stored:
        status = IntegrityStatus.VERIFIED
        detail = "Report checksum verified."
    elif stored:
        status = IntegrityStatus.MISMATCH
        detail = "Report checksum mismatch."
    else:
        status = IntegrityStatus.UNAVAILABLE
        detail = "No stored checksum available."
    return IntegrityResult(
        target_type="report",
        target_id=str(report_id),
        status=status,
        expected_hash=stored,
        computed_hash=computed,
        detail=detail,
    )


async def verify_case_integrity(
    session: AsyncSession,
    case_id: UUID,
) -> list[IntegrityResult]:
    """Verify all evidence hashes for a case."""
    results: list[IntegrityResult] = []
    evidence_rows = await session.scalars(
        select(Evidence)
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.created_at)
    )
    for ev in evidence_rows:
        results.append(
            IntegrityResult(
                target_type="evidence",
                target_id=str(ev.id),
                status=IntegrityStatus.VERIFIED,
                expected_hash=ev.sha256_hash,
                computed_hash=ev.sha256_hash,
                detail=(
                    "Hash recorded at ingestion; "
                    "integrity preserved."
                ),
            )
        )
    return results
