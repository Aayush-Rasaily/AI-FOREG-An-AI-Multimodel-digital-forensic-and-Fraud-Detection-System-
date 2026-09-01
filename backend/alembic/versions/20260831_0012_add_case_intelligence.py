"""Add case intelligence synthesis tables.

Revision ID: 20260831_0012
Revises: 20260831_0011
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0012"
down_revision = "20260831_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create case intelligence persistence tables."""

    op.create_table(
        "case_intelligence_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
                name="case_intelligence_run_status",
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
                name="case_intelligence_verdict",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("conflicts_count", sa.Integer(), nullable=False),
        sa.Column("relationships_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("coverage", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_intelligence_runs_case_id",
        "case_intelligence_runs",
        ["case_id"],
    )
    op.create_index(
        "uq_case_intelligence_runs_active",
        "case_intelligence_runs",
        ["case_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
        postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
    )
    op.create_table(
        "case_evidence_participation_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_number", sa.String(length=64), nullable=False),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("evidence_hash", sa.String(length=64), nullable=False),
        sa.Column("evidence_status", sa.String(length=32), nullable=False),
        sa.Column("coverage_status", sa.String(length=32), nullable=False),
        sa.Column("fusion_run_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "fusion_verdict",
            sa.Enum(
                "genuine",
                "suspicious",
                "potential_fraud",
                "inconclusive",
                "insufficient_evidence",
                "unavailable",
                name="case_participation_fusion_verdict",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("supporting_finding_ids", sa.JSON(), nullable=False),
        sa.Column("contradictory_finding_ids", sa.JSON(), nullable=False),
        sa.Column("conflicts_count", sa.Integer(), nullable=False),
        sa.Column("participating_modalities", sa.JSON(), nullable=False),
        sa.Column("unavailable_modalities", sa.JSON(), nullable=False),
        sa.Column("fusion_engine_version", sa.String(length=32), nullable=True),
        sa.Column("fusion_policy_version", sa.String(length=32), nullable=True),
        sa.Column("fusion_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["case_intelligence_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_evidence_participation_records_analysis_run_id",
        "case_evidence_participation_records",
        ["analysis_run_id"],
    )
    op.create_table(
        "case_relationship_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("relationship_id", sa.String(length=128), nullable=False),
        sa.Column("evidence_a_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_b_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "relationship_type",
            sa.Enum(
                "duplicate_hash",
                "reference_link",
                "comparison_link",
                "signature_verification_link",
                "shared_metadata",
                "shared_filename",
                name="case_relationship_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("supporting_reason", sa.Text(), nullable=False),
        sa.Column("source_reference", sa.String(length=256), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "detected",
                "confirmed",
                name="case_relationship_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["case_intelligence_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_relationship_records_analysis_run_id",
        "case_relationship_records",
        ["analysis_run_id"],
    )
    op.create_table(
        "case_conflict_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("conflict_id", sa.String(length=128), nullable=False),
        sa.Column(
            "conflict_type",
            sa.Enum(
                "verdict_disagreement",
                "temporal_inconsistency",
                "provenance_inconsistency",
                "metadata_inconsistency",
                "forensic_contradiction",
                "comparison_contradiction",
                "confidence_disagreement",
                name="case_conflict_type",
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
                name="case_conflict_severity",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("involved_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("involved_finding_ids", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "resolution_status",
            sa.Enum(
                "open",
                "acknowledged",
                "resolved",
                name="case_conflict_resolution_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["case_intelligence_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_conflict_records_analysis_run_id",
        "case_conflict_records",
        ["analysis_run_id"],
    )
    op.create_table(
        "case_timeline_event_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "evidence_registered",
                "evidence_processed",
                "fusion_completed",
                "comparison_completed",
                "custody_event",
                "temporal_inconsistency",
                "case_intelligence_completed",
                name="case_timeline_event_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timestamp_known", sa.Boolean(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("source_reference", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["case_intelligence_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_timeline_event_records_analysis_run_id",
        "case_timeline_event_records",
        ["analysis_run_id"],
    )


def downgrade() -> None:
    """Drop case intelligence persistence tables."""

    op.drop_index(
        "ix_case_timeline_event_records_analysis_run_id",
        table_name="case_timeline_event_records",
    )
    op.drop_table("case_timeline_event_records")
    op.drop_index(
        "ix_case_conflict_records_analysis_run_id",
        table_name="case_conflict_records",
    )
    op.drop_table("case_conflict_records")
    op.drop_index(
        "ix_case_relationship_records_analysis_run_id",
        table_name="case_relationship_records",
    )
    op.drop_table("case_relationship_records")
    op.drop_index(
        "ix_case_evidence_participation_records_analysis_run_id",
        table_name="case_evidence_participation_records",
    )
    op.drop_table("case_evidence_participation_records")
    op.drop_index(
        "uq_case_intelligence_runs_active",
        table_name="case_intelligence_runs",
    )
    op.drop_index(
        "ix_case_intelligence_runs_case_id",
        table_name="case_intelligence_runs",
    )
    op.drop_table("case_intelligence_runs")
