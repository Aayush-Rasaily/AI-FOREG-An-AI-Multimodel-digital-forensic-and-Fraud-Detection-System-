"""Alembic migration for Phase 9C investigation intelligence tables.

Revision ID: 20260909_0028
Revises: 20260908_0027
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260909_0028"
down_revision: Union[str, Sequence[str], None] = "20260908_0027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investigation_intelligence_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("investigation_score", sa.Float(), nullable=False),
        sa.Column("overall_completeness", sa.Float(), nullable=False),
        sa.Column("hypothesis_count", sa.Integer(), nullable=False),
        sa.Column("gap_count", sa.Integer(), nullable=False),
        sa.Column("recommendation_count", sa.Integer(), nullable=False),
        sa.Column("open_conflict_count", sa.Integer(), nullable=False),
        sa.Column("coverage", sa.JSON(), nullable=False),
        sa.Column("open_conflicts", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_investigation_intelligence_runs_case_id",
        "investigation_intelligence_runs",
        ["case_id"],
    )
    op.create_index(
        "ix_investigation_intelligence_runs_status",
        "investigation_intelligence_runs",
        ["status"],
    )

    op.create_table(
        "investigation_hypotheses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("hypothesis_key", sa.String(length=128), nullable=False),
        sa.Column("hypothesis_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("contradicting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["investigation_intelligence_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_investigation_hypotheses_run_id",
        "investigation_hypotheses",
        ["run_id"],
    )
    op.create_index(
        "ix_investigation_hypotheses_case_id",
        "investigation_hypotheses",
        ["case_id"],
    )
    op.create_index(
        "ix_investigation_hypotheses_type",
        "investigation_hypotheses",
        ["hypothesis_type"],
    )

    op.create_table(
        "evidence_gap_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("gap_key", sa.String(length=128), nullable=False),
        sa.Column("gap_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.String(length=64), nullable=False),
        sa.Column("affected_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["investigation_intelligence_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evidence_gap_records_run_id", "evidence_gap_records", ["run_id"],
    )
    op.create_index(
        "ix_evidence_gap_records_case_id", "evidence_gap_records", ["case_id"],
    )
    op.create_index(
        "ix_evidence_gap_records_gap_type",
        "evidence_gap_records",
        ["gap_type"],
    )

    op.create_table(
        "investigation_recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_key", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("action_text", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("related_hypothesis_keys", sa.JSON(), nullable=False),
        sa.Column("related_gap_keys", sa.JSON(), nullable=False),
        sa.Column("affected_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["investigation_intelligence_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_investigation_recommendations_run_id",
        "investigation_recommendations",
        ["run_id"],
    )
    op.create_index(
        "ix_investigation_recommendations_case_id",
        "investigation_recommendations",
        ["case_id"],
    )
    op.create_index(
        "ix_investigation_recommendations_code",
        "investigation_recommendations",
        ["code"],
    )


def downgrade() -> None:
    op.drop_table("investigation_recommendations")
    op.drop_table("evidence_gap_records")
    op.drop_table("investigation_hypotheses")
    op.drop_table("investigation_intelligence_runs")
