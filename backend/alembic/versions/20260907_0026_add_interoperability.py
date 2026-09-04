"""Add Phase 9A interoperability export/import metadata tables.

Revision ID: 20260907_0026
Revises: 20260906_0025
Create Date: 2026-09-07

Note: Spec referenced 20260901_0019, but that revision already exists for
system monitoring. This migration continues the linear chain after 8F/8G.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260907_0026"
down_revision = "20260906_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create export_jobs, import_jobs, and package_manifests."""

    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("format", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("package_version", sa.String(length=32), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("package_checksum", sa.String(length=64), nullable=True),
        sa.Column("manifest_checksum", sa.String(length=64), nullable=True),
        sa.Column("evidence_ids_json", sa.JSON(), nullable=False),
        sa.Column("report_versions_json", sa.JSON(), nullable=False),
        sa.Column("timeline_version", sa.String(length=128), nullable=True),
        sa.Column("policy_versions_json", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_export_jobs_case_id", "export_jobs", ["case_id"])
    op.create_index("ix_export_jobs_status", "export_jobs", ["status"])
    op.create_index("ix_export_jobs_created_at", "export_jobs", ["created_at"])

    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("package_version", sa.String(length=32), nullable=True),
        sa.Column("schema_version", sa.String(length=32), nullable=True),
        sa.Column("integrity_status", sa.String(length=32), nullable=False),
        sa.Column("validation_json", sa.JSON(), nullable=False),
        sa.Column("conflicts_json", sa.JSON(), nullable=False),
        sa.Column("package_checksum", sa.String(length=64), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("target_case_id", sa.Uuid(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"])
    op.create_index("ix_import_jobs_created_at", "import_jobs", ["created_at"])

    op.create_table(
        "package_manifests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("export_job_id", sa.Uuid(), nullable=False),
        sa.Column("manifest_json", sa.JSON(), nullable=False),
        sa.Column("manifest_checksum", sa.String(length=64), nullable=False),
        sa.Column("package_checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["export_job_id"], ["export_jobs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("export_job_id"),
    )
    op.create_index(
        "ix_package_manifests_export_job_id",
        "package_manifests",
        ["export_job_id"],
    )


def downgrade() -> None:
    """Drop interoperability tables."""

    op.drop_index(
        "ix_package_manifests_export_job_id", table_name="package_manifests",
    )
    op.drop_table("package_manifests")
    op.drop_index("ix_import_jobs_created_at", table_name="import_jobs")
    op.drop_index("ix_import_jobs_status", table_name="import_jobs")
    op.drop_table("import_jobs")
    op.drop_index("ix_export_jobs_created_at", table_name="export_jobs")
    op.drop_index("ix_export_jobs_status", table_name="export_jobs")
    op.drop_index("ix_export_jobs_case_id", table_name="export_jobs")
    op.drop_table("export_jobs")
