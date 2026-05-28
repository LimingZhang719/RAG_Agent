"""extend document file_type length

Revision ID: 20260528_02
Revises: 20260528_01
Create Date: 2026-05-28 00:00:01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260528_02"
down_revision: str | None = "20260528_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "documents",
        "file_type",
        type_=sa.String(length=255),
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "documents",
        "file_type",
        type_=sa.String(length=64),
        existing_type=sa.String(length=255),
        existing_nullable=False,
    )
