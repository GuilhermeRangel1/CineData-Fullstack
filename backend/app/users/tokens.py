"""Emissão de JWTs assinados pela própria aplicação."""

from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.core.errors import ConfiguracaoAutenticacaoError
from app.users.models import User
from app.users.schemas import TokenAcesso, UsuarioLeitura

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "cinedata-analytics"


def criar_token_acesso(usuario: User) -> TokenAcesso:
    """Assina uma sessão curta com a identidade e o papel da conta."""

    settings = get_settings()
    if not settings.jwt_secret_key:
        raise ConfiguracaoAutenticacaoError

    agora = datetime.now(UTC)
    expiracao = agora + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token = jwt.encode(
        {
            "sub": usuario.id,
            "email": usuario.email,
            "role": usuario.role,
            "iss": JWT_ISSUER,
            "iat": agora,
            "exp": expiracao,
        },
        settings.jwt_secret_key,
        algorithm=JWT_ALGORITHM,
    )
    return TokenAcesso(
        access_token=token,
        expires_in=int((expiracao - agora).total_seconds()),
        usuario=UsuarioLeitura.model_validate(usuario),
    )
