"""Alembic migration for Phase 9E case review tables.

Revision ID: 20260911_0030
Revises: 20260910_0029

Spec names review_checklists / review_approvals collide with Phase 8B/8E;
these tables use the case_review_* prefix.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260911_0030"
down_revision: Union[str, Sequence[str], None] = "20260910_0029"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_review_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("checklist_count", sa.Integer(), nullable=False),
        sa.Column("approval_count", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("outstanding", sa.JSON(), nullable=False),
        sa.Column("blocking", sa.JSON(), nullable=False),
        sa.Column("required_roles", sa.JSON(), nullable=False),
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
        "ix_case_review_runs_case_id", "case_review_runs", ["case_id"],
    )
    op.create_index(
        "ix_case_review_runs_stage", "case_review_runs", ["stage"],
    )

    op.create_table(
        "case_review_checklists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["case_review_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_review_checklists_run_id",
        "case_review_checklists",
        ["run_id"],
    )
    op.create_index(
        "ix_case_review_checklists_case_id",
        "case_review_checklists",
        ["case_id"],
    )

    op.create_table(
        "case_review_checklist_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("checklist_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("item_key", sa.String(length=128), nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("suggested_status", sa.String(length=32), nullable=False),
        sa.Column("blocking", sa.Boolean(), nullable=False),
        sa.Column("outstanding", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("reviewer", sa.String(length=256), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["checklist_id"],
            ["case_review_checklists.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["case_review_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_review_checklist_items_checklist_id",
        "case_review_checklist_items",
        ["checklist_id"],
    )
    op.create_index(
        "ix_case_review_checklist_items_run_id",
        "case_review_checklist_items",
        ["run_id"],
    )
    op.create_index(
        "ix_case_review_checklist_items_case_id",
        "case_review_checklist_items",
        ["case_id"],
    )
    op.create_index(
        "ix_case_review_checklist_items_code",
        "case_review_checklist_items",
        ["item_code"],
    )

    op.create_table(
        "case_review_approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("checklist_id", sa.Uuid(), nullable=True),
        sa.Column("checklist_item_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer", sa.String(length=256), nullable=False),
        sa.Column("approver_role", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("comments", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["checklist_id"],
            ["case_review_checklists.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["checklist_item_id"],
            ["case_review_checklist_items.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["case_review_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_review_approvals_run_id",
        "case_review_approvals",
        ["run_id"],
    )
    op.create_index(
        "ix_case_review_approvals_case_id",
        "case_review_approvals",
        ["case_id"],
    )
    op.create_index(
        "ix_case_review_approvals_role",
        "case_review_approvals",
        ["approver_role"],
    )

    op.create_table(
        "case_review_validation_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("validation_pct", sa.Float(), nullable=False),
        sa.Column("evidence_coverage_pct", sa.Float(), nullable=False),
        sa.Column("review_completion_pct", sa.Float(), nullable=False),
        sa.Column("approval_completion_pct", sa.Float(), nullable=False),
        sa.Column("outstanding_issues", sa.Integer(), nullable=False),
        sa.Column("blocking_issues", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["case_review_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_review_validation_records_run_id",
        "case_review_validation_records",
        ["run_id"],
    )
    op.create_index(
        "ix_case_review_validation_records_case_id",
        "case_review_validation_records",
        ["case_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_case_review_validation_records_case_id",
        table_name="case_review_validation_records",
    )
    op.drop_index(
        "ix_case_review_validation_records_run_id",
        table_name="case_review_validation_records",
    )
    op.drop_table("case_review_validation_records")
    op.drop_index(
        "ix_case_review_approvals_role", table_name="case_review_approvals",
    )
    op.drop_index(
        "ix_case_review_approvals_case_id",
        table_name="case_review_approvals",
    )
    op.drop_index(
        "ix_case_review_approvals_run_id",
        table_name="case_review_approvals",
    )
    op.drop_table("case_review_approvals")
    op.drop_index(
        "ix_case_review_checklist_items_code",
        table_name="case_review_checklist_items",
    )
    op.drop_index(
        "ix_case_review_checklist_items_case_id",
        table_name="case_review_checklist_items",
    )
    op.drop_index(
        "ix_case_review_checklist_items_run_id",
        table_name="case_review_checklist_items",
    )
    op.drop_index(
        "ix_case_review_checklist_items_checklist_id",
        table_name="case_review_checklist_items",
    )
    op.drop_table("case_review_checklist_items")
    op.drop_index(
        "ix_case_review_checklists_case_id",
        table_name="case_review_checklists",
    )
    op.drop_index(
        "ix_case_review_checklists_run_id",
        table_name="case_review_checklists",
    )
    op.drop_table("case_review_checklists")
    op.drop_index("ix_case_review_runs_stage", table_name="case_review_runs")
    op.drop_index("ix_case_review_runs_case_id", table_name="case_review_runs")
    op.drop_table("case_review_runs")
