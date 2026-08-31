"""Create case, evidence, and chain-of-custody tables.

Revision ID: 20260831_0001
Revises:
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Phase 3 persistence structures."""

    if op.get_bind().dialect.name != "sqlite":
        op.execute(sa.schema.CreateSequence(sa.Sequence("case_number_seq", start=1)))
        op.execute(
            sa.schema.CreateSequence(sa.Sequence("evidence_number_seq", start=1))
        )

    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_number", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "IN_PROGRESS",
                "ON_HOLD",
                "COMPLETED",
                "ARCHIVED",
                name="case_status",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum(
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="case_priority",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number", name="uq_cases_case_number"),
    )
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_created_at", "cases", ["created_at"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_number", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "REGISTERED",
                "READY_FOR_ANALYSIS",
                "ANALYZING",
                "ANALYZED",
                "FAILED",
                "QUARANTINED",
                name="evidence_status",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "sha256_hash", name="uq_evidence_case_hash"),
        sa.UniqueConstraint("evidence_number", name="uq_evidence_number"),
    )
    op.create_index("ix_evidence_case_id", "evidence", ["case_id"])
    op.create_index("ix_evidence_sha256_hash", "evidence", ["sha256_hash"])
    op.create_index("ix_evidence_created_at", "evidence", ["created_at"])

    op.create_table(
        "chain_of_custody_events",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "EVIDENCE_INGESTED",
                "VIEWED",
                "DOWNLOADED",
                "ANALYSIS_STARTED",
                "ANALYSIS_COMPLETED",
                "EXPORTED",
                "DERIVED_ARTIFACT_CREATED",
                name="custody_event_type",
                native_enum=False,
                length=64,
            ),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "actor_type",
            sa.Enum(
                "SYSTEM",
                "USER",
                "SERVICE",
                name="custody_actor_type",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_custody_evidence_id",
        "chain_of_custody_events",
        ["evidence_id"],
    )
    op.create_index(
        "ix_custody_timestamp",
        "chain_of_custody_events",
        ["timestamp"],
    )


def downgrade() -> None:
    """Remove Phase 3 persistence structures."""

    op.drop_index("ix_custody_timestamp", table_name="chain_of_custody_events")
    op.drop_index("ix_custody_evidence_id", table_name="chain_of_custody_events")
    op.drop_table("chain_of_custody_events")
    op.drop_index("ix_evidence_created_at", table_name="evidence")
    op.drop_index("ix_evidence_sha256_hash", table_name="evidence")
    op.drop_index("ix_evidence_case_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_cases_created_at", table_name="cases")
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_table("cases")
    if op.get_bind().dialect.name != "sqlite":
        op.execute(sa.schema.DropSequence(sa.Sequence("evidence_number_seq")))
        op.execute(sa.schema.DropSequence(sa.Sequence("case_number_seq")))
