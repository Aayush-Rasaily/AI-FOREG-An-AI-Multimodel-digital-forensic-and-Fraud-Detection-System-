"""Create provenance-preserving extraction records.

Revision ID: 20260831_0003
Revises: 20260831_0002
Create Date: 2026-08-31
"""

import sqlalchemy as sa

from alembic import op

revision = "20260831_0003"
down_revision = "20260831_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create searchable extraction records."""

    op.create_table(
        "extraction_records",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("evidence_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("artifact_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "extraction_type",
            sa.Enum(
                "TEXT",
                "WORD",
                "LINE",
                "IMAGE_REGION",
                "FACE_REGION",
                "SIGNATURE_REGION",
                "LOGO_REGION",
                "STAMP_REGION",
                "NUMBER",
                "DATE",
                "QR_CODE",
                "BARCODE",
                "TABLE",
                "PAGE",
                "FRAME",
                "AUDIO_STREAM",
                "METADATA",
                name="extraction_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.Enum(
                "ORIGINAL",
                "ARTIFACT",
                name="extraction_source_type",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("source_identifier", sa.String(length=1024), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("frame_number", sa.Integer(), nullable=True),
        sa.Column("timestamp_ms", sa.BigInteger(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("bbox_x", sa.Float(), nullable=True),
        sa.Column("bbox_y", sa.Float(), nullable=True),
        sa.Column("bbox_width", sa.Float(), nullable=True),
        sa.Column("bbox_height", sa.Float(), nullable=True),
        sa.Column("normalized_x", sa.Float(), nullable=True),
        sa.Column("normalized_y", sa.Float(), nullable=True),
        sa.Column("normalized_width", sa.Float(), nullable=True),
        sa.Column("normalized_height", sa.Float(), nullable=True),
        sa.Column("method", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extraction_records_evidence_id",
        "extraction_records",
        ["evidence_id"],
    )
    op.create_index(
        "ix_extraction_records_artifact_id",
        "extraction_records",
        ["artifact_id"],
    )
    op.create_index(
        "ix_extraction_records_type",
        "extraction_records",
        ["extraction_type"],
    )
    op.create_index(
        "ix_extraction_records_page_number",
        "extraction_records",
        ["page_number"],
    )
    op.create_index(
        "ix_extraction_records_frame_number",
        "extraction_records",
        ["frame_number"],
    )


def downgrade() -> None:
    """Remove extraction records."""

    op.drop_index("ix_extraction_records_frame_number", table_name="extraction_records")
    op.drop_index("ix_extraction_records_page_number", table_name="extraction_records")
    op.drop_index("ix_extraction_records_type", table_name="extraction_records")
    op.drop_index("ix_extraction_records_artifact_id", table_name="extraction_records")
    op.drop_index("ix_extraction_records_evidence_id", table_name="extraction_records")
    op.drop_table("extraction_records")
