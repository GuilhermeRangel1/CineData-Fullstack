"""Registra aberturas das comunidades para ordenar a descoberta."""

import sqlalchemy as sa
from alembic import op

revision = "0011_add_community_views"
down_revision = "0010_add_communities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "communities",
        sa.Column("visualizacoes", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("communities", "visualizacoes")
