"""Service facade for Phase 9F integrity monitoring."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.integrity.engine import IntegrityEngine
from backend.app.integrity.exceptions import IntegrityRunNotFoundError
from backend.app.integrity.models import IntegrityPlan, ProvenanceBundle, RunStatus
from backend.app.integrity.policy import IM_ENGINE_VERSION, IM_POLICY_VERSION
from backend.app.integrity.repository import IntegrityRepository
from backend.app.integrity.schemas import (
    IntegrityAlertListResponse,
    IntegrityAlertResponse,
    IntegrityCheckResponse,
    IntegrityDriftListResponse,
    IntegrityDriftResponse,
    IntegrityHistoryItem,
    IntegrityHistoryResponse,
    IntegrityMetricsResponse,
    IntegrityPreviewResponse,
    IntegrityRunResponse,
)
from backend.app.models.integrity import (
    IntegrityAlert,
    IntegrityCheck,
    IntegrityDriftRecord,
    IntegrityMonitorRun,
)


def _provenance_dict(bundle: ProvenanceBundle) -> dict[str, Any]:
    return {
        "evidence_ids": list(bundle.evidence_ids),
        "custody_event_ids": list(bundle.custody_event_ids),
        "audit_event_ids": list(bundle.audit_event_ids),
        "report_ids": list(bundle.report_ids),
        "storage_keys": list(bundle.storage_keys),
        "detail": bundle.detail,
        "engine_version": IM_ENGINE_VERSION,
        "policy_version": IM_POLICY_VERSION,
    }


class IntegrityMonitorService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        storage: Any | None = None,
    ) -> None:
        self.session = session
        self.repository = IntegrityRepository(session)
        self.engine = IntegrityEngine(session, storage=storage)

    def _metrics(self, data: dict | object) -> IntegrityMetricsResponse:
        if isinstance(data, dict):
            return IntegrityMetricsResponse(**data)
        return IntegrityMetricsResponse(
            checks_total=getattr(data, "checks_total", 0),
            checks_passed=getattr(data, "checks_passed", 0),
            checks_failed=getattr(data, "checks_failed", 0),
            checks_warned=getattr(data, "checks_warned", 0),
            alert_count=getattr(data, "alert_count", 0),
            drift_count=getattr(data, "drift_count", 0),
            evidence_coverage_pct=getattr(data, "evidence_coverage_pct", 0.0),
            integrity_score=getattr(data, "integrity_score", 0.0),
            critical_alerts=getattr(data, "critical_alerts", 0),
            high_alerts=getattr(data, "high_alerts", 0),
        )

    def _check_response(self, row: IntegrityCheck) -> IntegrityCheckResponse:
        return IntegrityCheckResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            check_key=row.check_key,
            check_code=row.check_code,
            title=row.title,
            status=row.status,
            severity=row.severity,
            evidence_id=row.evidence_id,
            message=row.message,
            expected=row.expected,
            observed=row.observed,
            provenance=dict(row.provenance_json or {}),
            created_at=row.created_at,
        )

    def _alert_response(self, row: IntegrityAlert) -> IntegrityAlertResponse:
        return IntegrityAlertResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            alert_key=row.alert_key,
            alert_code=row.alert_code,
            severity=row.severity,
            title=row.title,
            message=row.message,
            evidence_id=row.evidence_id,
            check_code=row.check_code,
            provenance=dict(row.provenance_json or {}),
            created_at=row.created_at,
        )

    def _drift_response(self, row: IntegrityDriftRecord) -> IntegrityDriftResponse:
        return IntegrityDriftResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            drift_key=row.drift_key,
            evidence_id=row.evidence_id,
            field_name=row.field_name,
            previous_value=row.previous_value,
            current_value=row.current_value,
            message=row.message,
            provenance=dict(row.provenance_json or {}),
            created_at=row.created_at,
        )

    def _plan_drafts(
        self,
        case_id: UUID,
        plan: IntegrityPlan,
    ) -> tuple[
        list[IntegrityCheckResponse],
        list[IntegrityAlertResponse],
        list[IntegrityDriftResponse],
    ]:
        checks = [
            IntegrityCheckResponse(
                case_id=case_id,
                check_key=item.check_key,
                check_code=item.check_code,
                title=item.title,
                status=item.status.value,
                severity=item.severity.value,
                evidence_id=item.evidence_id,
                message=item.message,
                expected=item.expected,
                observed=item.observed,
                provenance=_provenance_dict(item.provenance),
            )
            for item in plan.checks
        ]
        alerts = [
            IntegrityAlertResponse(
                case_id=case_id,
                alert_key=item.alert_key,
                alert_code=item.alert_code,
                severity=item.severity.value,
                title=item.title,
                message=item.message,
                evidence_id=item.evidence_id,
                check_code=item.check_code,
                provenance=_provenance_dict(item.provenance),
            )
            for item in plan.alerts
        ]
        drifts = [
            IntegrityDriftResponse(
                case_id=case_id,
                drift_key=item.drift_key,
                evidence_id=item.evidence_id,
                field_name=item.field_name,
                previous_value=item.previous_value,
                current_value=item.current_value,
                message=item.message,
                provenance=_provenance_dict(item.provenance),
            )
            for item in plan.drifts
        ]
        return checks, alerts, drifts

    async def _hydrate(self, run: IntegrityMonitorRun) -> IntegrityRunResponse:
        checks = [
            self._check_response(row)
            for row in await self.repository.checks_for_run(run.id)
        ]
        alerts = [
            self._alert_response(row)
            for row in await self.repository.alerts_for_run(run.id)
        ]
        drifts = [
            self._drift_response(row)
            for row in await self.repository.drifts_for_run(run.id)
        ]
        return IntegrityRunResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            check_count=run.check_count,
            alert_count=run.alert_count,
            drift_count=run.drift_count,
            metrics=self._metrics(run.metrics_json or {}),
            timeline=list(run.timeline_json or []),
            fingerprints=dict(run.fingerprints_json or {}),
            provenance=dict(run.provenance_json or {}),
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            created_at=run.created_at,
            completed_at=run.completed_at,
            checks=checks,
            alerts=alerts,
            drifts=drifts,
            persisted=True,
        )

    async def generate(self, case_id: UUID) -> IntegrityRunResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        previous = await self.repository.get_latest_run(case_id)
        previous_fps = dict(previous.fingerprints_json or {}) if previous else {}
        plan = await self.engine.plan(case, previous_fingerprints=previous_fps)
        fingerprints = dict(plan.provenance.get("fingerprints") or {})
        run = IntegrityMonitorRun(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            check_count=len(plan.checks),
            alert_count=len(plan.alerts),
            drift_count=len(plan.drifts),
            metrics_json=self._metrics(plan.metrics).model_dump(),
            timeline_json=plan.timeline,
            fingerprints_json=fingerprints,
            provenance_json={
                k: v for k, v in plan.provenance.items() if k != "fingerprints"
            },
            engine_version=IM_ENGINE_VERSION,
            policy_version=IM_POLICY_VERSION,
            completed_at=datetime.now(UTC),
        )
        await self.repository.add_run(run)
        await self.repository.add_checks(
            [
                IntegrityCheck(
                    run_id=run.id,
                    case_id=case_id,
                    check_key=item.check_key,
                    check_code=item.check_code,
                    title=item.title,
                    status=item.status.value,
                    severity=item.severity.value,
                    evidence_id=item.evidence_id,
                    message=item.message,
                    expected=item.expected,
                    observed=item.observed,
                    provenance_json=_provenance_dict(item.provenance),
                )
                for item in plan.checks
            ]
        )
        await self.repository.add_alerts(
            [
                IntegrityAlert(
                    run_id=run.id,
                    case_id=case_id,
                    alert_key=item.alert_key,
                    alert_code=item.alert_code,
                    severity=item.severity.value,
                    title=item.title,
                    message=item.message,
                    evidence_id=item.evidence_id,
                    check_code=item.check_code,
                    provenance_json=_provenance_dict(item.provenance),
                )
                for item in plan.alerts
            ]
        )
        await self.repository.add_drifts(
            [
                IntegrityDriftRecord(
                    run_id=run.id,
                    case_id=case_id,
                    drift_key=item.drift_key,
                    evidence_id=item.evidence_id,
                    field_name=item.field_name,
                    previous_value=item.previous_value,
                    current_value=item.current_value,
                    message=item.message,
                    provenance_json=_provenance_dict(item.provenance),
                    integrity_score=plan.metrics.integrity_score,
                )
                for item in plan.drifts
            ]
        )
        await self.session.commit()
        await self.session.refresh(run)
        return await self._hydrate(run)

    async def preview(self, case_id: UUID) -> IntegrityPreviewResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        previous = await self.repository.get_latest_run(case_id)
        previous_fps = dict(previous.fingerprints_json or {}) if previous else {}
        plan = await self.engine.plan(case, previous_fingerprints=previous_fps)
        checks, alerts, drifts = self._plan_drafts(case_id, plan)
        return IntegrityPreviewResponse(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            check_count=len(checks),
            alert_count=len(alerts),
            drift_count=len(drifts),
            metrics=self._metrics(plan.metrics),
            timeline=plan.timeline,
            fingerprints=dict(plan.provenance.get("fingerprints") or {}),
            provenance={
                k: v for k, v in plan.provenance.items() if k != "fingerprints"
            },
            engine_version=IM_ENGINE_VERSION,
            policy_version=IM_POLICY_VERSION,
            checks=checks,
            alerts=alerts,
            drifts=drifts,
            persisted=False,
        )

    async def get_latest(self, case_id: UUID) -> IntegrityRunResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            raise IntegrityRunNotFoundError("No integrity monitor run for this case.")
        return await self._hydrate(run)

    async def get_run(self, run_id: UUID) -> IntegrityRunResponse:
        run = await self.repository.get_run(run_id)
        if run is None:
            raise IntegrityRunNotFoundError("Integrity monitor run not found.")
        return await self._hydrate(run)

    async def list_alerts(self, case_id: UUID) -> IntegrityAlertListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return IntegrityAlertListResponse(items=[], total=0)
        rows = await self.repository.alerts_for_run(run.id)
        return IntegrityAlertListResponse(
            items=[self._alert_response(row) for row in rows],
            total=len(rows),
        )

    async def list_drifts(self, case_id: UUID) -> IntegrityDriftListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return IntegrityDriftListResponse(items=[], total=0)
        rows = await self.repository.drifts_for_run(run.id)
        return IntegrityDriftListResponse(
            items=[self._drift_response(row) for row in rows],
            total=len(rows),
        )

    async def history(self, case_id: UUID) -> IntegrityHistoryResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        rows = await self.repository.list_runs(case_id)
        return IntegrityHistoryResponse(
            items=[
                IntegrityHistoryItem(
                    id=row.id,
                    case_id=row.case_id,
                    status=row.status,
                    check_count=row.check_count,
                    alert_count=row.alert_count,
                    drift_count=row.drift_count,
                    metrics=self._metrics(row.metrics_json or {}),
                    engine_version=row.engine_version,
                    policy_version=row.policy_version,
                    created_at=row.created_at,
                    completed_at=row.completed_at,
                )
                for row in rows
            ],
            total=len(rows),
        )
