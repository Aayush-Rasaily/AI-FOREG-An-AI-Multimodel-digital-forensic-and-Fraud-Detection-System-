"""Add Phase 7D investigation report checksum and analysis-run metadata.

Revision ID: 20260901_0017
Revises: 20260901_0016
Create Date: 2026-09-01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0017"
down_revision = "20260901_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Extend forensic_reports for multi-format investigation reporting."""

    op.add_column(
        "forensic_reports",
        sa.Column("report_checksum", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "forensic_reports",
        sa.Column("included_analysis_run_ids", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Remove Phase 7D report columns."""

    op.drop_column("forensic_reports", "included_analysis_run_ids")
    op.drop_column("forensic_reports", "report_checksum")
