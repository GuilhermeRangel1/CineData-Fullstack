"""Permite remover o conteúdo de mensagens sem apagar a conversa."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_add_community_moderation"
down_revision: str | Sequence[str] | None = "0014_add_taste_map_synopsis_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("community_posts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "removida_por_moderacao", sa.Boolean(), server_default=sa.false(), nullable=False
            )
        )
    with op.batch_alter_table("community_comments") as batch_op:
        batch_op.add_column(
            sa.Column(
                "removida_por_moderacao", sa.Boolean(), server_default=sa.false(), nullable=False
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("community_comments") as batch_op:
        batch_op.drop_column("removida_por_moderacao")
    with op.batch_alter_table("community_posts") as batch_op:
        batch_op.drop_column("removida_por_moderacao")
