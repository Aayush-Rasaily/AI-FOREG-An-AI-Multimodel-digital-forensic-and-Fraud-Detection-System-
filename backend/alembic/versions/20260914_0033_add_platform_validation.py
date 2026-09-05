"""Alembic migration for Phase 9H platform validation.

Revision ID: 20260914_0033
Revises: 20260913_0032
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260914_0033"
down_revision: Union[str, Sequence[str], None] = "20260913_0032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_validation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("readiness_level", sa.String(length=32), nullable=False),
        sa.Column("check_count", sa.Integer(), nullable=False),
        sa.Column("pass_count", sa.Integer(), nullable=False),
        sa.Column("warn_count", sa.Integer(), nullable=False),
        sa.Column("fail_count", sa.Integer(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_platform_validation_runs_status",
        "platform_validation_runs",
        ["status"],
    )

    op.create_table(
        "platform_validation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("check_key", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["platform_validation_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_platform_validation_results_run_id",
        "platform_validation_results",
        ["run_id"],
    )
    op.create_index(
        "ix_platform_validation_results_check_key",
        "platform_validation_results",
        ["check_key"],
    )

    op.create_table(
        "platform_validation_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("check_key", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["platform_validation_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_platform_validation_issues_run_id",
        "platform_validation_issues",
        ["run_id"],
    )
    op.create_index(
        "ix_platform_validation_issues_severity",
        "platform_validation_issues",
        ["severity"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_platform_validation_issues_severity",
        table_name="platform_validation_issues",
    )
    op.drop_index(
        "ix_platform_validation_issues_run_id",
        table_name="platform_validation_issues",
    )
    op.drop_table("platform_validation_issues")
    op.drop_index(
        "ix_platform_validation_results_check_key",
        table_name="platform_validation_results",
    )
    op.drop_index(
        "ix_platform_validation_results_run_id",
        table_name="platform_validation_results",
    )
    op.drop_table("platform_validation_results")
    op.drop_index(
        "ix_platform_validation_runs_status",
        table_name="platform_validation_runs",
    )
    op.drop_table("platform_validation_runs")
