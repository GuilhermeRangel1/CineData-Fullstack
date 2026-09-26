"""Impede avaliações duplicadas por conta e filme.

Revision ID: 0013_unique_user_movie_review
Revises: 0012_add_community_image
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_unique_user_movie_review"
down_revision: str | Sequence[str] | None = "0012_add_community_image"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    duplicatas = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM ("
            "SELECT user_id, sk_movie_id FROM movie_reviews "
            "WHERE user_id IS NOT NULL GROUP BY user_id, sk_movie_id HAVING COUNT(*) > 1"
            ")"
        )
    ).scalar_one()
    if duplicatas:
        raise RuntimeError(
            "A migration 0013 encontrou avaliações duplicadas da mesma conta e filme. "
            "Revise esses registros antes de aplicar a restrição; nenhum dado foi removido."
        )

    op.create_index(
        "uq_movie_reviews_user_movie",
        "movie_reviews",
        ["user_id", "sk_movie_id"],
        unique=True,
        sqlite_where=sa.text("user_id IS NOT NULL"),
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_movie_reviews_user_movie", table_name="movie_reviews")
