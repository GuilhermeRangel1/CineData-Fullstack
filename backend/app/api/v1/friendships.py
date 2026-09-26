"""Rotas autenticadas para pedidos e relações de amizade."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.users.dependencies import get_current_user
from app.users.friendship_schemas import (
    ContatoAmizade,
    RespostaSolicitacaoAmizade,
    SolicitacaoAmizadeLeitura,
)
from app.users.friendship_services import AmizadesService
from app.users.models import User

friendships_router = APIRouter(prefix="/minha-conta/amigos", tags=["amizades"])


@friendships_router.get("", response_model=list[ContatoAmizade])
async def listar_amigos(
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> list[ContatoAmizade]:
    """Lista as contas que já aceitaram uma amizade com a pessoa atual."""

    return await AmizadesService(session).listar_amigos(usuario)


@friendships_router.get("/solicitacoes", response_model=list[SolicitacaoAmizadeLeitura])
async def listar_solicitacoes(
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> list[SolicitacaoAmizadeLeitura]:
    """Lista pedidos enviados e recebidos, incluindo pedidos bloqueados."""

    return await AmizadesService(session).listar_solicitacoes(usuario)


@friendships_router.post(
    "/solicitacoes/{usuario_id}",
    response_model=SolicitacaoAmizadeLeitura,
    status_code=status.HTTP_201_CREATED,
)
async def enviar_solicitacao(
    usuario_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> SolicitacaoAmizadeLeitura:
    """Envia um pedido de amizade para outro perfil local."""

    return await AmizadesService(session).enviar_solicitacao(usuario_id, usuario)


@friendships_router.patch(
    "/solicitacoes/{solicitacao_id}", response_model=SolicitacaoAmizadeLeitura
)
async def responder_solicitacao(
    solicitacao_id: Annotated[str, Path(min_length=1, max_length=32)],
    dados: RespostaSolicitacaoAmizade,
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> SolicitacaoAmizadeLeitura:
    """Aceita ou bloqueia um pedido pendente recebido pela conta atual."""

    return await AmizadesService(session).responder(solicitacao_id, dados.acao, usuario)


@friendships_router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_amigo(
    usuario_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Encerra uma amizade aceita, sem apagar usuários ou seu histórico."""

    await AmizadesService(session).remover_amigo(usuario_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
