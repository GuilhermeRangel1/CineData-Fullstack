"""Indexa termos de sinopse para a seleção de candidatos do mapa.

Revision ID: 0014_add_taste_map_synopsis_index
Revises: 0013_unique_user_movie_review
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0014_add_taste_map_synopsis_index"
down_revision: str | Sequence[str] | None = "0013_unique_user_movie_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE VIRTUAL TABLE movie_synopsis_fts USING fts5("
        "sk_movie_id UNINDEXED, sinopse, "
        "tokenize='unicode61 remove_diacritics 2')"
    )
    op.execute(
        "INSERT INTO movie_synopsis_fts (sk_movie_id, sinopse) "
        "SELECT sk_movie_id, COALESCE(sinopse, '') FROM dim_movies"
    )
    op.execute(
        "CREATE TRIGGER dim_movies_synopsis_fts_insert AFTER INSERT ON dim_movies "
        "BEGIN INSERT INTO movie_synopsis_fts (sk_movie_id, sinopse) "
        "VALUES (NEW.sk_movie_id, COALESCE(NEW.sinopse, '')); END"
    )
    op.execute(
        "CREATE TRIGGER dim_movies_synopsis_fts_update AFTER UPDATE OF sinopse ON dim_movies "
        "BEGIN DELETE FROM movie_synopsis_fts WHERE sk_movie_id = OLD.sk_movie_id; "
        "INSERT INTO movie_synopsis_fts (sk_movie_id, sinopse) "
        "VALUES (NEW.sk_movie_id, COALESCE(NEW.sinopse, '')); END"
    )
    op.execute(
        "CREATE TRIGGER dim_movies_synopsis_fts_delete AFTER DELETE ON dim_movies "
        "BEGIN DELETE FROM movie_synopsis_fts WHERE sk_movie_id = OLD.sk_movie_id; END"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS dim_movies_synopsis_fts_delete")
    op.execute("DROP TRIGGER IF EXISTS dim_movies_synopsis_fts_update")
    op.execute("DROP TRIGGER IF EXISTS dim_movies_synopsis_fts_insert")
    op.execute("DROP TABLE movie_synopsis_fts")
