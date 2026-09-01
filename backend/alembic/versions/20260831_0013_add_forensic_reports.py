"""Add forensic investigation report tables.

Revision ID: 20260831_0013
Revises: 20260831_0012
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0013"
down_revision = "20260831_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create forensic report persistence tables."""

    op.create_table(
        "forensic_reports",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "GENERATING",
                "COMPLETED",
                "FAILED",
                name="forensic_report_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("report_version", sa.String(length=32), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("fusion_policy_version", sa.String(length=32), nullable=True),
        sa.Column(
            "case_intelligence_policy_version",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column("case_intelligence_run_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("evidence_hashes", sa.JSON(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("pdf_storage_key", sa.String(length=1024), nullable=True),
        sa.Column("pdf_sha256", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["case_intelligence_run_id"],
            ["case_intelligence_runs.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_forensic_reports_case_id",
        "forensic_reports",
        ["case_id"],
    )
    op.create_index(
        "uq_forensic_reports_active",
        "forensic_reports",
        ["case_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('QUEUED', 'GENERATING')"),
        postgresql_where=sa.text("status IN ('QUEUED', 'GENERATING')"),
    )


def downgrade() -> None:
    """Drop forensic report persistence tables."""

    op.drop_index("uq_forensic_reports_active", table_name="forensic_reports")
    op.drop_index("ix_forensic_reports_case_id", table_name="forensic_reports")
    op.drop_table("forensic_reports")
