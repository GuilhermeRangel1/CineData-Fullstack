"""Vincula novas avaliações às contas locais.

Revision ID: 0004_link_reviews_to_users
Revises: 0003_add_local_users
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_link_reviews_to_users"
down_revision: str | Sequence[str] | None = "0003_add_local_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("movie_reviews") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(length=32), nullable=True))
        batch_op.create_foreign_key(
            "fk_movie_reviews_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_movie_reviews_user_id", ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("movie_reviews") as batch_op:
        batch_op.drop_index("ix_movie_reviews_user_id")
        batch_op.drop_constraint("fk_movie_reviews_user_id_users", type_="foreignkey")
        batch_op.drop_column("user_id")
