"""Analytics planning engine."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics.aggregation import collect_raw_counts
from backend.app.analytics.dashboards import build_dashboard, build_sections
from backend.app.analytics.metrics import build_metrics
from backend.app.analytics.models import AnalyticsPlan, RunStatus
from backend.app.analytics.policy import (
    AN_ENGINE_VERSION,
    AN_POLICY_VERSION,
    TREND_HISTORY_LIMIT,
)


class AnalyticsEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def plan(
        self,
        *,
        history_points: list[dict[str, Any]] | None = None,
    ) -> AnalyticsPlan:
        raw = await collect_raw_counts(self.session)
        metrics = build_metrics(raw)
        sections = build_sections(metrics, raw)
        trends = self._build_trends(history_points or [], raw)
        dashboard = build_dashboard(sections, trends)
        return AnalyticsPlan(
            status=RunStatus.SUCCEEDED,
            metrics=metrics,
            sections=sections,
            trends=trends,
            dashboard=dashboard,
            provenance={
                "engine_version": AN_ENGINE_VERSION,
                "policy_version": AN_POLICY_VERSION,
                "aggregation": "deterministic_sql_counts",
                "forecasting": False,
                "machine_learning": False,
            },
        )

    def _build_trends(
        self,
        history: list[dict[str, Any]],
        current: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        """Build deterministic series from prior snapshots + current point."""

        keys = [
            "cases_opened",
            "evidence_processed",
            "ai_analyses_completed",
            "integrity_alerts",
            "workflow_completion_pct",
        ]
        series: dict[str, list[dict[str, Any]]] = {key: [] for key in keys}
        points = list(history[-TREND_HISTORY_LIMIT:])
        points.append(
            {
                "label": "current",
                **{key: current.get(key, 0) for key in keys},
            }
        )
        for idx, point in enumerate(points):
            for key in keys:
                series[key].append(
                    {
                        "index": idx,
                        "label": str(point.get("label") or f"t{idx}"),
                        "value": float(point.get(key) or 0),
                    }
                )
        return series
