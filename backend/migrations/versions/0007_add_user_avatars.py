"""Adiciona fotos locais aos perfis de usuário.

Revision ID: 0007_add_user_avatars
Revises: 0006_add_trailer_to_movies
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_add_user_avatars"
down_revision: str | Sequence[str] | None = "0006_add_trailer_to_movies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("avatar_url", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("avatar_url")
