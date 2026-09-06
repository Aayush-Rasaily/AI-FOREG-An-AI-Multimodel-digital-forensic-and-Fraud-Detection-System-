"""Alembic migration for Phase 10C performance indexes.

Revision ID: 20260915_0034
Revises: 20260914_0033

Additive indexes only — no schema or behavior changes.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "20260915_0034"
down_revision: str | Sequence[str] | None = "20260914_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_evidence_case_id_created_at",
        "evidence",
        ["case_id", "created_at"],
    )
    op.create_index(
        "ix_processing_jobs_evidence_id_created_at",
        "processing_jobs",
        ["evidence_id", "created_at"],
    )
    op.create_index(
        "ix_processing_jobs_status_created_at",
        "processing_jobs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_audit_events_case_id_timestamp",
        "audit_events",
        ["case_id", "timestamp"],
    )
    op.create_index(
        "ix_findings_analysis_run_id_detector",
        "findings",
        ["analysis_run_id", "detector"],
    )
    op.create_index(
        "ix_analysis_runs_evidence_id_created_at",
        "analysis_runs",
        ["evidence_id", "created_at"],
    )
    op.create_index(
        "ix_fusion_analysis_runs_evidence_id_created_at",
        "fusion_analysis_runs",
        ["evidence_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fusion_analysis_runs_evidence_id_created_at",
        table_name="fusion_analysis_runs",
    )
    op.drop_index(
        "ix_analysis_runs_evidence_id_created_at",
        table_name="analysis_runs",
    )
    op.drop_index(
        "ix_findings_analysis_run_id_detector",
        table_name="findings",
    )
    op.drop_index(
        "ix_audit_events_case_id_timestamp",
        table_name="audit_events",
    )
    op.drop_index(
        "ix_processing_jobs_status_created_at",
        table_name="processing_jobs",
    )
    op.drop_index(
        "ix_processing_jobs_evidence_id_created_at",
        table_name="processing_jobs",
    )
    op.drop_index(
        "ix_evidence_case_id_created_at",
        table_name="evidence",
    )
