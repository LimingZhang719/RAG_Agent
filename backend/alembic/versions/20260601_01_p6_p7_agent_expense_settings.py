"""p6 p7 agent expense settings

Revision ID: 20260601_01
Revises: 20260529_01
Create Date: 2026-06-01 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260601_01"
down_revision: str | None = "20260529_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "expense_claims",
        sa.Column("claim_no", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "expense_claims",
        sa.Column(
            "expense_type",
            sa.String(length=64),
            nullable=False,
            server_default="travel",
        ),
    )
    op.add_column(
        "expense_claims",
        sa.Column("audit_summary", sa.dialects.postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "expense_claims",
        sa.Column(
            "reviewer_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "expense_claims",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "expense_claims",
        sa.Column("review_comment", sa.Text(), nullable=True),
    )
    op.create_unique_constraint("uq_expense_claims_claim_no", "expense_claims", ["claim_no"])

    op.add_column(
        "expense_attachments",
        sa.Column("extracted_fields", sa.dialects.postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "expense_attachments",
        sa.Column("ocr_confidence", sa.Numeric(5, 4), nullable=True),
    )
    op.add_column(
        "expense_attachments",
        sa.Column("classification_source", sa.String(length=32), nullable=True),
    )

    op.create_table(
        "expense_approval_logs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "claim_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("expense_claims.id"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.Enum(
                "submit",
                "resubmit",
                "approve",
                "reject",
                "request_supplement",
                name="expense_approval_action",
            ),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("snapshot", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_expense_approval_logs_claim", "expense_approval_logs", ["claim_id"])

    op.create_table(
        "travel_expense_standards",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "org_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.Column("city_tier", sa.String(length=32), nullable=True),
        sa.Column("daily_limit", sa.Numeric(12, 2), nullable=True),
        sa.Column("single_trip_limit", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CNY"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "system_settings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("value", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column(
            "value_type",
            sa.Enum("string", "number", "boolean", "json", "secret", name="setting_value_type"),
            nullable=False,
        ),
        sa.Column("group_name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "is_runtime_editable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "updated_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("travel_expense_standards")
    op.drop_index("ix_expense_approval_logs_claim", table_name="expense_approval_logs")
    op.drop_table("expense_approval_logs")
    op.drop_column("expense_attachments", "classification_source")
    op.drop_column("expense_attachments", "ocr_confidence")
    op.drop_column("expense_attachments", "extracted_fields")
    op.drop_constraint("uq_expense_claims_claim_no", "expense_claims", type_="unique")
    op.drop_column("expense_claims", "review_comment")
    op.drop_column("expense_claims", "reviewed_at")
    op.drop_column("expense_claims", "reviewer_id")
    op.drop_column("expense_claims", "audit_summary")
    op.drop_column("expense_claims", "expense_type")
    op.drop_column("expense_claims", "claim_no")
