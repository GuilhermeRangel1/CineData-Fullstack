"""Rotas HTTP do catálogo de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import Pagina
from app.db.session import get_db
from app.movies.schemas import (
    AvaliacaoCriacao,
    AvaliacaoLeitura,
    ConsultaCatalogo,
    FilmeAtualizacao,
    FilmeCriacao,
    FilmeDetalhe,
    FilmeResumo,
)
from app.movies.services import AvaliacoesService, CatalogoFilmesService, GestaoFilmesService

movies_router = APIRouter(prefix="/filmes", tags=["filmes"])


@movies_router.post("", response_model=FilmeDetalhe, status_code=status.HTTP_201_CREATED)
async def criar_filme(
    dados: FilmeCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FilmeDetalhe:
    """Cadastra um filme e seus relacionamentos obrigatórios."""

    return await GestaoFilmesService(session).criar(dados)


@movies_router.get("", response_model=Pagina[FilmeResumo])
async def listar_filmes(
    consulta: Annotated[ConsultaCatalogo, Query()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Pagina[FilmeResumo]:
    """Lista filmes segundo a convenção pública do catálogo."""

    return await CatalogoFilmesService(session).listar(consulta)


@movies_router.get("/{filme_id}/avaliacoes", response_model=list[AvaliacaoLeitura])
async def listar_avaliacoes(
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[AvaliacaoLeitura]:
    """Lista o histórico de avaliações de um filme, da mais recente à mais antiga."""

    return await AvaliacoesService(session).listar(filme_id)


@movies_router.post(
    "/{filme_id}/avaliacoes",
    response_model=AvaliacaoLeitura,
    status_code=status.HTTP_201_CREATED,
)
async def criar_avaliacao(
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    dados: AvaliacaoCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AvaliacaoLeitura:
    """Registra uma avaliação e atualiza a média pública do filme."""

    return await AvaliacoesService(session).criar(filme_id, dados)


@movies_router.get("/{filme_id}", response_model=FilmeDetalhe)
async def obter_filme(
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FilmeDetalhe:
    """Consulta os detalhes completos de um filme pelo seu identificador público."""

    return await CatalogoFilmesService(session).obter_detalhe(filme_id)


@movies_router.patch("/{filme_id}", response_model=FilmeDetalhe)
async def atualizar_filme(
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    dados: FilmeAtualizacao,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FilmeDetalhe:
    """Atualiza parcialmente um filme pelo seu identificador público."""

    return await GestaoFilmesService(session).atualizar(filme_id, dados)


@movies_router.delete("/{filme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_filme(
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Remove um filme pelo seu identificador público."""

    await GestaoFilmesService(session).remover(filme_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
