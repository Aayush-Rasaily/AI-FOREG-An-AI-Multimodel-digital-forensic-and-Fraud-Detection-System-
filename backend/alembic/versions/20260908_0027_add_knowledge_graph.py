"""Add Phase 9B knowledge graph tables.

Revision ID: 20260908_0027
Revises: 20260907_0026
Create Date: 2026-09-08

Note: Spec referenced 20260901_00XX, but that band is exhausted.
This migration continues the linear chain after Phase 9A.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260908_0027"
down_revision = "20260907_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create knowledge graph run and graph tables."""

    op.create_table(
        "knowledge_graph_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("relationship_count", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_graph_runs_case_id", "knowledge_graph_runs", ["case_id"],
    )
    op.create_index(
        "ix_knowledge_graph_runs_status", "knowledge_graph_runs", ["status"],
    )

    op.create_table(
        "graph_entities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("graph_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("entity_key", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("normalized_key", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id"], ["knowledge_graph_runs.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_graph_entities_graph_id", "graph_entities", ["graph_id"])
    op.create_index("ix_graph_entities_case_id", "graph_entities", ["case_id"])
    op.create_index(
        "ix_graph_entities_entity_type", "graph_entities", ["entity_type"],
    )
    op.create_index(
        "ix_graph_entities_normalized_key", "graph_entities", ["normalized_key"],
    )

    op.create_table(
        "graph_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("graph_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_key", sa.String(length=128), nullable=False),
        sa.Column("source_entity_key", sa.String(length=128), nullable=False),
        sa.Column("target_entity_key", sa.String(length=128), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("support_count", sa.Integer(), nullable=False),
        sa.Column("provenance_count", sa.Integer(), nullable=False),
        sa.Column("relationship_weight", sa.Float(), nullable=False),
        sa.Column("creation_source", sa.String(length=64), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id"], ["knowledge_graph_runs.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_graph_relationships_graph_id", "graph_relationships", ["graph_id"],
    )
    op.create_index(
        "ix_graph_relationships_case_id", "graph_relationships", ["case_id"],
    )
    op.create_index(
        "ix_graph_relationships_type",
        "graph_relationships",
        ["relationship_type"],
    )

    op.create_table(
        "graph_entity_aliases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("graph_id", sa.Uuid(), nullable=False),
        sa.Column("entity_key", sa.String(length=128), nullable=False),
        sa.Column("alias", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id"], ["knowledge_graph_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_graph_entity_aliases_graph_id", "graph_entity_aliases", ["graph_id"],
    )
    op.create_index(
        "ix_graph_entity_aliases_entity_key",
        "graph_entity_aliases",
        ["entity_key"],
    )
    op.create_index(
        "ix_graph_entity_aliases_alias", "graph_entity_aliases", ["alias"],
    )

    op.create_table(
        "graph_provenance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("graph_id", sa.Uuid(), nullable=False),
        sa.Column("target_kind", sa.String(length=32), nullable=False),
        sa.Column("target_key", sa.String(length=128), nullable=False),
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=True),
        sa.Column("finding_id", sa.String(length=64), nullable=True),
        sa.Column("timeline_id", sa.String(length=64), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("fusion_id", sa.String(length=64), nullable=True),
        sa.Column("ocr_field", sa.String(length=128), nullable=True),
        sa.Column("metadata_field", sa.String(length=128), nullable=True),
        sa.Column("timestamp", sa.String(length=64), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["graph_id"], ["knowledge_graph_runs.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_graph_provenance_graph_id", "graph_provenance", ["graph_id"],
    )
    op.create_index(
        "ix_graph_provenance_target_key", "graph_provenance", ["target_key"],
    )


def downgrade() -> None:
    """Drop knowledge graph tables."""

    op.drop_index("ix_graph_provenance_target_key", table_name="graph_provenance")
    op.drop_index("ix_graph_provenance_graph_id", table_name="graph_provenance")
    op.drop_table("graph_provenance")
    op.drop_index("ix_graph_entity_aliases_alias", table_name="graph_entity_aliases")
    op.drop_index(
        "ix_graph_entity_aliases_entity_key", table_name="graph_entity_aliases",
    )
    op.drop_index(
        "ix_graph_entity_aliases_graph_id", table_name="graph_entity_aliases",
    )
    op.drop_table("graph_entity_aliases")
    op.drop_index("ix_graph_relationships_type", table_name="graph_relationships")
    op.drop_index("ix_graph_relationships_case_id", table_name="graph_relationships")
    op.drop_index("ix_graph_relationships_graph_id", table_name="graph_relationships")
    op.drop_table("graph_relationships")
    op.drop_index("ix_graph_entities_normalized_key", table_name="graph_entities")
    op.drop_index("ix_graph_entities_entity_type", table_name="graph_entities")
    op.drop_index("ix_graph_entities_case_id", table_name="graph_entities")
    op.drop_index("ix_graph_entities_graph_id", table_name="graph_entities")
    op.drop_table("graph_entities")
    op.drop_index("ix_knowledge_graph_runs_status", table_name="knowledge_graph_runs")
    op.drop_index(
        "ix_knowledge_graph_runs_case_id", table_name="knowledge_graph_runs",
    )
    op.drop_table("knowledge_graph_runs")
