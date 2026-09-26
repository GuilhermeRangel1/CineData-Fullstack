"""Adiciona imagem opcional às comunidades."""

import sqlalchemy as sa
from alembic import op

revision = "0012_add_community_image"
down_revision = "0011_add_community_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("communities", sa.Column("imagem_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("communities", "imagem_url")
