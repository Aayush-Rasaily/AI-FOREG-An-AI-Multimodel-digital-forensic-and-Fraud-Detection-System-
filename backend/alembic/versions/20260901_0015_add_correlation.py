"""Add cross-evidence correlation tables.

Revision ID: 20260901_0015
Revises: 20260901_0014
Create Date: 2026-09-01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0015"
down_revision = "20260901_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create correlation persistence tables."""

    op.create_table(
        "correlation_analysis_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                name="correlation_run_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("correlation_count", sa.Integer(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_correlation_analysis_runs_case_id",
        "correlation_analysis_runs",
        ["case_id"],
    )
    op.create_index(
        "uq_correlation_analysis_runs_active",
        "correlation_analysis_runs",
        ["case_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
        postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
    )
    op.create_table(
        "evidence_correlations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("left_evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("right_evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=256), nullable=False),
        sa.Column(
            "correlation_type",
            sa.Enum(
                "same_hash",
                "same_email",
                "same_phone",
                "same_device",
                "same_camera",
                "same_signature",
                "same_logo",
                "same_qr",
                "same_audio_speaker",
                "same_location",
                "same_document",
                "similar_filename",
                "temporal_overlap",
                "shared_metadata",
                "shared_identifier",
                name="correlation_type",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("supporting_findings", sa.JSON(), nullable=False),
        sa.Column("supporting_metadata", sa.JSON(), nullable=False),
        sa.Column("supporting_entities", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["correlation_analysis_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["left_evidence_id"],
            ["evidence.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["right_evidence_id"],
            ["evidence.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evidence_correlations_analysis_run_id",
        "evidence_correlations",
        ["analysis_run_id"],
    )
    op.create_index(
        "ix_evidence_correlations_case_id",
        "evidence_correlations",
        ["case_id"],
    )
    op.create_index(
        "ix_evidence_correlations_left_evidence_id",
        "evidence_correlations",
        ["left_evidence_id"],
    )
    op.create_index(
        "ix_evidence_correlations_right_evidence_id",
        "evidence_correlations",
        ["right_evidence_id"],
    )
    op.create_index(
        "uq_evidence_correlations_pair_type",
        "evidence_correlations",
        [
            "analysis_run_id",
            "left_evidence_id",
            "right_evidence_id",
            "correlation_type",
        ],
        unique=True,
    )
    op.create_table(
        "correlation_support_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("correlation_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("support_kind", sa.String(length=64), nullable=False),
        sa.Column("support_ref", sa.String(length=256), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["correlation_id"],
            ["evidence_correlations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_correlation_support_records_correlation_id",
        "correlation_support_records",
        ["correlation_id"],
    )


def downgrade() -> None:
    """Drop correlation persistence tables."""

    op.drop_index(
        "ix_correlation_support_records_correlation_id",
        table_name="correlation_support_records",
    )
    op.drop_table("correlation_support_records")
    op.drop_index(
        "uq_evidence_correlations_pair_type",
        table_name="evidence_correlations",
    )
    op.drop_index(
        "ix_evidence_correlations_right_evidence_id",
        table_name="evidence_correlations",
    )
    op.drop_index(
        "ix_evidence_correlations_left_evidence_id",
        table_name="evidence_correlations",
    )
    op.drop_index(
        "ix_evidence_correlations_case_id",
        table_name="evidence_correlations",
    )
    op.drop_index(
        "ix_evidence_correlations_analysis_run_id",
        table_name="evidence_correlations",
    )
    op.drop_table("evidence_correlations")
    op.drop_index(
        "uq_correlation_analysis_runs_active",
        table_name="correlation_analysis_runs",
    )
    op.drop_index(
        "ix_correlation_analysis_runs_case_id",
        table_name="correlation_analysis_runs",
    )
    op.drop_table("correlation_analysis_runs")
