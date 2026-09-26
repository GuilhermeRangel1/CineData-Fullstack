"""Adiciona trailers opcionais aos filmes.

Revision ID: 0006_add_trailer_to_movies
Revises: 0005_add_user_lists
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_add_trailer_to_movies"
down_revision: str | Sequence[str] | None = "0005_add_user_lists"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("dim_movies") as batch_op:
        batch_op.add_column(sa.Column("url_trailer", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("dim_movies") as batch_op:
        batch_op.drop_column("url_trailer")
