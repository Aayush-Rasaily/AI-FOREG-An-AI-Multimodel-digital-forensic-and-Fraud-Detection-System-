"""Application service for digital evidence exchange."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.storage import StorageService
from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.core.config import Settings
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.interoperability.archive import (
    build_deterministic_zip,
    write_deterministic_zip,
)
from backend.app.interoperability.engine import InteropEngine
from backend.app.interoperability.exceptions import (
    ExportNotFoundError,
    ImportNotFoundError,
    UnsupportedFormatError,
)
from backend.app.interoperability.exporters import (
    export_csv_package,
    export_json_package,
    export_manifest_only,
    export_pdf_bundle,
    export_zip_evidence,
)
from backend.app.interoperability.hashing import sha256_bytes
from backend.app.interoperability.importers import (
    load_package_members,
    run_import_validation,
)
from backend.app.interoperability.policy import (
    INTEROP_ENGINE_VERSION,
    INTEROP_POLICY_VERSION,
    PACKAGE_SCHEMA_VERSION,
    PACKAGE_VERSION,
    SUPPORTED_EXPORT_FORMATS,
    ExportFormat,
    JobStatus,
)
from backend.app.interoperability.repository import InteropRepository
from backend.app.interoperability.schemas import (
    ExportJobListResponse,
    ExportJobResponse,
    ImportJobListResponse,
    ImportJobResponse,
    ManifestResponse,
)
from backend.app.models.interoperability import (
    ExportJob,
    ImportJob,
    PackageManifestRecord,
)


def _actor_name(principal: AuthenticatedPrincipal | None) -> str | None:
    if principal is None:
        return None
    return principal.username


class InteroperabilityService:
    """Export / import investigation packages with provenance."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        storage: StorageService,
    ) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage
        self.repository = InteropRepository(session)
        self.engine = InteropEngine(session)

    def _packages_root(self) -> Path:
        root = Path(self.settings.storage_root) / "interop" / "packages"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _export_response(self, job: ExportJob) -> ExportJobResponse:
        return ExportJobResponse(
            id=job.id,
            case_id=job.case_id,
            format=job.format,
            status=job.status,
            package_version=job.package_version,
            schema_version=job.schema_version,
            storage_key=job.storage_key,
            package_checksum=job.package_checksum,
            manifest_checksum=job.manifest_checksum,
            evidence_ids=[str(item) for item in (job.evidence_ids_json or [])],
            report_versions=[str(item) for item in (job.report_versions_json or [])],
            timeline_version=job.timeline_version,
            policy_versions=dict(job.policy_versions_json or {}),
            error_message=job.error_message,
            created_by=job.created_by,
            engine_version=job.engine_version,
            policy_version=job.policy_version,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )

    def _import_response(self, job: ImportJob) -> ImportJobResponse:
        return ImportJobResponse(
            id=job.id,
            source_filename=job.source_filename,
            status=job.status,
            package_version=job.package_version,
            schema_version=job.schema_version,
            integrity_status=job.integrity_status,
            validation=dict(job.validation_json or {}),
            conflicts=[str(item) for item in (job.conflicts_json or [])],
            package_checksum=job.package_checksum,
            storage_key=job.storage_key,
            target_case_id=job.target_case_id,
            error_message=job.error_message,
            created_by=job.created_by,
            engine_version=job.engine_version,
            policy_version=job.policy_version,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )

    async def _read_blob(self, storage_key: str | None) -> bytes | None:
        if not storage_key:
            return None
        try:
            async with self.storage.open(storage_key) as handle:
                return handle.read()
        except Exception:  # noqa: BLE001 — optional binary inclusion
            return None

    async def export_case(
        self,
        case_id: UUID,
        *,
        format_name: str,
        evidence_ids: list[UUID] | None,
        include_binaries: bool,
        principal: AuthenticatedPrincipal | None,
    ) -> ExportJobResponse:
        if format_name not in SUPPORTED_EXPORT_FORMATS:
            raise UnsupportedFormatError(
                f"Unsupported export format: {format_name}"
            )
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")

        job = ExportJob(
            case_id=case_id,
            format=format_name,
            status=JobStatus.RUNNING.value,
            package_version=PACKAGE_VERSION,
            schema_version=PACKAGE_SCHEMA_VERSION,
            evidence_ids_json=[str(item) for item in (evidence_ids or [])],
            report_versions_json=[],
            policy_versions_json={},
            created_by=_actor_name(principal),
            engine_version=INTEROP_ENGINE_VERSION,
            policy_version=INTEROP_POLICY_VERSION,
        )
        await self.repository.add(job)
        await self.session.flush()

        # Deterministic created_at for manifest (documented as package field).
        created_at = (
            job.created_at.astimezone(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        try:
            snapshot = await self.engine.build_snapshot(
                case, evidence_ids=evidence_ids,
            )
            evidence_blobs: dict[str, bytes] = {}
            if include_binaries or format_name in {
                ExportFormat.ZIP_EVIDENCE.value,
                ExportFormat.JSON_PACKAGE.value,
            }:
                if include_binaries or format_name == ExportFormat.ZIP_EVIDENCE.value:
                    for item in snapshot.evidence:
                        blob = await self._read_blob(item.get("storage_key"))
                        if blob is not None:
                            evidence_blobs[str(item["id"])] = blob

            pdf_blobs: dict[str, bytes] = {}
            if format_name == ExportFormat.PDF_BUNDLE.value:
                for report in snapshot.reports:
                    blob = await self._read_blob(report.get("pdf_storage_key"))
                    if blob is not None:
                        pdf_blobs[str(report["id"])] = blob

            if format_name == ExportFormat.JSON_PACKAGE.value:
                files, manifest = export_json_package(
                    snapshot,
                    created_at=created_at,
                    evidence_blobs=evidence_blobs if include_binaries else None,
                )
            elif format_name == ExportFormat.CSV.value:
                files, manifest = export_csv_package(
                    snapshot, created_at=created_at,
                )
            elif format_name == ExportFormat.PDF_BUNDLE.value:
                files, manifest = export_pdf_bundle(
                    snapshot, created_at=created_at, pdf_blobs=pdf_blobs,
                )
            elif format_name == ExportFormat.ZIP_EVIDENCE.value:
                files, manifest = export_zip_evidence(
                    snapshot,
                    created_at=created_at,
                    evidence_blobs=evidence_blobs,
                )
            else:
                files, manifest = export_manifest_only(
                    snapshot, created_at=created_at,
                )

            archive_name = f"{job.id}.zip"
            storage_rel = f"interop/packages/{archive_name}"
            archive_path = self._packages_root() / archive_name
            write_deterministic_zip(archive_path, files)

            provenance = manifest.get("provenance") or {}
            job.status = JobStatus.COMPLETED.value
            job.storage_key = storage_rel
            job.package_checksum = manifest.get("package_checksum")
            job.manifest_checksum = manifest.get("manifest_checksum")
            job.evidence_ids_json = list(provenance.get("evidence_included") or [])
            job.report_versions_json = list(provenance.get("report_versions") or [])
            job.timeline_version = provenance.get("timeline_version")
            job.policy_versions_json = dict(manifest.get("policy_versions") or {})
            job.completed_at = datetime.now(UTC)

            await self.repository.add(
                PackageManifestRecord(
                    export_job_id=job.id,
                    manifest_json=manifest,
                    manifest_checksum=str(manifest.get("manifest_checksum")),
                    package_checksum=str(manifest.get("package_checksum")),
                )
            )
            await self.session.commit()
            await self.session.refresh(job)
            return self._export_response(job)
        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.FAILED.value
            job.error_message = f"{type(exc).__name__}: {exc}"
            job.completed_at = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(job)
            return self._export_response(job)

    async def list_exports(
        self, *, case_id: UUID | None = None,
    ) -> ExportJobListResponse:
        rows = await self.repository.list_exports(case_id=case_id)
        items = [self._export_response(row) for row in rows]
        return ExportJobListResponse(items=items, total=len(items))

    async def get_export(self, export_id: UUID) -> ExportJobResponse:
        job = await self.repository.get_export(export_id)
        if job is None:
            raise ExportNotFoundError("Export job not found.")
        return self._export_response(job)

    async def get_manifest(self, export_id: UUID) -> ManifestResponse:
        job = await self.repository.get_export(export_id)
        if job is None:
            raise ExportNotFoundError("Export job not found.")
        record = await self.repository.get_manifest_for_export(export_id)
        if record is None:
            raise ExportNotFoundError("Export manifest not found.")
        return ManifestResponse(
            export_job_id=export_id,
            manifest=dict(record.manifest_json),
            manifest_checksum=record.manifest_checksum,
            package_checksum=record.package_checksum,
        )

    async def download_export(self, export_id: UUID) -> tuple[Path, str, str]:
        """Return (path, filename, media_type) for a completed export."""

        job = await self.repository.get_export(export_id)
        if job is None or not job.storage_key:
            raise ExportNotFoundError("Export package not found.")
        path = Path(self.settings.storage_root) / job.storage_key
        if not path.is_file():
            raise ExportNotFoundError("Export archive file is missing.")
        return path, f"export-{export_id}.zip", "application/zip"

    async def import_package(
        self,
        *,
        filename: str,
        payload: bytes,
        principal: AuthenticatedPrincipal | None,
    ) -> ImportJobResponse:
        job = ImportJob(
            source_filename=filename,
            status=JobStatus.RUNNING.value,
            integrity_status="PENDING",
            validation_json={},
            conflicts_json=[],
            created_by=_actor_name(principal),
            engine_version=INTEROP_ENGINE_VERSION,
            policy_version=INTEROP_POLICY_VERSION,
        )
        await self.repository.add(job)
        await self.session.flush()

        import_name = f"import-{job.id}.zip"
        import_path = self._packages_root() / import_name
        import_path.write_bytes(payload)
        job.storage_key = f"interop/packages/{import_name}"
        job.package_checksum = sha256_bytes(payload)

        try:
            members = load_package_members(import_path)
            numbers, ids = await self.engine.existing_case_identifiers()
            result = run_import_validation(
                members=members,
                existing_case_numbers=numbers,
                existing_case_ids=ids,
            )
            job.validation_json = {
                "valid": result.valid,
                "integrity_status": result.integrity_status,
                "findings": [
                    {
                        "check": item.check,
                        "status": item.status,
                        "message": item.message,
                    }
                    for item in result.findings
                ],
                "package_version": result.package_version,
                "schema_version": result.schema_version,
            }
            job.conflicts_json = list(result.conflicts)
            job.package_version = result.package_version
            job.schema_version = result.schema_version
            job.integrity_status = result.integrity_status
            job.completed_at = datetime.now(UTC)

            if result.integrity_status == "CONFLICTS":
                job.status = JobStatus.CONFLICTS.value
                # Never overwrite existing investigations automatically.
            elif not result.valid:
                job.status = JobStatus.INVALID.value
            else:
                job.status = JobStatus.COMPLETED.value
                # Validation-only success: package accepted, no auto-create.

            await self.session.commit()
            await self.session.refresh(job)
            return self._import_response(job)
        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.FAILED.value
            job.integrity_status = "FAILED"
            job.error_message = f"{type(exc).__name__}: {exc}"
            job.completed_at = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(job)
            return self._import_response(job)

    async def list_imports(self) -> ImportJobListResponse:
        rows = await self.repository.list_imports()
        items = [self._import_response(row) for row in rows]
        return ImportJobListResponse(items=items, total=len(items))

    async def get_import(self, import_id: UUID) -> ImportJobResponse:
        job = await self.repository.get_import(import_id)
        if job is None:
            raise ImportNotFoundError("Import job not found.")
        return self._import_response(job)

    @staticmethod
    def build_archive_bytes(files: dict[str, bytes]) -> bytes:
        """Expose deterministic ZIP builder for tests."""

        return build_deterministic_zip(files)
