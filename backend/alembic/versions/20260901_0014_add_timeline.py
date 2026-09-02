"""Add investigation timeline engine tables.

Revision ID: 20260901_0014
Revises: 20260831_0013
Create Date: 2026-09-01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0014"
down_revision = "20260831_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create investigation timeline persistence tables."""

    op.create_table(
        "investigation_timelines",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                name="timeline_run_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("conflicts_count", sa.Integer(), nullable=False),
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
        "ix_investigation_timelines_case_id",
        "investigation_timelines",
        ["case_id"],
    )
    op.create_index(
        "uq_investigation_timelines_active",
        "investigation_timelines",
        ["case_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
        postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
    )
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("timeline_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "evidence_uploaded",
                "evidence_updated",
                "processing_queued",
                "processing_started",
                "processing_completed",
                "extraction_completed",
                "custody_event",
                "forensic_analysis_completed",
                "image_ai_completed",
                "document_ai_completed",
                "signature_ai_completed",
                "video_ai_completed",
                "audio_ai_completed",
                "fusion_completed",
                "case_intelligence_completed",
                "report_generated",
                "metadata_timestamp",
                "timestamp_missing",
                name="timeline_event_type",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("normalized_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("uncertainty_ms", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("supporting_artifacts", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["timeline_id"],
            ["investigation_timelines.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_timeline_events_timeline_id", "timeline_events", ["timeline_id"]
    )
    op.create_index("ix_timeline_events_case_id", "timeline_events", ["case_id"])
    op.create_index(
        "ix_timeline_events_evidence_id", "timeline_events", ["evidence_id"]
    )
    op.create_index(
        "ix_timeline_events_event_id",
        "timeline_events",
        ["timeline_id", "event_id"],
        unique=True,
    )
    op.create_table(
        "timeline_conflicts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("timeline_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("conflict_id", sa.String(length=128), nullable=False),
        sa.Column(
            "conflict_type",
            sa.Enum(
                "multiple_timestamps",
                "filesystem_before_exif",
                "future_timestamp",
                "clock_drift",
                "timezone_mismatch",
                "duplicate_event",
                name="timeline_conflict_type",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("involved_event_ids", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["timeline_id"],
            ["investigation_timelines.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_timeline_conflicts_timeline_id",
        "timeline_conflicts",
        ["timeline_id"],
    )
    op.create_index("ix_timeline_conflicts_case_id", "timeline_conflicts", ["case_id"])
    op.create_index(
        "ix_timeline_conflicts_conflict_id",
        "timeline_conflicts",
        ["timeline_id", "conflict_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop investigation timeline persistence tables."""

    op.drop_index("ix_timeline_conflicts_conflict_id", table_name="timeline_conflicts")
    op.drop_index("ix_timeline_conflicts_case_id", table_name="timeline_conflicts")
    op.drop_index("ix_timeline_conflicts_timeline_id", table_name="timeline_conflicts")
    op.drop_table("timeline_conflicts")
    op.drop_index("ix_timeline_events_event_id", table_name="timeline_events")
    op.drop_index("ix_timeline_events_evidence_id", table_name="timeline_events")
    op.drop_index("ix_timeline_events_case_id", table_name="timeline_events")
    op.drop_index("ix_timeline_events_timeline_id", table_name="timeline_events")
    op.drop_table("timeline_events")
    op.drop_index(
        "uq_investigation_timelines_active",
        table_name="investigation_timelines",
    )
    op.drop_index(
        "ix_investigation_timelines_case_id", table_name="investigation_timelines"
    )
    op.drop_table("investigation_timelines")
