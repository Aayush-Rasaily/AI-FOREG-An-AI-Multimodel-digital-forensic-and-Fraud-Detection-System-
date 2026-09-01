"""Add AI image forensic analysis tables.

Revision ID: 20260831_0007
Revises: 20260831_0006
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0007"
down_revision = "20260831_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create AI image analysis persistence tables."""

    op.create_table(
        "image_analysis_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("processing_job_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                name="image_analysis_run_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("device", sa.String(length=16), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("findings_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["processing_job_id"],
            ["processing_jobs.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_image_analysis_runs_evidence_id",
        "image_analysis_runs",
        ["evidence_id"],
    )
    op.create_table(
        "image_ai_findings",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("detector", sa.String(length=64), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "AI_GENERATED",
                "DEEPFAKE",
                "MANIPULATION",
                "LOGO",
                "ID_DOCUMENT",
                "IMAGE",
                name="image_finding_category",
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
                name="image_ai_finding_severity",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("model_framework", sa.String(length=32), nullable=False),
        sa.Column("heatmap_artifact_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("mask_artifact_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["image_analysis_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["heatmap_artifact_id"],
            ["artifacts.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["mask_artifact_id"],
            ["artifacts.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_image_ai_findings_analysis_run_id",
        "image_ai_findings",
        ["analysis_run_id"],
    )
    op.create_index(
        "ix_image_ai_findings_evidence_id",
        "image_ai_findings",
        ["evidence_id"],
    )
    op.create_index(
        "ix_image_ai_findings_detector",
        "image_ai_findings",
        ["detector"],
    )
    op.create_table(
        "image_ai_finding_regions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("finding_id", sa.Uuid(as_uuid=True), nullable=False),
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
            ["finding_id"],
            ["image_ai_findings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_image_ai_finding_regions_finding_id",
        "image_ai_finding_regions",
        ["finding_id"],
    )


def downgrade() -> None:
    """Drop AI image analysis persistence tables."""

    op.drop_index(
        "ix_image_ai_finding_regions_finding_id",
        table_name="image_ai_finding_regions",
    )
    op.drop_table("image_ai_finding_regions")
    op.drop_index("ix_image_ai_findings_detector", table_name="image_ai_findings")
    op.drop_index("ix_image_ai_findings_evidence_id", table_name="image_ai_findings")
    op.drop_index(
        "ix_image_ai_findings_analysis_run_id",
        table_name="image_ai_findings",
    )
    op.drop_table("image_ai_findings")
    op.drop_index(
        "ix_image_analysis_runs_evidence_id",
        table_name="image_analysis_runs",
    )
    op.drop_table("image_analysis_runs")
