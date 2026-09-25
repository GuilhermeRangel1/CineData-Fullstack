"""Dependências FastAPI para autenticar a sessão e aplicar papéis."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import PermissaoNegadaError, TokenInvalidoError
from app.db.session import get_db
from app.users.models import User
from app.users.tokens import JWT_ALGORITHM, JWT_ISSUER

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Valida o JWT e confirma que sua conta ainda existe no banco."""

    settings = get_settings()
    if credentials is None or not settings.jwt_secret_key:
        raise TokenInvalidoError

    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.PyJWTError as error:
        raise TokenInvalidoError from error

    usuario = await session.get(User, claims["sub"])
    if usuario is None:
        raise TokenInvalidoError
    return usuario


async def get_current_admin(
    usuario: Annotated[User, Depends(get_current_user)],
) -> User:
    """Exige que a conta autenticada tenha o papel administrativo atual."""

    if usuario.role != "admin":
        raise PermissaoNegadaError
    return usuario
