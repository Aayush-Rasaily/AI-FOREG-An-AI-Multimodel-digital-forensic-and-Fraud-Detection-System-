"""Create processing job and derived artifact tables.

Revision ID: 20260831_0002
Revises: 20260831_0001
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0002"
down_revision = "20260831_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Phase 4 processing structures."""

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "job_type",
            sa.Enum(
                "INGESTION_INSPECTION",
                "METADATA_EXTRACTION",
                "PREVIEW_GENERATION",
                "FILE_CLASSIFICATION",
                "PREPROCESSING",
                name="processing_job_type",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
                name="processing_job_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message_safe", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_processing_jobs_evidence_id",
        "processing_jobs",
        ["evidence_id"],
    )
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_index(
        "ix_processing_jobs_created_at",
        "processing_jobs",
        ["created_at"],
    )
    op.create_index(
        "uq_processing_jobs_active",
        "processing_jobs",
        ["evidence_id", "job_type"],
        unique=True,
        postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
        sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
    )

    op.create_table(
        "artifacts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "artifact_type",
            sa.Enum(
                "PREVIEW",
                "THUMBNAIL",
                "METADATA",
                "CLASSIFICATION",
                "DERIVATIVE",
                name="artifact_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_artifacts_storage_key"),
    )
    op.create_index("ix_artifacts_evidence_id", "artifacts", ["evidence_id"])
    op.create_index("ix_artifacts_artifact_type", "artifacts", ["artifact_type"])
    op.create_index("ix_artifacts_created_at", "artifacts", ["created_at"])
    op.create_index("ix_artifacts_sha256_hash", "artifacts", ["sha256_hash"])


def downgrade() -> None:
    """Remove Phase 4 processing structures."""

    op.drop_index("ix_artifacts_sha256_hash", table_name="artifacts")
    op.drop_index("ix_artifacts_created_at", table_name="artifacts")
    op.drop_index("ix_artifacts_artifact_type", table_name="artifacts")
    op.drop_index("ix_artifacts_evidence_id", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("uq_processing_jobs_active", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_created_at", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_status", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_evidence_id", table_name="processing_jobs")
    op.drop_table("processing_jobs")
