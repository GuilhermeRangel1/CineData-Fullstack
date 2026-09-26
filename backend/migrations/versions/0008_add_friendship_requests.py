"""Cria pedidos de amizade com estados sociais explícitos.

Revision ID: 0008_add_friendship_requests
Revises: 0007_add_user_avatars
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_add_friendship_requests"
down_revision: str | Sequence[str] | None = "0007_add_user_avatars"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "friendship_requests",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("requester_id", sa.String(length=32), nullable=False),
        sa.Column("recipient_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pendente", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("requester_id <> recipient_id", name="different_users"),
        sa.CheckConstraint(
            "status IN ('pendente', 'aceita', 'bloqueada')", name="status_valid"
        ),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_id", "recipient_id", name="requester_recipient_unique"),
    )
    op.create_index("ix_friendship_requests_requester_id", "friendship_requests", ["requester_id"])
    op.create_index("ix_friendship_requests_recipient_id", "friendship_requests", ["recipient_id"])
    op.create_index("ix_friendship_requests_status", "friendship_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_friendship_requests_status", table_name="friendship_requests")
    op.drop_index("ix_friendship_requests_recipient_id", table_name="friendship_requests")
    op.drop_index("ix_friendship_requests_requester_id", table_name="friendship_requests")
    op.drop_table("friendship_requests")
