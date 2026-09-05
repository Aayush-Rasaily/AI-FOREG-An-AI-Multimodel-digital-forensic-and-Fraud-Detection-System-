"""Alembic migration for Phase 9F integrity monitoring tables.

Revision ID: 20260912_0031
Revises: 20260911_0030
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260912_0031"
down_revision: Union[str, Sequence[str], None] = "20260911_0030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "integrity_monitor_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("check_count", sa.Integer(), nullable=False),
        sa.Column("alert_count", sa.Integer(), nullable=False),
        sa.Column("drift_count", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("timeline", sa.JSON(), nullable=False),
        sa.Column("fingerprints", sa.JSON(), nullable=False),
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
        "ix_integrity_monitor_runs_case_id",
        "integrity_monitor_runs",
        ["case_id"],
    )
    op.create_index(
        "ix_integrity_monitor_runs_status",
        "integrity_monitor_runs",
        ["status"],
    )

    op.create_table(
        "integrity_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("check_key", sa.String(length=128), nullable=False),
        sa.Column("check_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("expected", sa.Text(), nullable=True),
        sa.Column("observed", sa.Text(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["integrity_monitor_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integrity_checks_run_id", "integrity_checks", ["run_id"])
    op.create_index("ix_integrity_checks_case_id", "integrity_checks", ["case_id"])
    op.create_index("ix_integrity_checks_code", "integrity_checks", ["check_code"])

    op.create_table(
        "integrity_alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("alert_key", sa.String(length=128), nullable=False),
        sa.Column("alert_code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=True),
        sa.Column("check_code", sa.String(length=64), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["integrity_monitor_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integrity_alerts_run_id", "integrity_alerts", ["run_id"])
    op.create_index("ix_integrity_alerts_case_id", "integrity_alerts", ["case_id"])
    op.create_index(
        "ix_integrity_alerts_severity", "integrity_alerts", ["severity"],
    )

    op.create_table(
        "integrity_drift_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("drift_key", sa.String(length=128), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("current_value", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("integrity_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["integrity_monitor_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_integrity_drift_records_run_id",
        "integrity_drift_records",
        ["run_id"],
    )
    op.create_index(
        "ix_integrity_drift_records_case_id",
        "integrity_drift_records",
        ["case_id"],
    )
    op.create_index(
        "ix_integrity_drift_records_evidence_id",
        "integrity_drift_records",
        ["evidence_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_integrity_drift_records_evidence_id",
        table_name="integrity_drift_records",
    )
    op.drop_index(
        "ix_integrity_drift_records_case_id",
        table_name="integrity_drift_records",
    )
    op.drop_index(
        "ix_integrity_drift_records_run_id",
        table_name="integrity_drift_records",
    )
    op.drop_table("integrity_drift_records")
    op.drop_index("ix_integrity_alerts_severity", table_name="integrity_alerts")
    op.drop_index("ix_integrity_alerts_case_id", table_name="integrity_alerts")
    op.drop_index("ix_integrity_alerts_run_id", table_name="integrity_alerts")
    op.drop_table("integrity_alerts")
    op.drop_index("ix_integrity_checks_code", table_name="integrity_checks")
    op.drop_index("ix_integrity_checks_case_id", table_name="integrity_checks")
    op.drop_index("ix_integrity_checks_run_id", table_name="integrity_checks")
    op.drop_table("integrity_checks")
    op.drop_index(
        "ix_integrity_monitor_runs_status", table_name="integrity_monitor_runs",
    )
    op.drop_index(
        "ix_integrity_monitor_runs_case_id",
        table_name="integrity_monitor_runs",
    )
    op.drop_table("integrity_monitor_runs")
