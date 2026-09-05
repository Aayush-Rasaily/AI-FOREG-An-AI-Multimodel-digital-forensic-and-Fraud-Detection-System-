"""Alembic migration for Phase 9G investigation analytics.

Revision ID: 20260913_0032
Revises: 20260912_0031
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260913_0032"
down_revision: Union[str, Sequence[str], None] = "20260912_0031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analytics_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metric_count", sa.Integer(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_runs_status", "analytics_runs", ["status"])

    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["analytics_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analytics_snapshots_run_id", "analytics_snapshots", ["run_id"],
    )

    op.create_table(
        "analytics_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["analytics_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analytics_metrics_run_id", "analytics_metrics", ["run_id"],
    )
    op.create_index(
        "ix_analytics_metrics_key", "analytics_metrics", ["metric_key"],
    )

    op.create_table(
        "analytics_dashboards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("layout", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["analytics_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analytics_dashboards_run_id", "analytics_dashboards", ["run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analytics_dashboards_run_id", table_name="analytics_dashboards",
    )
    op.drop_table("analytics_dashboards")
    op.drop_index("ix_analytics_metrics_key", table_name="analytics_metrics")
    op.drop_index("ix_analytics_metrics_run_id", table_name="analytics_metrics")
    op.drop_table("analytics_metrics")
    op.drop_index(
        "ix_analytics_snapshots_run_id", table_name="analytics_snapshots",
    )
    op.drop_table("analytics_snapshots")
    op.drop_index("ix_analytics_runs_status", table_name="analytics_runs")
    op.drop_table("analytics_runs")
