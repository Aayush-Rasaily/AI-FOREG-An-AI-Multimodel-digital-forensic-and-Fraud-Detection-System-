"""Service facade for Phase 9H platform validation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.models.platform_validation import (
    PlatformValidationIssue,
    PlatformValidationResult,
    PlatformValidationRun,
)
from backend.app.platform_validation.engine import (
    PlatformValidationEngine,
    build_issues,
)
from backend.app.platform_validation.exceptions import (
    PlatformValidationRunNotFoundError,
)
from backend.app.platform_validation.models import CheckStatus, RunStatus
from backend.app.platform_validation.policy import (
    PV_ENGINE_VERSION,
    PV_POLICY_VERSION,
)
from backend.app.platform_validation.repository import PlatformValidationRepository
from backend.app.platform_validation.schemas import (
    HealthReportResponse,
    PlatformValidationRunResponse,
    ReadinessResponse,
    ValidationIssueResponse,
    ValidationListResponse,
    ValidationResultResponse,
)


class PlatformValidationService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        app: FastAPI,
    ) -> None:
        self.session = session
        self.settings = settings
        self.app = app
        self.repository = PlatformValidationRepository(session)
        self.engine = PlatformValidationEngine(settings=settings, app=app)

    def _result_response(
        self,
        row: PlatformValidationResult,
    ) -> ValidationResultResponse:
        return ValidationResultResponse(
            check_key=row.check_key,
            category=row.category,
            label=row.label,
            status=row.status,
            message=row.message,
            details=dict(row.details_json or {}),
        )

    def _issue_response(
        self,
        row: PlatformValidationIssue,
    ) -> ValidationIssueResponse:
        return ValidationIssueResponse(
            check_key=row.check_key,
            category=row.category,
            severity=row.severity,
            message=row.message,
            details=dict(row.details_json or {}),
        )

    async def _hydrate(
        self,
        run: PlatformValidationRun,
    ) -> PlatformValidationRunResponse:
        results = [
            self._result_response(row)
            for row in await self.repository.results_for_run(run.id)
        ]
        issues = [
            self._issue_response(row)
            for row in await self.repository.issues_for_run(run.id)
        ]
        summary = dict(run.summary_json or {})
        return PlatformValidationRunResponse(
            id=run.id,
            status=run.status,
            readiness_score=run.readiness_score,
            readiness_level=run.readiness_level,
            check_count=run.check_count,
            pass_count=run.pass_count,
            warn_count=run.warn_count,
            fail_count=run.fail_count,
            results=results,
            issues=issues,
            health_report=dict(summary.get("health_report") or {}),
            compatibility=dict(summary.get("compatibility") or {}),
            provenance=dict(run.provenance_json or {}),
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            created_at=run.created_at,
            completed_at=run.completed_at,
            persisted=True,
        )

    def _from_plan(
        self,
        plan: Any,
        *,
        run_id: UUID | None = None,
        persisted: bool,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> PlatformValidationRunResponse:
        results = [
            ValidationResultResponse(
                check_key=item.key,
                category=item.category,
                label=item.label,
                status=item.status.value,
                message=item.message,
                details=dict(item.details),
            )
            for item in plan.outcomes
        ]
        issues = [
            ValidationIssueResponse(
                check_key=row["check_key"],
                category=row["category"],
                severity=row["severity"],
                message=row["message"],
                details=dict(row["details"]),
            )
            for row in build_issues(list(plan.outcomes))
        ]
        pass_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.PASS)
        warn_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.WARN)
        fail_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.FAIL)
        return PlatformValidationRunResponse(
            id=run_id,
            status=RunStatus.SUCCEEDED.value,
            readiness_score=plan.readiness_score,
            readiness_level=plan.readiness_level.value,
            check_count=len(plan.outcomes),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            results=results,
            issues=issues,
            health_report=dict(plan.health_report),
            compatibility=dict(plan.compatibility),
            provenance=dict(plan.provenance),
            engine_version=PV_ENGINE_VERSION,
            policy_version=PV_POLICY_VERSION,
            created_at=created_at,
            completed_at=completed_at,
            persisted=persisted,
        )

    async def validate(self) -> PlatformValidationRunResponse:
        plan = await self.engine.plan()
        pass_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.PASS)
        warn_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.WARN)
        fail_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.FAIL)
        now = datetime.now(UTC)
        run = PlatformValidationRun(
            status=RunStatus.SUCCEEDED.value,
            readiness_score=plan.readiness_score,
            readiness_level=plan.readiness_level.value,
            check_count=len(plan.outcomes),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            summary_json={
                "health_report": plan.health_report,
                "compatibility": plan.compatibility,
            },
            provenance_json=plan.provenance,
            engine_version=PV_ENGINE_VERSION,
            policy_version=PV_POLICY_VERSION,
            completed_at=now,
        )
        await self.repository.add_run(run)
        await self.repository.add_results(
            [
                PlatformValidationResult(
                    run_id=run.id,
                    check_key=item.key,
                    category=item.category,
                    label=item.label,
                    status=item.status.value,
                    message=item.message,
                    details_json=dict(item.details),
                )
                for item in plan.outcomes
            ]
        )
        await self.repository.add_issues(
            [
                PlatformValidationIssue(
                    run_id=run.id,
                    check_key=row["check_key"],
                    category=row["category"],
                    severity=row["severity"],
                    message=row["message"],
                    details_json=dict(row["details"]),
                )
                for row in build_issues(list(plan.outcomes))
            ]
        )
        await self.session.commit()
        return await self._hydrate(run)

    async def get_latest(self) -> PlatformValidationRunResponse:
        run = await self.repository.get_latest_run()
        if run is not None:
            return await self._hydrate(run)
        plan = await self.engine.plan()
        return self._from_plan(plan, persisted=False, completed_at=datetime.now(UTC))

    async def get_run(self, run_id: UUID) -> PlatformValidationRunResponse:
        run = await self.repository.get_run(run_id)
        if run is None:
            raise PlatformValidationRunNotFoundError(
                "Platform validation run not found."
            )
        return await self._hydrate(run)

    async def list_runs(self) -> ValidationListResponse:
        runs = await self.repository.list_runs()
        hydrated = [await self._hydrate(run) for run in runs]
        return ValidationListResponse(
            runs=hydrated,
            engine_version=PV_ENGINE_VERSION,
            policy_version=PV_POLICY_VERSION,
        )

    async def get_readiness(self) -> ReadinessResponse:
        latest = await self.repository.get_latest_run()
        if latest is not None:
            return ReadinessResponse(
                readiness_score=latest.readiness_score,
                readiness_level=latest.readiness_level,
                check_count=latest.check_count,
                pass_count=latest.pass_count,
                warn_count=latest.warn_count,
                fail_count=latest.fail_count,
                engine_version=latest.engine_version,
                policy_version=latest.policy_version,
                generated_at=latest.completed_at or latest.created_at,
                persisted=True,
                run_id=latest.id,
            )
        plan = await self.engine.plan()
        pass_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.PASS)
        warn_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.WARN)
        fail_count = sum(1 for item in plan.outcomes if item.status == CheckStatus.FAIL)
        return ReadinessResponse(
            readiness_score=plan.readiness_score,
            readiness_level=plan.readiness_level.value,
            check_count=len(plan.outcomes),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            engine_version=PV_ENGINE_VERSION,
            policy_version=PV_POLICY_VERSION,
            generated_at=datetime.now(UTC),
            persisted=False,
            run_id=None,
        )

    async def get_health_report(self) -> HealthReportResponse:
        latest = await self.repository.get_latest_run()
        if latest is not None:
            summary = dict(latest.summary_json or {})
            return HealthReportResponse(
                report=dict(summary.get("health_report") or {}),
                engine_version=latest.engine_version,
                policy_version=latest.policy_version,
                persisted=True,
                run_id=latest.id,
            )
        plan = await self.engine.plan()
        return HealthReportResponse(
            report=dict(plan.health_report),
            engine_version=PV_ENGINE_VERSION,
            policy_version=PV_POLICY_VERSION,
            persisted=False,
            run_id=None,
        )
