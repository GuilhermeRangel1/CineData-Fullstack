"""Cria comunidades, participações e interações sociais.

Revision ID: 0010_add_communities
Revises: 0009_add_review_visibility
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_add_communities"
down_revision: str | Sequence[str] | None = "0009_add_review_visibility"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "communities",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index("ix_communities_nome", "communities", ["nome"])

    op.create_table(
        "community_memberships",
        sa.Column("community_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("community_id", "user_id"),
    )

    op.create_table(
        "community_posts",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("community_id", sa.String(length=32), nullable=False),
        sa.Column("author_id", sa.String(length=32), nullable=False),
        sa.Column("sk_movie_id", sa.String(length=64), nullable=True),
        sa.Column("conteudo", sa.String(length=4000), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sk_movie_id"], ["dim_movies.sk_movie_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_posts_community_id", "community_posts", ["community_id"])
    op.create_index("ix_community_posts_author_id", "community_posts", ["author_id"])
    op.create_index("ix_community_posts_sk_movie_id", "community_posts", ["sk_movie_id"])
    op.create_index("ix_community_posts_created_at", "community_posts", ["created_at"])

    op.create_table(
        "community_comments",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("post_id", sa.String(length=32), nullable=False),
        sa.Column("author_id", sa.String(length=32), nullable=False),
        sa.Column("conteudo", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_comments_post_id", "community_comments", ["post_id"])
    op.create_index("ix_community_comments_author_id", "community_comments", ["author_id"])

    op.create_table(
        "community_reactions",
        sa.Column("post_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("tipo", sa.String(length=20), server_default="curtir", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("tipo IN ('curtir', 'amei', 'interessante')", name="reaction_type_valid"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("community_reactions")
    op.drop_index("ix_community_comments_author_id", table_name="community_comments")
    op.drop_index("ix_community_comments_post_id", table_name="community_comments")
    op.drop_table("community_comments")
    op.drop_index("ix_community_posts_created_at", table_name="community_posts")
    op.drop_index("ix_community_posts_sk_movie_id", table_name="community_posts")
    op.drop_index("ix_community_posts_author_id", table_name="community_posts")
    op.drop_index("ix_community_posts_community_id", table_name="community_posts")
    op.drop_table("community_posts")
    op.drop_table("community_memberships")
    op.drop_index("ix_communities_nome", table_name="communities")
    op.drop_table("communities")
