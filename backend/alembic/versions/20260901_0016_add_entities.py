"""Add entity resolution and investigation graph tables.

Revision ID: 20260901_0016
Revises: 20260901_0015
Create Date: 2026-09-01
"""

import sqlalchemy as sa

from alembic import op

revision = "20260901_0016"
down_revision = "20260901_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create entity-resolution persistence tables."""

    op.create_table(
        "entity_resolution_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                name="entity_run_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("relationship_count", sa.Integer(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_entity_resolution_runs_case_id",
        "entity_resolution_runs",
        ["case_id"],
    )
    op.create_index(
        "uq_entity_resolution_runs_active",
        "entity_resolution_runs",
        ["case_id"],
        unique=True,
        sqlite_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
        postgresql_where=sa.text("status IN ('QUEUED', 'RUNNING')"),
    )

    op.create_table(
        "investigation_entities",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("canonical_id", sa.String(length=32), nullable=False),
        sa.Column(
            "entity_type",
            sa.Enum(
                "person",
                "organization",
                "email",
                "phone",
                "address",
                "website",
                "domain",
                "device",
                "camera",
                "vehicle",
                "bank_account",
                "crypto_wallet",
                "document",
                "image",
                "video",
                "audio",
                "qr_code",
                "logo",
                "signature",
                "location",
                "ip_address",
                "file_hash",
                name="entity_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("normalized_key", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("support_count", sa.Integer(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["entity_resolution_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_run_id",
            "entity_type",
            "normalized_key",
            name="uq_investigation_entities_run_type_key",
        ),
    )
    op.create_index(
        "ix_investigation_entities_analysis_run_id",
        "investigation_entities",
        ["analysis_run_id"],
    )
    op.create_index(
        "ix_investigation_entities_case_id",
        "investigation_entities",
        ["case_id"],
    )
    op.create_index(
        "ix_investigation_entities_canonical_id",
        "investigation_entities",
        ["canonical_id"],
    )

    op.create_table(
        "entity_relationships",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("relationship_id", sa.String(length=256), nullable=False),
        sa.Column("source_canonical_id", sa.String(length=32), nullable=False),
        sa.Column("target_canonical_id", sa.String(length=32), nullable=False),
        sa.Column(
            "relationship_type",
            sa.Enum(
                "owns",
                "uses",
                "created",
                "contains",
                "references",
                "sent_to",
                "received_from",
                "captured_by",
                "signed_by",
                "located_at",
                "related_to",
                "derived_from",
                "duplicate_of",
                "supports",
                "contradicts",
                name="entity_relationship_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("support_count", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["entity_resolution_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_run_id",
            "source_canonical_id",
            "target_canonical_id",
            "relationship_type",
            name="uq_entity_relationships_run_edge",
        ),
    )
    op.create_index(
        "ix_entity_relationships_analysis_run_id",
        "entity_relationships",
        ["analysis_run_id"],
    )
    op.create_index(
        "ix_entity_relationships_case_id",
        "entity_relationships",
        ["case_id"],
    )

    op.create_table(
        "entity_support_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("relationship_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("support_kind", sa.String(length=64), nullable=False),
        sa.Column("support_ref", sa.String(length=256), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["investigation_entities.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["entity_relationships.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_entity_support_records_entity_id",
        "entity_support_records",
        ["entity_id"],
    )
    op.create_index(
        "ix_entity_support_records_relationship_id",
        "entity_support_records",
        ["relationship_id"],
    )


def downgrade() -> None:
    """Drop entity-resolution persistence tables."""

    op.drop_index(
        "ix_entity_support_records_relationship_id",
        table_name="entity_support_records",
    )
    op.drop_index(
        "ix_entity_support_records_entity_id",
        table_name="entity_support_records",
    )
    op.drop_table("entity_support_records")
    op.drop_index(
        "ix_entity_relationships_case_id",
        table_name="entity_relationships",
    )
    op.drop_index(
        "ix_entity_relationships_analysis_run_id",
        table_name="entity_relationships",
    )
    op.drop_table("entity_relationships")
    op.drop_index(
        "ix_investigation_entities_canonical_id",
        table_name="investigation_entities",
    )
    op.drop_index(
        "ix_investigation_entities_case_id",
        table_name="investigation_entities",
    )
    op.drop_index(
        "ix_investigation_entities_analysis_run_id",
        table_name="investigation_entities",
    )
    op.drop_table("investigation_entities")
    op.drop_index(
        "uq_entity_resolution_runs_active",
        table_name="entity_resolution_runs",
    )
    op.drop_index(
        "ix_entity_resolution_runs_case_id",
        table_name="entity_resolution_runs",
    )
    op.drop_table("entity_resolution_runs")
