"""Add Phase 8F security governance tables.

Revision ID: 20260906_0025
Revises: 20260905_0024
Create Date: 2026-09-06

Note: Spec referenced 20260901_0018, but that revision already exists for
the audit framework. This migration continues the linear chain after 8E.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260906_0025"
down_revision = "20260905_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create security governance tables."""

    op.create_table(
        "security_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_security_roles_code"),
    )
    op.create_index("ix_security_roles_code", "security_roles", ["code"])

    op.create_table(
        "security_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_security_permissions_code"),
    )
    op.create_index(
        "ix_security_permissions_resource",
        "security_permissions",
        ["resource"],
    )

    op.create_table(
        "case_access_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("access_level", sa.String(length=64), nullable=False),
        sa.Column("granted_by", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "case_id",
            "user_id",
            "access_level",
            name="uq_case_access_case_user_level",
        ),
    )
    op.create_index(
        "ix_case_access_records_case_id", "case_access_records", ["case_id"],
    )
    op.create_index(
        "ix_case_access_records_user_id", "case_access_records", ["user_id"],
    )
    op.create_index(
        "ix_case_access_records_active", "case_access_records", ["active"],
    )

    op.create_table(
        "policy_violations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("policy_code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_policy_violations_case_id", "policy_violations", ["case_id"],
    )
    op.create_index(
        "ix_policy_violations_policy_code",
        "policy_violations",
        ["policy_code"],
    )
    op.create_index(
        "ix_policy_violations_detected_at",
        "policy_violations",
        ["detected_at"],
    )

    op.create_table(
        "compliance_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_compliance_reports_case_id", "compliance_reports", ["case_id"],
    )
    op.create_index(
        "ix_compliance_reports_generated_at",
        "compliance_reports",
        ["generated_at"],
    )


def downgrade() -> None:
    """Drop security governance tables."""

    op.drop_index(
        "ix_compliance_reports_generated_at",
        table_name="compliance_reports",
    )
    op.drop_index(
        "ix_compliance_reports_case_id", table_name="compliance_reports",
    )
    op.drop_table("compliance_reports")

    op.drop_index(
        "ix_policy_violations_detected_at", table_name="policy_violations",
    )
    op.drop_index(
        "ix_policy_violations_policy_code", table_name="policy_violations",
    )
    op.drop_index(
        "ix_policy_violations_case_id", table_name="policy_violations",
    )
    op.drop_table("policy_violations")

    op.drop_index(
        "ix_case_access_records_active", table_name="case_access_records",
    )
    op.drop_index(
        "ix_case_access_records_user_id", table_name="case_access_records",
    )
    op.drop_index(
        "ix_case_access_records_case_id", table_name="case_access_records",
    )
    op.drop_table("case_access_records")

    op.drop_index(
        "ix_security_permissions_resource",
        table_name="security_permissions",
    )
    op.drop_table("security_permissions")

    op.drop_index("ix_security_roles_code", table_name="security_roles")
    op.drop_table("security_roles")
