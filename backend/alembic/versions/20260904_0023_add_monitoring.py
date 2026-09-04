"""Add Phase 8D operational monitoring summary tables.

Revision ID: 20260904_0023
Revises: 20260903_0022
Create Date: 2026-09-04

Note: Spec referenced 20260901_0016, but that revision already exists for
entity resolution. This migration continues the linear chain after 8C.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260904_0023"
down_revision = "20260903_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create monitoring summary tables."""

    op.create_table(
        "monitoring_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_monitoring_snapshots_generated_at",
        "monitoring_snapshots",
        ["generated_at"],
    )

    op.create_table(
        "audit_statistics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["monitoring_snapshots.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_statistics_generated_at",
        "audit_statistics",
        ["generated_at"],
    )

    op.create_table(
        "system_health_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["monitoring_snapshots.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_system_health_records_assessed_at",
        "system_health_records",
        ["assessed_at"],
    )
    op.create_index(
        "ix_system_health_records_status",
        "system_health_records",
        ["status"],
    )


def downgrade() -> None:
    """Drop monitoring summary tables."""

    op.drop_index(
        "ix_system_health_records_status",
        table_name="system_health_records",
    )
    op.drop_index(
        "ix_system_health_records_assessed_at",
        table_name="system_health_records",
    )
    op.drop_table("system_health_records")
    op.drop_index(
        "ix_audit_statistics_generated_at",
        table_name="audit_statistics",
    )
    op.drop_table("audit_statistics")
    op.drop_index(
        "ix_monitoring_snapshots_generated_at",
        table_name="monitoring_snapshots",
    )
    op.drop_table("monitoring_snapshots")
