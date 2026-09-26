"""Rotas públicas de perfis locais."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.users.profile_services import PerfilPublicoService
from app.users.schemas import PerfilPublico

profiles_router = APIRouter(prefix="/perfis", tags=["perfis"])


@profiles_router.get("/{usuario_id}", response_model=PerfilPublico)
async def obter_perfil(
    usuario_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PerfilPublico:
    """Expõe somente dados sociais intencionalmente públicos de uma conta."""

    return await PerfilPublicoService(session).obter(usuario_id)
