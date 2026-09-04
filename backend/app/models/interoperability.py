"""SQLAlchemy models for interoperability export/import metadata."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from backend.app.infrastructure.database.base import Base


class ExportJob(Base):
    """Metadata for a generated investigation export package."""

    __tablename__ = "export_jobs"
    __table_args__ = (
        Index("ix_export_jobs_case_id", "case_id"),
        Index("ix_export_jobs_status", "status"),
        Index("ix_export_jobs_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    case_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    format: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    package_version: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    package_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manifest_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_ids_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    report_versions_json: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list,
    )
    timeline_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    policy_versions_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )


class ImportJob(Base):
    """Metadata for a validated (or rejected) investigation import."""

    __tablename__ = "import_jobs"
    __table_args__ = (
        Index("ix_import_jobs_status", "status"),
        Index("ix_import_jobs_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    package_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    schema_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    integrity_status: Mapped[str] = mapped_column(String(32), nullable=False)
    validation_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    conflicts_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    package_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    target_case_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )


class PackageManifestRecord(Base):
    """Persisted manifest metadata for an export (no file duplication)."""

    __tablename__ = "package_manifests"
    __table_args__ = (
        Index("ix_package_manifests_export_job_id", "export_job_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4,
    )
    export_job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("export_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    manifest_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    manifest_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    package_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
