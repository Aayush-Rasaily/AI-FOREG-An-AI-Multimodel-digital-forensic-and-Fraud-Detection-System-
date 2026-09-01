"""Add reference comparison runs, differences, and reference evidence.

Revision ID: 20260831_0005
Revises: 20260831_0004
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0005"
down_revision = "20260831_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create reference comparison persistence tables."""

    op.create_table(
        "reference_evidence",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reference_evidence_case_id",
        "reference_evidence",
        ["case_id"],
    )
    op.create_index(
        "ix_reference_evidence_evidence_id",
        "reference_evidence",
        ["evidence_id"],
    )
    op.create_table(
        "comparison_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reference_record_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reference_evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("processing_job_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                name="comparison_run_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("differences_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["reference_record_id"],
            ["reference_evidence.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reference_evidence_id"],
            ["evidence.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processing_job_id"],
            ["processing_jobs.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comparison_runs_evidence_id",
        "comparison_runs",
        ["evidence_id"],
    )
    op.create_index(
        "ix_comparison_runs_reference_record_id",
        "comparison_runs",
        ["reference_record_id"],
    )
    op.create_table(
        "differences",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("comparison_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("matcher", sa.String(length=64), nullable=False),
        sa.Column(
            "difference_type",
            sa.Enum(
                "TEXT_CHANGED",
                "TEXT_INSERTED",
                "TEXT_REMOVED",
                "NUMBER_CHANGED",
                "DATE_CHANGED",
                "IMAGE_CHANGED",
                "LOGO_CHANGED",
                "LAYOUT_CHANGED",
                "METADATA_CHANGED",
                "PAGE_INSERTED",
                "PAGE_REMOVED",
                "SIGNATURE_CHANGED",
                "UNKNOWN",
                name="difference_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "INFO",
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="difference_severity",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("original_value", sa.Text(), nullable=True),
        sa.Column("submitted_value", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["comparison_run_id"],
            ["comparison_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_differences_comparison_run_id",
        "differences",
        ["comparison_run_id"],
    )
    op.create_index("ix_differences_evidence_id", "differences", ["evidence_id"])
    op.create_index("ix_differences_matcher", "differences", ["matcher"])
    op.create_table(
        "difference_regions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("difference_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("frame_number", sa.Integer(), nullable=True),
        sa.Column("polygon", sa.JSON(), nullable=True),
        sa.Column("normalized_x", sa.Float(), nullable=True),
        sa.Column("normalized_y", sa.Float(), nullable=True),
        sa.Column("normalized_width", sa.Float(), nullable=True),
        sa.Column("normalized_height", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["difference_id"],
            ["differences.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_difference_regions_difference_id",
        "difference_regions",
        ["difference_id"],
    )


def downgrade() -> None:
    """Remove reference comparison persistence tables."""

    op.drop_index(
        "ix_difference_regions_difference_id",
        table_name="difference_regions",
    )
    op.drop_table("difference_regions")
    op.drop_index("ix_differences_matcher", table_name="differences")
    op.drop_index("ix_differences_evidence_id", table_name="differences")
    op.drop_index("ix_differences_comparison_run_id", table_name="differences")
    op.drop_table("differences")
    op.drop_index(
        "ix_comparison_runs_reference_record_id",
        table_name="comparison_runs",
    )
    op.drop_index("ix_comparison_runs_evidence_id", table_name="comparison_runs")
    op.drop_table("comparison_runs")
    op.drop_index("ix_reference_evidence_evidence_id", table_name="reference_evidence")
    op.drop_index("ix_reference_evidence_case_id", table_name="reference_evidence")
    op.drop_table("reference_evidence")
