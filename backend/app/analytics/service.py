"""Service facade for Phase 9G analytics."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics.engine import AnalyticsEngine
from backend.app.analytics.exceptions import AnalyticsRunNotFoundError
from backend.app.analytics.models import RunStatus
from backend.app.analytics.policy import AN_ENGINE_VERSION, AN_POLICY_VERSION
from backend.app.analytics.repository import AnalyticsRepository
from backend.app.analytics.schemas import (
    AnalyticsExportResponse,
    AnalyticsRunResponse,
    AnalyticsSectionResponse,
    MetricResponse,
)
from backend.app.models.analytics import (
    AnalyticsDashboard,
    AnalyticsMetric,
    AnalyticsRun,
    AnalyticsSnapshot,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AnalyticsRepository(session)
        self.engine = AnalyticsEngine(session)

    def _metric_response(self, row: AnalyticsMetric) -> MetricResponse:
        return MetricResponse(
            key=row.metric_key,
            label=row.label,
            value=row.value,
            unit=row.unit,
            category=row.category,
            provenance=dict(row.provenance_json or {}),
        )

    async def _history_points(self) -> list[dict[str, Any]]:
        snapshots = await self.repository.list_recent_snapshots(limit=19)
        points: list[dict[str, Any]] = []
        for snap in snapshots:
            payload = dict(snap.payload_json or {})
            sections = dict(payload.get("sections") or {})
            overview = {
                item["key"]: item["value"]
                for item in (sections.get("overview") or {}).get("kpis") or []
            }
            cases = dict(sections.get("cases") or {})
            evidence = dict(sections.get("evidence") or {})
            ai = dict(sections.get("ai") or {})
            integrity = dict(sections.get("integrity") or {})
            workflow = dict(sections.get("workflow") or {})
            points.append(
                {
                    "label": snap.created_at.isoformat() if snap.created_at else "",
                    "cases_opened": overview.get(
                        "cases_opened", cases.get("opened", 0)
                    ),
                    "evidence_processed": overview.get(
                        "evidence_processed", evidence.get("processed", 0)
                    ),
                    "ai_analyses_completed": overview.get(
                        "ai_analyses_completed",
                        ai.get("analyses_completed", 0),
                    ),
                    "integrity_alerts": overview.get(
                        "integrity_alerts", integrity.get("alerts", 0)
                    ),
                    "workflow_completion_pct": overview.get(
                        "workflow_completion_pct",
                        workflow.get("workflow_completion_pct", 0),
                    ),
                }
            )
        return points

    async def _hydrate(self, run: AnalyticsRun) -> AnalyticsRunResponse:
        snapshot = await self.repository.get_snapshot_for_run(run.id)
        payload = dict(snapshot.payload_json or {}) if snapshot else {}
        metrics = [
            self._metric_response(row)
            for row in await self.repository.metrics_for_run(run.id)
        ]
        return AnalyticsRunResponse(
            id=run.id,
            status=run.status,
            metric_count=run.metric_count,
            metrics=metrics,
            sections=dict(payload.get("sections") or {}),
            trends=dict(payload.get("trends") or {}),
            dashboard=dict(payload.get("dashboard") or {}),
            provenance=dict(run.provenance_json or {}),
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            created_at=run.created_at,
            completed_at=run.completed_at,
            persisted=True,
        )

    async def refresh(self) -> AnalyticsRunResponse:
        history = await self._history_points()
        plan = await self.engine.plan(history_points=history)
        run = AnalyticsRun(
            status=RunStatus.SUCCEEDED.value,
            metric_count=len(plan.metrics),
            provenance_json=plan.provenance,
            engine_version=AN_ENGINE_VERSION,
            policy_version=AN_POLICY_VERSION,
            completed_at=datetime.now(UTC),
        )
        await self.repository.add_run(run)
        payload = {
            "sections": plan.sections,
            "trends": plan.trends,
            "dashboard": plan.dashboard,
            "metrics": [
                {
                    "key": item.key,
                    "label": item.label,
                    "value": item.value,
                    "unit": item.unit,
                    "category": item.category,
                    "provenance": item.provenance,
                }
                for item in plan.metrics
            ],
        }
        await self.repository.add_snapshot(
            AnalyticsSnapshot(run_id=run.id, payload_json=payload)
        )
        await self.repository.add_metrics(
            [
                AnalyticsMetric(
                    run_id=run.id,
                    metric_key=item.key,
                    label=item.label,
                    value=item.value,
                    unit=item.unit,
                    category=item.category,
                    provenance_json=item.provenance,
                )
                for item in plan.metrics
            ]
        )
        await self.repository.add_dashboard(
            AnalyticsDashboard(
                run_id=run.id,
                title=str(plan.dashboard.get("title") or "Investigation Analytics"),
                layout_json=plan.dashboard,
            )
        )
        await self.session.commit()
        await self.session.refresh(run)
        return await self._hydrate(run)

    async def get_latest(self) -> AnalyticsRunResponse:
        run = await self.repository.get_latest_run()
        if run is None:
            # Live compute without persist
            plan = await self.engine.plan(history_points=[])
            return AnalyticsRunResponse(
                status=RunStatus.SUCCEEDED.value,
                metric_count=len(plan.metrics),
                metrics=[
                    MetricResponse(
                        key=item.key,
                        label=item.label,
                        value=item.value,
                        unit=item.unit,
                        category=item.category,
                        provenance=item.provenance,
                    )
                    for item in plan.metrics
                ],
                sections=plan.sections,
                trends=plan.trends,
                dashboard=plan.dashboard,
                provenance=plan.provenance,
                engine_version=AN_ENGINE_VERSION,
                policy_version=AN_POLICY_VERSION,
                persisted=False,
            )
        return await self._hydrate(run)

    async def get_dashboard(self) -> dict[str, Any]:
        latest = await self.get_latest()
        return {
            **(latest.dashboard or {}),
            "engine_version": latest.engine_version,
            "policy_version": latest.policy_version,
            "run_id": str(latest.id) if latest.id else None,
            "persisted": latest.persisted,
        }

    async def get_section(self, section: str) -> AnalyticsSectionResponse:
        latest = await self.get_latest()
        data = dict((latest.sections or {}).get(section) or {})
        return AnalyticsSectionResponse(
            section=section,
            data=data,
            engine_version=latest.engine_version,
            policy_version=latest.policy_version,
            generated_at=latest.completed_at or latest.created_at,
        )

    async def export(self) -> AnalyticsExportResponse:
        latest = await self.get_latest()
        return AnalyticsExportResponse(
            format="json",
            generated_at=datetime.now(UTC),
            engine_version=latest.engine_version,
            policy_version=latest.policy_version,
            payload={
                "metrics": [item.model_dump() for item in latest.metrics],
                "sections": latest.sections,
                "trends": latest.trends,
                "dashboard": latest.dashboard,
                "provenance": latest.provenance,
                "run_id": str(latest.id) if latest.id else None,
            },
        )

    async def get_run(self, run_id: UUID) -> AnalyticsRunResponse:
        run = await self.repository.get_run(run_id)
        if run is None:
            raise AnalyticsRunNotFoundError("Analytics run not found.")
        return await self._hydrate(run)
