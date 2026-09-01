"""Add multimodal fusion analysis tables.

Revision ID: 20260831_0011
Revises: 20260831_0010
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0011"
down_revision = "20260831_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create multimodal fusion persistence tables."""

    op.create_table(
        "fusion_analysis_runs",
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
                "UNAVAILABLE",
                "CANCELLED",
                name="fusion_run_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column(
            "verdict",
            sa.Enum(
                "genuine",
                "suspicious",
                "potential_fraud",
                "inconclusive",
                "insufficient_evidence",
                "unavailable",
                name="fusion_verdict",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("findings_count", sa.Integer(), nullable=False),
        sa.Column("conflicts_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("modality_status", sa.JSON(), nullable=False),
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
        "ix_fusion_analysis_runs_evidence_id",
        "fusion_analysis_runs",
        ["evidence_id"],
    )
    op.create_table(
        "jury_assessment_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "forensic_analyst",
                "document_image_specialist",
                "multimedia_specialist",
                "signature_specialist",
                "consistency_analyst",
                "senior_judge",
                name="jury_member_role",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("member_name", sa.String(length=128), nullable=False),
        sa.Column(
            "verdict",
            sa.Enum(
                "genuine",
                "suspicious",
                "potential_fraud",
                "inconclusive",
                "insufficient_evidence",
                "unavailable",
                name="jury_fusion_verdict",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "availability",
            sa.Enum(
                "available",
                "unavailable",
                "not_applicable",
                "failed",
                "insufficient_evidence",
                name="jury_modality_availability",
                native_enum=False,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("supporting_finding_ids", sa.JSON(), nullable=False),
        sa.Column("contradictory_finding_ids", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["fusion_analysis_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_jury_assessment_records_analysis_run_id",
        "jury_assessment_records",
        ["analysis_run_id"],
    )
    op.create_table(
        "fusion_conflict_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("conflict_id", sa.String(length=128), nullable=False),
        sa.Column(
            "conflict_type",
            sa.Enum(
                "verdict_disagreement",
                "confidence_disagreement",
                "modality_disagreement",
                "temporal_inconsistency",
                "provenance_inconsistency",
                "contradictory_finding",
                name="fusion_conflict_type",
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
                name="fusion_conflict_severity",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("involved_finding_ids", sa.JSON(), nullable=False),
        sa.Column("involved_modalities", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "resolution_status",
            sa.Enum(
                "open",
                "acknowledged",
                "resolved",
                name="fusion_conflict_resolution_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["fusion_analysis_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fusion_conflict_records_analysis_run_id",
        "fusion_conflict_records",
        ["analysis_run_id"],
    )


def downgrade() -> None:
    """Drop multimodal fusion persistence tables."""

    op.drop_index(
        "ix_fusion_conflict_records_analysis_run_id",
        table_name="fusion_conflict_records",
    )
    op.drop_table("fusion_conflict_records")
    op.drop_index(
        "ix_jury_assessment_records_analysis_run_id",
        table_name="jury_assessment_records",
    )
    op.drop_table("jury_assessment_records")
    op.drop_index(
        "ix_fusion_analysis_runs_evidence_id",
        table_name="fusion_analysis_runs",
    )
    op.drop_table("fusion_analysis_runs")
