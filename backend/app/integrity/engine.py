"""Integrity monitoring collection and planning engine."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrity.drift import current_fingerprints
from backend.app.integrity.models import IntegrityPlan, RunStatus
from backend.app.integrity.policy import IM_ENGINE_VERSION, IM_POLICY_VERSION
from backend.app.integrity.scoring import compute_metrics
from backend.app.integrity.verifier import verify_case_snapshot
from backend.app.models.audit import AuditEvent
from backend.app.models.case import Case
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.document_ai import DocumentAIFinding
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.image_ai import ImageAIFinding


class IntegrityEngine:
    """Collect stored evidence signals and plan an integrity monitor run."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        storage: Any | None = None,
    ) -> None:
        self.session = session
        self.storage = storage

    async def load_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def collect(self, case_id: UUID) -> dict[str, Any]:
        evidence_result = await self.session.execute(
            select(Evidence).where(Evidence.case_id == case_id)
        )
        evidence_rows = list(evidence_result.scalars().all())
        evidence = [
            {
                "id": str(row.id),
                "evidence_number": row.evidence_number,
                "sha256_hash": row.sha256_hash,
                "file_size": int(row.file_size),
                "mime_type": row.mime_type,
                "storage_key": row.storage_key,
                "metadata": dict(row.metadata_json or {}),
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "updated_at": row.updated_at.isoformat() if row.updated_at else "",
            }
            for row in sorted(evidence_rows, key=lambda item: str(item.id))
        ]
        evidence_ids = [UUID(str(item["id"])) for item in evidence]

        custody_by: dict[str, list[dict[str, Any]]] = {
            str(item["id"]): [] for item in evidence
        }
        if evidence_ids:
            custody_result = await self.session.execute(
                select(ChainOfCustodyEvent).where(
                    ChainOfCustodyEvent.evidence_id.in_(evidence_ids)
                )
            )
            for row in custody_result.scalars().all():
                custody_by.setdefault(str(row.evidence_id), []).append(
                    {
                        "id": str(row.id),
                        "event_type": (
                            row.event_type.value
                            if hasattr(row.event_type, "value")
                            else str(row.event_type)
                        ),
                        "timestamp": (
                            row.timestamp.isoformat() if row.timestamp else ""
                        ),
                        "sha256_hash": row.sha256_hash,
                    }
                )
            for eid in custody_by:
                custody_by[eid] = sorted(
                    custody_by[eid],
                    key=lambda item: (item["timestamp"], item["id"]),
                )

        audit_evidence_ids: set[str] = set()
        if evidence_ids:
            audit_result = await self.session.execute(
                select(AuditEvent.evidence_id).where(
                    AuditEvent.evidence_id.in_(evidence_ids)
                )
            )
            audit_evidence_ids = {
                str(eid) for eid in audit_result.scalars().all() if eid is not None
            }

        ai_evidence_ids: set[str] = set()
        if evidence_ids:
            img = await self.session.execute(
                select(ImageAIFinding.evidence_id).where(
                    ImageAIFinding.evidence_id.in_(evidence_ids)
                )
            )
            ai_evidence_ids.update(str(eid) for eid in img.scalars().all())
            doc = await self.session.execute(
                select(DocumentAIFinding.evidence_id).where(
                    DocumentAIFinding.evidence_id.in_(evidence_ids)
                )
            )
            ai_evidence_ids.update(str(eid) for eid in doc.scalars().all())

        reports = await self.session.execute(
            select(ForensicReport).where(ForensicReport.case_id == case_id)
        )
        report_rows = [
            {"id": str(row.id)}
            for row in sorted(reports.scalars().all(), key=lambda item: str(item.id))
        ]

        storage_presence: dict[str, bool | None] = {}
        observed_sizes: dict[str, int] = {}
        for item in evidence:
            eid = str(item["id"])
            key = item.get("storage_key")
            if self.storage is None or not key:
                storage_presence[eid] = None
                continue
            try:
                exists = await self.storage.exists(str(key))
            except Exception:
                storage_presence[eid] = None
                continue
            storage_presence[eid] = bool(exists)
            if not exists:
                continue
            try:
                async with self.storage.open(str(key)) as handle:
                    handle.seek(0, 2)
                    observed_sizes[eid] = int(handle.tell())
            except Exception:
                continue

        return {
            "evidence": evidence,
            "custody_by_evidence": custody_by,
            "audit_evidence_ids": sorted(audit_evidence_ids),
            "ai_evidence_ids": sorted(ai_evidence_ids),
            "reports": report_rows,
            "storage_presence": storage_presence,
            "observed_sizes": observed_sizes,
            "fingerprints": current_fingerprints(evidence),
        }

    async def plan(
        self,
        case: Case,
        *,
        previous_fingerprints: dict[str, str] | None = None,
    ) -> IntegrityPlan:
        snapshot = await self.collect(case.id)
        checks, alerts, drifts, timeline = verify_case_snapshot(
            snapshot,
            previous_fingerprints=previous_fingerprints,
        )
        metrics = compute_metrics(
            checks,
            alerts,
            drifts,
            evidence_total=len(snapshot["evidence"]),
            evidence_checked=len(snapshot["evidence"]),
        )
        return IntegrityPlan(
            status=RunStatus.SUCCEEDED,
            metrics=metrics,
            checks=checks,
            alerts=alerts,
            drifts=drifts,
            timeline=timeline,
            provenance={
                "engine_version": IM_ENGINE_VERSION,
                "policy_version": IM_POLICY_VERSION,
                "evidence_count": len(snapshot["evidence"]),
                "fingerprints": snapshot["fingerprints"],
                "sources": sorted(
                    {
                        "evidence",
                        *(
                            ["custody"]
                            if any(snapshot["custody_by_evidence"].values())
                            else []
                        ),
                        *(["audit"] if snapshot["audit_evidence_ids"] else []),
                        *(["ai"] if snapshot["ai_evidence_ids"] else []),
                        *(["reports"] if snapshot["reports"] else []),
                    }
                ),
            },
        )
