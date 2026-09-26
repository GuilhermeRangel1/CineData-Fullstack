"""Rotas administrativas para preencher filmes com metadados externos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.core.config import get_settings
from app.integrations.tmdb import TmdbGateway, TmdbImportacao, TmdbResultado
from app.users.dependencies import get_current_admin
from app.users.models import User

external_movies_router = APIRouter(prefix="/admin/fontes/tmdb", tags=["fontes externas"])


@external_movies_router.get("/busca", response_model=list[TmdbResultado])
async def buscar_filmes_tmdb(
    busca: Annotated[str, Query(min_length=2, max_length=100)],
    admin: Annotated[User, Depends(get_current_admin)],
    ano: Annotated[int | None, Query(ge=1888, le=2100)] = None,
) -> list[TmdbResultado]:
    """Pesquisa filmes no TMDB; credenciais nunca são expostas ao frontend."""

    del admin
    return await TmdbGateway(get_settings().tmdb_api_token).buscar(busca, ano)


@external_movies_router.get("/{tmdb_id}", response_model=TmdbImportacao)
async def obter_filme_tmdb(
    tmdb_id: Annotated[int, Path(ge=1)],
    admin: Annotated[User, Depends(get_current_admin)],
) -> TmdbImportacao:
    """Obtém dados selecionados, pôsteres e trailer oficial de um filme do TMDB."""

    del admin
    return await TmdbGateway(get_settings().tmdb_api_token).obter(tmdb_id)
