"""Add AI model records, inference jobs, and logs.

Revision ID: 20260831_0006
Revises: 20260831_0005
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0006"
down_revision = "20260831_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create AI infrastructure persistence tables."""

    op.create_table(
        "ai_model_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("framework", sa.String(length=32), nullable=False),
        sa.Column("author", sa.String(length=128), nullable=False),
        sa.Column("license", sa.String(length=64), nullable=False),
        sa.Column("input_type", sa.String(length=32), nullable=False),
        sa.Column("output_type", sa.String(length=32), nullable=False),
        sa.Column("model_hash", sa.String(length=64), nullable=False),
        sa.Column("required_device", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "REGISTERED",
                "LOADED",
                "UNLOADED",
                "FAILED",
                name="ai_model_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("current_device", sa.String(length=16), nullable=True),
        sa.Column("last_loaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_latency_ms", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_ai_model_records_name", "ai_model_records", ["name"])
    op.create_table(
        "inference_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("model_record_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("task", sa.String(length=64), nullable=False),
        sa.Column("device", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                name="inference_job_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("batch_size", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["model_record_id"],
            ["ai_model_records.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_inference_jobs_model_record_id",
        "inference_jobs",
        ["model_record_id"],
    )
    op.create_index("ix_inference_jobs_status", "inference_jobs", ["status"])
    op.create_table(
        "inference_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("job_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["inference_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inference_logs_job_id", "inference_logs", ["job_id"])


def downgrade() -> None:
    """Remove AI infrastructure persistence tables."""

    op.drop_index("ix_inference_logs_job_id", table_name="inference_logs")
    op.drop_table("inference_logs")
    op.drop_index("ix_inference_jobs_status", table_name="inference_jobs")
    op.drop_index("ix_inference_jobs_model_record_id", table_name="inference_jobs")
    op.drop_table("inference_jobs")
    op.drop_index("ix_ai_model_records_name", table_name="ai_model_records")
    op.drop_table("ai_model_records")
