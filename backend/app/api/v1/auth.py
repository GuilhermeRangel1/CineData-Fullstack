"""Rotas públicas de cadastro e login local."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.users.schemas import CredenciaisLogin, TokenAcesso, UsuarioCadastro, UsuarioLeitura
from app.users.services import AuthService

auth_router = APIRouter(prefix="/auth", tags=["autenticação"])


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
