"""add chunking config to knowledge bases and documents

Revision ID: 20260528_03
Revises: 20260528_02
Create Date: 2026-05-28 00:00:02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260528_03"
down_revision: str | None = "20260528_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    chunk_method_enum = sa.Enum("sentence", "token", name="chunk_method")
    chunk_method_enum.create(op.get_bind(), checkfirst=True)

    document_chunk_method_enum = sa.Enum(
        "sentence", "token", name="document_chunk_method"
    )
    document_chunk_method_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "knowledge_bases",
        sa.Column(
            "chunk_method",
            chunk_method_enum,
            nullable=False,
            server_default="sentence",
        ),
    )
    op.add_column(
        "knowledge_bases",
        sa.Column("chunk_size", sa.Integer(), nullable=False, server_default="1024"),
    )
    op.add_column(
        "knowledge_bases",
        sa.Column(
            "chunk_overlap", sa.Integer(), nullable=False, server_default="128"
        ),
    )

    op.add_column(
        "documents",
        sa.Column("chunk_method", document_chunk_method_enum, nullable=True),
    )
    op.add_column(
        "documents", sa.Column("chunk_size", sa.Integer(), nullable=True)
    )
    op.add_column(
        "documents", sa.Column("chunk_overlap", sa.Integer(), nullable=True)
    )

    op.alter_column("knowledge_bases", "chunk_method", server_default=None)
    op.alter_column("knowledge_bases", "chunk_size", server_default=None)
    op.alter_column("knowledge_bases", "chunk_overlap", server_default=None)


def downgrade() -> None:
    op.drop_column("documents", "chunk_overlap")
    op.drop_column("documents", "chunk_size")
    op.drop_column("documents", "chunk_method")

    op.drop_column("knowledge_bases", "chunk_overlap")
    op.drop_column("knowledge_bases", "chunk_size")
    op.drop_column("knowledge_bases", "chunk_method")

    sa.Enum(name="document_chunk_method").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="chunk_method").drop(op.get_bind(), checkfirst=True)
