"""Rotas do mapa de gostos pessoal."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.taste_map.schemas import MapaGostos
from app.taste_map.services import MapaGostosService
from app.users.dependencies import get_current_user
from app.users.models import User

taste_map_router = APIRouter(prefix="/mapa-de-gostos", tags=["mapa de gostos"])


@taste_map_router.get("", response_model=MapaGostos)
async def obter_mapa_de_gostos(
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
    limite_nos: Annotated[int, Query(ge=6, le=48)] = 24,
    vizinhos_por_filme: Annotated[int, Query(ge=1, le=6)] = 3,
    busca: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    excluir: Annotated[list[str] | None, Query(max_length=48)] = None,
) -> MapaGostos:
    """Entrega somente uma malha navegável para a conta autenticada."""

    return await MapaGostosService(session).obter(
        usuario,
        limite_nos=limite_nos,
        vizinhos_por_filme=vizinhos_por_filme,
        busca=busca,
        excluir=set(excluir or []),
    )
