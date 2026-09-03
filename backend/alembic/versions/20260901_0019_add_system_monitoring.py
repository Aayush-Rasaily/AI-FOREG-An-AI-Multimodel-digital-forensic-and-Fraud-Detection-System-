"""Add Phase 7F system monitoring tables.

Revision ID: 20260901_0019
Revises: 20260901_0018
Create Date: 2026-09-01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0019"
down_revision = "20260901_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create system_diagnostics_runs table."""
    op.create_table(
        "system_diagnostics_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "overall_status", sa.String(length=32), nullable=False,
        ),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column(
            "engine_version", sa.String(length=32), nullable=False,
        ),
        sa.Column(
            "policy_version", sa.String(length=32), nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop system_diagnostics_runs table."""
    op.drop_table("system_diagnostics_runs")
