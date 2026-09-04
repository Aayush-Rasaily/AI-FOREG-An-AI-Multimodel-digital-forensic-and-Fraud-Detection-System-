"""Service facade for operational monitoring."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.monitoring import (
    AuditStatistics,
    MonitoringSnapshot,
    SystemHealthRecord,
)
from backend.app.monitoring.engine import MonitoringEngine
from backend.app.monitoring.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.monitoring.repository import MonitoringRepository
from backend.app.monitoring.schemas import (
    MonitoringDashboardResponse,
    MonitoringRefreshResponse,
    MonitoringSectionResponse,
    SystemHealthResponse,
)


class MonitoringService:
    """Compute and serve operational monitoring analytics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MonitoringRepository(session)
        self.engine = MonitoringEngine(session)

    async def _payload(self) -> dict:
        latest = await self.repository.get_latest_snapshot()
        if latest is not None:
            data = dict(latest.payload_json)
            data["snapshot_id"] = latest.id
            return data
        return await self.engine.compute()

    async def get_dashboard(self) -> MonitoringDashboardResponse:
        payload = await self._payload()
        return MonitoringDashboardResponse(**payload)

    async def get_system_health(self) -> SystemHealthResponse:
        payload = await self._payload()
        health = payload["system_health"]
        return SystemHealthResponse(**health)

    async def get_processing(self) -> MonitoringSectionResponse:
        payload = await self._payload()
        return MonitoringSectionResponse(
            data=payload["processing"],
            generated_at=payload["generated_at"],
            engine_version=payload["engine_version"],
            policy_version=payload["policy_version"],
        )

    async def get_ai(self) -> MonitoringSectionResponse:
        payload = await self._payload()
        return MonitoringSectionResponse(
            data=payload["ai"],
            generated_at=payload["generated_at"],
            engine_version=payload["engine_version"],
            policy_version=payload["policy_version"],
        )

    async def get_api(self) -> MonitoringSectionResponse:
        payload = await self._payload()
        return MonitoringSectionResponse(
            data=payload["api"],
            generated_at=payload["generated_at"],
            engine_version=payload["engine_version"],
            policy_version=payload["policy_version"],
        )

    async def get_activity(self) -> MonitoringSectionResponse:
        payload = await self._payload()
        return MonitoringSectionResponse(
            data=payload["activity"],
            generated_at=payload["generated_at"],
            engine_version=payload["engine_version"],
            policy_version=payload["policy_version"],
        )

    async def get_bottlenecks(self) -> MonitoringSectionResponse:
        payload = await self._payload()
        return MonitoringSectionResponse(
            data=payload["bottlenecks"],
            generated_at=payload["generated_at"],
            engine_version=payload["engine_version"],
            policy_version=payload["policy_version"],
        )

    async def get_audit_summary(self) -> MonitoringSectionResponse:
        payload = await self._payload()
        return MonitoringSectionResponse(
            data=payload["audit_summary"],
            generated_at=payload["generated_at"],
            engine_version=payload["engine_version"],
            policy_version=payload["policy_version"],
        )

    async def refresh(self) -> MonitoringRefreshResponse:
        payload = await self.engine.compute()
        snapshot = MonitoringSnapshot(
            generated_at=datetime.now(UTC),
            payload_json=payload,
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
        )
        await self.repository.add_snapshot(snapshot)
        health = SystemHealthRecord(
            assessed_at=datetime.now(UTC),
            snapshot_id=snapshot.id,
            status=str(payload["system_health"]["status"]),
            details_json=payload["system_health"],
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
        )
        await self.repository.add_health_record(health)
        audit_stats = AuditStatistics(
            generated_at=datetime.now(UTC),
            snapshot_id=snapshot.id,
            summary_json=payload["audit_summary"],
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
        )
        await self.repository.add_audit_statistics(audit_stats)
        await self.session.commit()
        return MonitoringRefreshResponse(
            snapshot_id=snapshot.id,
            health_record_id=health.id,
            audit_statistics_id=audit_stats.id,
            generated_at=snapshot.generated_at,
            system_health=payload["system_health"],
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
        )
