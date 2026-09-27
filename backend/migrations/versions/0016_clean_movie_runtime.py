"""Normalize invalid movie runtimes and reject them in SQLite."""

from collections.abc import Sequence
import logging

import sqlalchemy as sa
from alembic import op

revision: str = "0016_clean_movie_runtime"
down_revision: str | Sequence[str] | None = "0015_add_community_moderation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    result = op.get_bind().execute(
        sa.text(
            "UPDATE dim_movies SET duracao_minutos = NULL "
            "WHERE duracao_minutos IS NOT NULL AND duracao_minutos < 1"
        )
    )
    if result.rowcount:
        logger.info(
            "Normalized %s invalid movie runtimes to unknown (NULL).", result.rowcount
        )

    op.execute(
        """
        CREATE TRIGGER dim_movies_runtime_positive_insert
        BEFORE INSERT ON dim_movies
        FOR EACH ROW
        WHEN NEW.duracao_minutos IS NOT NULL AND NEW.duracao_minutos < 1
        BEGIN
            SELECT RAISE(ABORT, 'duracao_minutos must be positive or NULL');
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER dim_movies_runtime_positive_update
        BEFORE UPDATE OF duracao_minutos ON dim_movies
        FOR EACH ROW
        WHEN NEW.duracao_minutos IS NOT NULL AND NEW.duracao_minutos < 1
        BEGIN
            SELECT RAISE(ABORT, 'duracao_minutos must be positive or NULL');
        END
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS dim_movies_runtime_positive_update")
    op.execute("DROP TRIGGER IF EXISTS dim_movies_runtime_positive_insert")
