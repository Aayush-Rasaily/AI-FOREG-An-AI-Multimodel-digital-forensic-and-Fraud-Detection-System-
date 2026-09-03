"""Add Phase 7E audit framework tables.

Revision ID: 20260901_0018
Revises: 20260901_0017
Create Date: 2026-09-01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0018"
down_revision = "20260901_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_events table."""
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("user", sa.String(256), nullable=False),
        sa.Column("operation", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("evidence_id", sa.Uuid(), nullable=True),
        sa.Column("previous_state", sa.JSON(), nullable=True),
        sa.Column("new_state", sa.JSON(), nullable=True),
        sa.Column("client_ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column(
            "engine_version", sa.String(32), nullable=False,
        ),
        sa.Column(
            "policy_version", sa.String(32), nullable=False,
        ),
        sa.Column(
            "sha256_checksum", sa.String(64), nullable=True,
        ),
        sa.Column(
            "integrity_hash", sa.String(64), nullable=False,
        ),
        sa.Column(
            "metadata", sa.JSON(), nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_timestamp",
        "audit_events",
        ["timestamp"],
    )
    op.create_index(
        "ix_audit_events_case_id",
        "audit_events",
        ["case_id"],
    )
    op.create_index(
        "ix_audit_events_evidence_id",
        "audit_events",
        ["evidence_id"],
    )
    op.create_index(
        "ix_audit_events_operation",
        "audit_events",
        ["operation"],
    )
    op.create_index(
        "ix_audit_events_category",
        "audit_events",
        ["category"],
    )
    op.create_index(
        "ix_audit_events_user",
        "audit_events",
        ["user"],
    )


def downgrade() -> None:
    """Drop audit_events table."""
    op.drop_table("audit_events")
