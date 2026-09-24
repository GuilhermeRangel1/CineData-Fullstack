"""Rotas HTTP do catálogo de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import Pagina
from app.db.session import get_db
from app.movies.schemas import ConsultaCatalogo, FilmeResumo
from app.movies.services import CatalogoFilmesService

movies_router = APIRouter(prefix="/filmes", tags=["filmes"])


@movies_router.get("", response_model=Pagina[FilmeResumo])
async def listar_filmes(
    consulta: Annotated[ConsultaCatalogo, Query()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Pagina[FilmeResumo]:
    """Lista filmes segundo a convenção pública do catálogo."""

    return await CatalogoFilmesService(session).listar(consulta)
