"""Add Phase 8C investigation intelligence summaries.

Revision ID: 20260903_0022
Revises: 20260902_0021
Create Date: 2026-09-03

Note: Spec referenced 20260901_0016, but that revision already exists for
entity resolution. This migration continues the linear chain after 8B.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260903_0022"
down_revision = "20260902_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create investigation_summaries table."""

    op.create_table(
        "investigation_summaries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("overall_risk", sa.String(length=16), nullable=False),
        sa.Column("overall_confidence", sa.Integer(), nullable=False),
        sa.Column("overview", sa.JSON(), nullable=False),
        sa.Column("key_findings", sa.JSON(), nullable=False),
        sa.Column("timeline_summary", sa.JSON(), nullable=False),
        sa.Column("correlation_summary", sa.JSON(), nullable=False),
        sa.Column("ai_summary", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("narrative", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_investigation_summaries_case_id",
        "investigation_summaries",
        ["case_id"],
    )
    op.create_index(
        "ix_investigation_summaries_generated_at",
        "investigation_summaries",
        ["generated_at"],
    )


def downgrade() -> None:
    """Drop investigation_summaries table."""

    op.drop_index(
        "ix_investigation_summaries_generated_at",
        table_name="investigation_summaries",
    )
    op.drop_index(
        "ix_investigation_summaries_case_id",
        table_name="investigation_summaries",
    )
    op.drop_table("investigation_summaries")
