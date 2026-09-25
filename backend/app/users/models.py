"""Modelo persistente de contas locais.

As contas são independentes dos dados importados do catálogo. Relações com
avaliações, listas e comunidades serão introduzidas em migrações próprias.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

USER_ROLES: tuple[str, ...] = ("user", "admin")


def generate_user_id() -> str:
    """Gera um identificador opaco para uma conta local."""

    return uuid4().hex


class User(Base):
    """Conta autenticável por e-mail e senha."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN (" + ", ".join(f"'{role}'" for role in USER_ROLES) + ")",
            name="role_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_user_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        server_default="user",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
