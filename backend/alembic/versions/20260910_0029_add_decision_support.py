"""Alembic migration for Phase 9D decision support tables.

Revision ID: 20260910_0029
Revises: 20260909_0028

Spec table names (workflow_runs / workflow_tasks) collide with Phase 8E;
these tables use the decision_support_* prefix.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0029"
down_revision: Union[str, Sequence[str], None] = "20260909_0028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "decision_support_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=32), nullable=False),
        sa.Column("task_count", sa.Integer(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
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
        "ix_decision_support_runs_case_id",
        "decision_support_runs",
        ["case_id"],
    )
    op.create_index(
        "ix_decision_support_runs_status",
        "decision_support_runs",
        ["status"],
    )

    op.create_table(
        "decision_support_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("task_key", sa.String(length=128), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("estimated_effort_hours", sa.Float(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("required_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("supporting_intelligence", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["decision_support_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_support_tasks_run_id",
        "decision_support_tasks",
        ["run_id"],
    )
    op.create_index(
        "ix_decision_support_tasks_case_id",
        "decision_support_tasks",
        ["case_id"],
    )
    op.create_index(
        "ix_decision_support_tasks_status",
        "decision_support_tasks",
        ["status"],
    )
    op.create_index(
        "ix_decision_support_tasks_stage",
        "decision_support_tasks",
        ["stage"],
    )

    op.create_table(
        "decision_support_review_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("queue_key", sa.String(length=128), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["decision_support_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_support_review_items_run_id",
        "decision_support_review_items",
        ["run_id"],
    )
    op.create_index(
        "ix_decision_support_review_items_case_id",
        "decision_support_review_items",
        ["case_id"],
    )

    op.create_table(
        "decision_support_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("investigator", sa.String(length=256), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["decision_support_runs.id"], ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["decision_support_tasks.id"], ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_support_decisions_case_id",
        "decision_support_decisions",
        ["case_id"],
    )
    op.create_index(
        "ix_decision_support_decisions_task_id",
        "decision_support_decisions",
        ["task_id"],
    )


def downgrade() -> None:
    op.drop_table("decision_support_decisions")
    op.drop_table("decision_support_review_items")
    op.drop_table("decision_support_tasks")
    op.drop_table("decision_support_runs")
