"""Rotas de descoberta e participação em comunidades."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.communities.schemas import (
    ComentarioCriacao,
    ComentarioLeitura,
    ComunidadeAtualizacao,
    ComunidadeCriacao,
    ComunidadeLeitura,
    PessoaComunidade,
    PublicacaoCriacao,
    PublicacaoLeitura,
    ReacaoCriacao,
    ReacaoResumo,
)
from app.communities.services import ComunidadesService
from app.db.session import get_db
from app.users.dependencies import get_current_admin, get_current_user
from app.users.models import User

communities_router = APIRouter(prefix="/comunidades", tags=["comunidades"])


@communities_router.get("", response_model=list[ComunidadeLeitura])
async def listar_comunidades(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ComunidadeLeitura]:
    return await ComunidadesService(session).listar()


@communities_router.post("", response_model=ComunidadeLeitura, status_code=status.HTTP_201_CREATED)
async def criar_comunidade(
    dados: ComunidadeCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin)],
) -> ComunidadeLeitura:
    del admin
    return await ComunidadesService(session).criar(dados)


@communities_router.get("/{comunidade_id}", response_model=ComunidadeLeitura)
async def obter_comunidade(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ComunidadeLeitura:
    return await ComunidadesService(session).obter(comunidade_id)


@communities_router.patch("/{comunidade_id}", response_model=ComunidadeLeitura)
async def atualizar_comunidade(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    dados: ComunidadeAtualizacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin)],
) -> ComunidadeLeitura:
    del admin
    return await ComunidadesService(session).atualizar(comunidade_id, dados)


@communities_router.post("/{comunidade_id}/visualizacoes", response_model=ComunidadeLeitura)
async def registrar_visualizacao(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ComunidadeLeitura:
    """Conta aberturas da conversa; não representa visitantes únicos."""
    return await ComunidadesService(session).registrar_visualizacao(comunidade_id)


@communities_router.delete("/{comunidade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_comunidade(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin)],
) -> Response:
    del admin
    await ComunidadesService(session).remover(comunidade_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@communities_router.get("/{comunidade_id}/membros", response_model=list[PessoaComunidade])
async def listar_membros(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[PessoaComunidade]:
    return await ComunidadesService(session).listar_membros(comunidade_id)


@communities_router.post("/{comunidade_id}/participacao", status_code=status.HTTP_204_NO_CONTENT)
async def entrar_na_comunidade(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    await ComunidadesService(session).entrar(comunidade_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@communities_router.delete("/{comunidade_id}/participacao", status_code=status.HTTP_204_NO_CONTENT)
async def sair_da_comunidade(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    await ComunidadesService(session).sair(comunidade_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@communities_router.get("/{comunidade_id}/publicacoes", response_model=list[PublicacaoLeitura])
async def listar_publicacoes(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[PublicacaoLeitura]:
    return await ComunidadesService(session).listar_publicacoes(comunidade_id)


@communities_router.post(
    "/{comunidade_id}/publicacoes",
    response_model=PublicacaoLeitura,
    status_code=status.HTTP_201_CREATED,
)
async def criar_publicacao(
    comunidade_id: Annotated[str, Path(min_length=1, max_length=32)],
    dados: PublicacaoCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> PublicacaoLeitura:
    return await ComunidadesService(session).criar_publicacao(comunidade_id, dados, usuario)


@communities_router.post(
    "/publicacoes/{publicacao_id}/comentarios",
    response_model=ComentarioLeitura,
    status_code=status.HTTP_201_CREATED,
)
async def comentar_publicacao(
    publicacao_id: Annotated[str, Path(min_length=1, max_length=32)],
    dados: ComentarioCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> ComentarioLeitura:
    return await ComunidadesService(session).comentar(publicacao_id, dados, usuario)


@communities_router.post("/publicacoes/{publicacao_id}/reacoes", response_model=list[ReacaoResumo])
async def reagir_a_publicacao(
    publicacao_id: Annotated[str, Path(min_length=1, max_length=32)],
    dados: ReacaoCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> list[ReacaoResumo]:
    return await ComunidadesService(session).reagir(publicacao_id, dados.tipo, usuario)


@communities_router.delete(
    "/publicacoes/{publicacao_id}/reacoes", status_code=status.HTTP_204_NO_CONTENT
)
async def remover_reacao(
    publicacao_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    await ComunidadesService(session).remover_reacao(publicacao_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
