"""Add document AI and signature verification tables.

Revision ID: 20260831_0008
Revises: 20260831_0007
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0008"
down_revision = "20260831_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create document AI and signature verification persistence tables."""

    op.create_table(
        "document_analysis_runs",
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
                name="document_analysis_run_status",
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
        "ix_document_analysis_runs_evidence_id",
        "document_analysis_runs",
        ["evidence_id"],
    )
    op.create_table(
        "document_ai_findings",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("detector", sa.String(length=64), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "TAMPERING",
                "TEXT_INCONSISTENCY",
                "FONT_INCONSISTENCY",
                "LAYOUT_INCONSISTENCY",
                "LOGO",
                "METADATA",
                "REGION_ANOMALY",
                "DATE_INCONSISTENCY",
                "NUMBER_INCONSISTENCY",
                "REFERENCE_MISMATCH",
                "SIGNATURE",
                "ID_DOCUMENT",
                "CAPABILITY",
                name="document_finding_category",
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
                name="document_ai_finding_severity",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "method",
            sa.Enum(
                "classical",
                "ai",
                "reference",
                name="document_detection_method",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("model_framework", sa.String(length=32), nullable=False),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["document_analysis_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            ["artifacts.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_ai_findings_analysis_run_id",
        "document_ai_findings",
        ["analysis_run_id"],
    )
    op.create_index(
        "ix_document_ai_findings_evidence_id",
        "document_ai_findings",
        ["evidence_id"],
    )
    op.create_index(
        "ix_document_ai_findings_detector",
        "document_ai_findings",
        ["detector"],
    )
    op.create_table(
        "document_ai_finding_regions",
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
            ["document_ai_findings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_ai_finding_regions_finding_id",
        "document_ai_finding_regions",
        ["finding_id"],
    )
    op.create_table(
        "signature_verification_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reference_evidence_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("questioned_evidence_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("processing_job_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("reference_hash", sa.String(length=64), nullable=False),
        sa.Column("questioned_hash", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column(
            "verdict",
            sa.Enum(
                "MATCH",
                "NON_MATCH",
                "INCONCLUSIVE",
                "UNAVAILABLE",
                name="signature_verdict",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("device", sa.String(length=16), nullable=False),
        sa.Column("processing_time_ms", sa.Float(), nullable=True),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("localization", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["reference_evidence_id"],
            ["evidence.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["questioned_evidence_id"],
            ["evidence.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["processing_job_id"],
            ["processing_jobs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            ["artifacts.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_signature_verification_runs_questioned_evidence_id",
        "signature_verification_runs",
        ["questioned_evidence_id"],
    )


def downgrade() -> None:
    """Drop document AI and signature verification persistence tables."""

    op.drop_index(
        "ix_signature_verification_runs_questioned_evidence_id",
        table_name="signature_verification_runs",
    )
    op.drop_table("signature_verification_runs")
    op.drop_index(
        "ix_document_ai_finding_regions_finding_id",
        table_name="document_ai_finding_regions",
    )
    op.drop_table("document_ai_finding_regions")
    op.drop_index("ix_document_ai_findings_detector", table_name="document_ai_findings")
    op.drop_index(
        "ix_document_ai_findings_evidence_id",
        table_name="document_ai_findings",
    )
    op.drop_index(
        "ix_document_ai_findings_analysis_run_id",
        table_name="document_ai_findings",
    )
    op.drop_table("document_ai_findings")
    op.drop_index(
        "ix_document_analysis_runs_evidence_id",
        table_name="document_analysis_runs",
    )
    op.drop_table("document_analysis_runs")
