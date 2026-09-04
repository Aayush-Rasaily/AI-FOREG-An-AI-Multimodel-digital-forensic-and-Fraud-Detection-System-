"""Persistence helpers for interoperability jobs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.interoperability import (
    ExportJob,
    ImportJob,
    PackageManifestRecord,
)


class InteropRepository:
    """CRUD helpers for export/import metadata."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entity: object) -> None:
        self.session.add(entity)

    async def get_export(self, export_id: UUID) -> ExportJob | None:
        return await self.session.get(ExportJob, export_id)

    async def get_import(self, import_id: UUID) -> ImportJob | None:
        return await self.session.get(ImportJob, import_id)

    async def list_exports(
        self, *, case_id: UUID | None = None, limit: int = 100,
    ) -> list[ExportJob]:
        stmt = select(ExportJob).order_by(ExportJob.created_at.desc()).limit(limit)
        if case_id is not None:
            stmt = (
                select(ExportJob)
                .where(ExportJob.case_id == case_id)
                .order_by(ExportJob.created_at.desc())
                .limit(limit)
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_imports(self, *, limit: int = 100) -> list[ImportJob]:
        stmt = select(ImportJob).order_by(ImportJob.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_manifest_for_export(
        self, export_id: UUID,
    ) -> PackageManifestRecord | None:
        stmt = select(PackageManifestRecord).where(
            PackageManifestRecord.export_job_id == export_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
