"""Modelos persistentes das comunidades e suas interações."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.movies.models import DimMovie
from app.users.models import User

REACTION_TYPES: tuple[str, ...] = ("curtir", "amei", "interessante")


def generate_community_id() -> str:
    """Gera identificadores opacos para entidades do domínio social."""

    return uuid4().hex


community_memberships = Table(
    "community_memberships",
    Base.metadata,
    Column(
        "community_id",
        String(32),
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id",
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


class Community(Base):
    """Espaço de conversa administrado, mas aberto para descoberta."""

    __tablename__ = "communities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_community_id)
    nome: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    descricao: Mapped[str] = mapped_column(String(1000))
    visualizacoes: Mapped[int] = mapped_column(default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list[User]] = relationship(secondary=community_memberships)
    posts: Mapped[list["CommunityPost"]] = relationship(
        back_populates="community",
        cascade="all, delete-orphan",
        order_by="CommunityPost.created_at.desc()",
    )


class CommunityPost(Base):
    """Publicação de uma pessoa participante, com menção opcional a um filme."""

    __tablename__ = "community_posts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_community_id)
    community_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("communities.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sk_movie_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("dim_movies.sk_movie_id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    conteudo: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    community: Mapped[Community] = relationship(back_populates="posts")
    author: Mapped[User] = relationship()
    movie: Mapped[DimMovie | None] = relationship()
    comments: Mapped[list["CommunityComment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="CommunityComment.created_at",
    )
    reactions: Mapped[list["CommunityReaction"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class CommunityComment(Base):
    """Comentário associado a uma publicação de comunidade."""

    __tablename__ = "community_comments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_community_id)
    post_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("community_posts.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    conteudo: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    post: Mapped[CommunityPost] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()


class CommunityReaction(Base):
    """Uma reação simples por pessoa em cada publicação."""

    __tablename__ = "community_reactions"
    __table_args__ = (
        CheckConstraint(
            "tipo IN (" + ", ".join(f"'{reaction}'" for reaction in REACTION_TYPES) + ")",
            name="reaction_type_valid",
        ),
    )

    post_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("community_posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    tipo: Mapped[str] = mapped_column(String(20), default="curtir", server_default="curtir")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    post: Mapped[CommunityPost] = relationship(back_populates="reactions")
