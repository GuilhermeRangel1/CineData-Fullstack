"""Rotas públicas de cadastro e login local."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.users.dependencies import get_current_user
from app.users.models import User
from app.users.profile_services import PerfilPublicoService
from app.users.schemas import (
    CredenciaisLogin,
    PerfilProprio,
    TokenAcesso,
    UsuarioAtualizacao,
    UsuarioCadastro,
    UsuarioLeitura,
)
from app.users.services import AuthService

auth_router = APIRouter(prefix="/auth", tags=["autenticação"])


@auth_router.get("/perfil", response_model=PerfilProprio)
async def obter_perfil_proprio(
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> PerfilProprio:
    """Retorna a visão completa do perfil para a própria conta autenticada."""

    return await PerfilPublicoService(session).obter_proprio(usuario.id)


@auth_router.post("/cadastro", response_model=UsuarioLeitura, status_code=status.HTTP_201_CREATED)
async def cadastrar(
    dados: UsuarioCadastro,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioLeitura:
    """Cria uma conta pública sempre com papel de usuário comum."""

    return await AuthService(session).cadastrar(dados)


@auth_router.post("/login", response_model=TokenAcesso)
async def login(
    dados: CredenciaisLogin,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenAcesso:
    """Inicia uma sessão local e devolve um token Bearer JWT."""

    return await AuthService(session).autenticar(dados)


@auth_router.patch("/perfil", response_model=UsuarioLeitura)
async def atualizar_perfil(
    dados: UsuarioAtualizacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> UsuarioLeitura:
    """Atualiza o nome ou a foto de perfil da conta autenticada."""

    return await AuthService(session).atualizar_perfil(usuario, dados)
