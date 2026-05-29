"""add user approval fields

Revision ID: 20260529_01
Revises: 20260528_03
Create Date: 2026-05-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260529_01"
down_revision: str | None = "20260528_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    approval_status_enum = sa.Enum(
        "approved", "pending", "rejected", name="approval_status"
    )
    approval_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "approval_status",
            approval_status_enum,
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column(
        "users",
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "users", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_users_approved_by_users", "users", "users", ["approved_by"], ["id"]
    )
    op.alter_column("users", "approval_status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_users_approved_by_users", "users", type_="foreignkey")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "approved_by")
    op.drop_column("users", "approval_status")
    sa.Enum(name="approval_status").drop(op.get_bind(), checkfirst=True)
