"""Cria listas pessoais, itens de listas e a lista especial assistir depois.

Revision ID: 0005_add_user_lists
Revises: 0004_link_reviews_to_users
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_user_lists"
down_revision: str | Sequence[str] | None = "0004_link_reviews_to_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_lists",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("visibilidade", sa.String(length=20), server_default="privada", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("visibilidade IN ('publica', 'privada')", name="visibility_valid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_lists_user_id", "user_lists", ["user_id"], unique=False)
    op.create_index("ix_user_lists_visibilidade", "user_lists", ["visibilidade"], unique=False)

    op.create_table(
        "user_list_movies",
        sa.Column("list_id", sa.String(length=32), nullable=False),
        sa.Column("sk_movie_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["list_id"], ["user_lists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sk_movie_id"], ["dim_movies.sk_movie_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("list_id", "sk_movie_id"),
    )
    op.create_index("ix_user_list_movies_sk_movie_id", "user_list_movies", ["sk_movie_id"], unique=False)

    op.create_table(
        "watch_later_movies",
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("sk_movie_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sk_movie_id"], ["dim_movies.sk_movie_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "sk_movie_id"),
    )
    op.create_index("ix_watch_later_movies_sk_movie_id", "watch_later_movies", ["sk_movie_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_watch_later_movies_sk_movie_id", table_name="watch_later_movies")
    op.drop_table("watch_later_movies")
    op.drop_index("ix_user_list_movies_sk_movie_id", table_name="user_list_movies")
    op.drop_table("user_list_movies")
    op.drop_index("ix_user_lists_visibilidade", table_name="user_lists")
    op.drop_index("ix_user_lists_user_id", table_name="user_lists")
    op.drop_table("user_lists")
