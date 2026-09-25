"""Adiciona índice para o filtro de catálogo por gênero.

Revision ID: 0002_add_catalog_filter_index
Revises: 0001_initial_movie_schema
Create Date: 2026-09-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_add_catalog_filter_index"
down_revision: str | Sequence[str] | None = "0001_initial_movie_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_bridge_movie_genre_sk_genre_id",
        "bridge_movie_genre",
        ["sk_genre_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_bridge_movie_genre_sk_genre_id", table_name="bridge_movie_genre")
