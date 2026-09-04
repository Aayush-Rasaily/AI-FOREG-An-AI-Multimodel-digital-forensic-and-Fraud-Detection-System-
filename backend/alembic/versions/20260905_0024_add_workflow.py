"""Add Phase 8E investigation workflow tables.

Revision ID: 20260905_0024
Revises: 20260904_0023
Create Date: 2026-09-05

Note: Spec referenced 20260901_0017, but that revision already exists for
reports. This migration continues the linear chain after Phase 8D.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260905_0024"
down_revision = "20260904_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create investigation workflow tables."""

    op.create_table(
        "investigation_workflows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assigned_analyst_id", sa.Uuid(), nullable=True),
        sa.Column("activity", sa.JSON(), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status_changed_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["assigned_analyst_id"], ["users.id"], ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", name="uq_investigation_workflows_case"),
    )
    op.create_index(
        "ix_investigation_workflows_case_id",
        "investigation_workflows",
        ["case_id"],
    )
    op.create_index(
        "ix_investigation_workflows_status",
        "investigation_workflows",
        ["status"],
    )

    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("linked_evidence_id", sa.Uuid(), nullable=True),
        sa.Column("linked_report_id", sa.Uuid(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["investigation_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["assignee_id"], ["users.id"], ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["linked_evidence_id"], ["evidence.id"], ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["linked_report_id"],
            ["forensic_reports.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_tasks_case_id", "workflow_tasks", ["case_id"])
    op.create_index(
        "ix_workflow_tasks_workflow_id", "workflow_tasks", ["workflow_id"],
    )
    op.create_index("ix_workflow_tasks_status", "workflow_tasks", ["status"])
    op.create_index(
        "ix_workflow_tasks_assignee_id", "workflow_tasks", ["assignee_id"],
    )

    op.create_table(
        "workflow_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("history", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["investigation_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_notes_case_id", "workflow_notes", ["case_id"])
    op.create_index(
        "ix_workflow_notes_workflow_id", "workflow_notes", ["workflow_id"],
    )

    op.create_table(
        "workflow_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("review_kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=True),
        sa.Column("report_id", sa.Uuid(), nullable=True),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("history", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["investigation_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["evidence.id"], ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["report_id"], ["forensic_reports.id"], ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"], ["users.id"], ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_reviews_case_id", "workflow_reviews", ["case_id"],
    )
    op.create_index(
        "ix_workflow_reviews_workflow_id", "workflow_reviews", ["workflow_id"],
    )
    op.create_index(
        "ix_workflow_reviews_kind", "workflow_reviews", ["review_kind"],
    )
    op.create_index(
        "ix_workflow_reviews_status", "workflow_reviews", ["status"],
    )

    op.create_table(
        "workflow_milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("milestone_type", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("reached_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reached_by", sa.Uuid(), nullable=True),
        sa.Column("auto_derived", sa.Boolean(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["investigation_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workflow_id",
            "milestone_type",
            name="uq_workflow_milestones_type",
        ),
    )
    op.create_index(
        "ix_workflow_milestones_case_id", "workflow_milestones", ["case_id"],
    )
    op.create_index(
        "ix_workflow_milestones_workflow_id",
        "workflow_milestones",
        ["workflow_id"],
    )

    op.create_table(
        "workflow_notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["investigation_workflows.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_notifications_case_id",
        "workflow_notifications",
        ["case_id"],
    )
    op.create_index(
        "ix_workflow_notifications_user_id",
        "workflow_notifications",
        ["user_id"],
    )
    op.create_index(
        "ix_workflow_notifications_status",
        "workflow_notifications",
        ["status"],
    )


def downgrade() -> None:
    """Drop investigation workflow tables."""

    op.drop_index(
        "ix_workflow_notifications_status",
        table_name="workflow_notifications",
    )
    op.drop_index(
        "ix_workflow_notifications_user_id",
        table_name="workflow_notifications",
    )
    op.drop_index(
        "ix_workflow_notifications_case_id",
        table_name="workflow_notifications",
    )
    op.drop_table("workflow_notifications")

    op.drop_index(
        "ix_workflow_milestones_workflow_id",
        table_name="workflow_milestones",
    )
    op.drop_index(
        "ix_workflow_milestones_case_id", table_name="workflow_milestones",
    )
    op.drop_table("workflow_milestones")

    op.drop_index(
        "ix_workflow_reviews_status", table_name="workflow_reviews",
    )
    op.drop_index("ix_workflow_reviews_kind", table_name="workflow_reviews")
    op.drop_index(
        "ix_workflow_reviews_workflow_id", table_name="workflow_reviews",
    )
    op.drop_index(
        "ix_workflow_reviews_case_id", table_name="workflow_reviews",
    )
    op.drop_table("workflow_reviews")

    op.drop_index(
        "ix_workflow_notes_workflow_id", table_name="workflow_notes",
    )
    op.drop_index("ix_workflow_notes_case_id", table_name="workflow_notes")
    op.drop_table("workflow_notes")

    op.drop_index(
        "ix_workflow_tasks_assignee_id", table_name="workflow_tasks",
    )
    op.drop_index("ix_workflow_tasks_status", table_name="workflow_tasks")
    op.drop_index(
        "ix_workflow_tasks_workflow_id", table_name="workflow_tasks",
    )
    op.drop_index("ix_workflow_tasks_case_id", table_name="workflow_tasks")
    op.drop_table("workflow_tasks")

    op.drop_index(
        "ix_investigation_workflows_status",
        table_name="investigation_workflows",
    )
    op.drop_index(
        "ix_investigation_workflows_case_id",
        table_name="investigation_workflows",
    )
    op.drop_table("investigation_workflows")
