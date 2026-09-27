"""Normalize unrated scores and validate imported performance metrics."""

from collections.abc import Sequence
import logging

import sqlalchemy as sa
from alembic import op

revision: str = "0017_validate_movie_performance"
down_revision: str | Sequence[str] | None = "0016_clean_movie_runtime"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger("alembic.runtime.migration")

INVALID_PERFORMANCE = """
    (orcamento_usd IS NOT NULL AND orcamento_usd < 0)
    OR (receita_usd IS NOT NULL AND receita_usd < 0)
    OR (orcamento_brl IS NOT NULL AND orcamento_brl < 0)
    OR (receita_brl IS NOT NULL AND receita_brl < 0)
    OR (popularidade IS NOT NULL AND popularidade < 0)
    OR (nota_tmdb IS NOT NULL AND (nota_tmdb < 0 OR nota_tmdb > 10))
    OR (nota_imdb IS NOT NULL AND (nota_imdb < 0 OR nota_imdb > 10))
    OR (qtd_tmdb IS NOT NULL AND qtd_tmdb < 0)
    OR (qtd_imdb IS NOT NULL AND qtd_imdb < 0)
"""

INVALID_PERFORMANCE_TRIGGER = """
    (NEW.orcamento_usd IS NOT NULL AND NEW.orcamento_usd < 0)
    OR (NEW.receita_usd IS NOT NULL AND NEW.receita_usd < 0)
    OR (NEW.orcamento_brl IS NOT NULL AND NEW.orcamento_brl < 0)
    OR (NEW.receita_brl IS NOT NULL AND NEW.receita_brl < 0)
    OR (NEW.popularidade IS NOT NULL AND NEW.popularidade < 0)
    OR (NEW.nota_tmdb IS NOT NULL AND (NEW.nota_tmdb < 0 OR NEW.nota_tmdb > 10))
    OR (NEW.nota_imdb IS NOT NULL AND (NEW.nota_imdb < 0 OR NEW.nota_imdb > 10))
    OR (NEW.qtd_tmdb IS NOT NULL AND NEW.qtd_tmdb < 0)
    OR (NEW.qtd_imdb IS NOT NULL AND NEW.qtd_imdb < 0)
    OR (NEW.qtd_tmdb = 0 AND NEW.nota_tmdb IS NOT NULL)
    OR (NEW.qtd_imdb = 0 AND NEW.nota_imdb IS NOT NULL)
"""


def upgrade() -> None:
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            """
            UPDATE fact_movies_performance
            SET
                orcamento_usd = CASE WHEN orcamento_usd < 0 THEN NULL ELSE orcamento_usd END,
                receita_usd = CASE WHEN receita_usd < 0 THEN NULL ELSE receita_usd END,
                orcamento_brl = CASE WHEN orcamento_brl < 0 THEN NULL ELSE orcamento_brl END,
                receita_brl = CASE WHEN receita_brl < 0 THEN NULL ELSE receita_brl END,
                popularidade = CASE WHEN popularidade < 0 THEN NULL ELSE popularidade END,
                nota_tmdb = CASE
                    WHEN nota_tmdb < 0 OR nota_tmdb > 10 OR qtd_tmdb <= 0 THEN NULL
                    ELSE nota_tmdb
                END,
                nota_imdb = CASE
                    WHEN nota_imdb < 0 OR nota_imdb > 10 OR qtd_imdb <= 0 THEN NULL
                    ELSE nota_imdb
                END,
                qtd_tmdb = CASE WHEN qtd_tmdb < 0 THEN NULL ELSE qtd_tmdb END,
                qtd_imdb = CASE WHEN qtd_imdb < 0 THEN NULL ELSE qtd_imdb END
            WHERE
            """ + INVALID_PERFORMANCE + """
                OR (qtd_tmdb = 0 AND nota_tmdb IS NOT NULL)
                OR (qtd_imdb = 0 AND nota_imdb IS NOT NULL)
            """
        )
    )
    if result.rowcount:
        logger.info("Normalized %s inconsistent movie performance rows.", result.rowcount)

    for event in ("INSERT", "UPDATE"):
        suffix = event.lower()
        op.execute(
            f"""
            CREATE TRIGGER fact_movies_performance_validate_{suffix}
            BEFORE {event} ON fact_movies_performance
            FOR EACH ROW
            WHEN {INVALID_PERFORMANCE_TRIGGER}
            BEGIN
                SELECT RAISE(ABORT, 'invalid movie performance metrics');
            END
            """
        )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS fact_movies_performance_validate_update")
    op.execute("DROP TRIGGER IF EXISTS fact_movies_performance_validate_insert")
