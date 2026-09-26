"""Define visibilidade pública ou privada para novas avaliações.

Revision ID: 0009_add_review_visibility
Revises: 0008_add_friendship_requests
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_add_review_visibility"
down_revision: str | Sequence[str] | None = "0008_add_friendship_requests"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("movie_reviews") as batch_op:
        batch_op.add_column(
            sa.Column("visibilidade", sa.String(length=20), server_default="publica", nullable=False)
        )
        batch_op.create_check_constraint(
            "visibility_valid", "visibilidade IN ('publica', 'privada')"
        )
        batch_op.create_index("ix_movie_reviews_visibilidade", ["visibilidade"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("movie_reviews") as batch_op:
        batch_op.drop_index("ix_movie_reviews_visibilidade")
        batch_op.drop_constraint("ck_movie_reviews_visibility_valid", type_="check")
        batch_op.drop_column("visibilidade")
