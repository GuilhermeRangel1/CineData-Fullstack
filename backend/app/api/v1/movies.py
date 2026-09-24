"""Rotas HTTP do catálogo de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import Pagina
from app.db.session import get_db
from app.movies.schemas import ConsultaCatalogo, FilmeCriacao, FilmeDetalhe, FilmeResumo
from app.movies.services import CatalogoFilmesService, FilmePersistenceError, GestaoFilmesService

movies_router = APIRouter(prefix="/filmes", tags=["filmes"])


@movies_router.post("", response_model=FilmeDetalhe, status_code=status.HTTP_201_CREATED)
async def criar_filme(
    dados: FilmeCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FilmeDetalhe:
    """Cadastra um filme e seus relacionamentos obrigatórios."""

    try:
        return await GestaoFilmesService(session).criar(dados)
    except FilmePersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar o filme devido a um conflito de dados.",
        ) from error


@movies_router.get("", response_model=Pagina[FilmeResumo])
async def listar_filmes(
    consulta: Annotated[ConsultaCatalogo, Query()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Pagina[FilmeResumo]:
    """Lista filmes segundo a convenção pública do catálogo."""

    return await CatalogoFilmesService(session).listar(consulta)
