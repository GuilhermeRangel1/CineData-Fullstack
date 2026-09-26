"""Rotas do painel administrativo de analytics."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas import ResumoAnalytics
from app.analytics.services import AnalyticsService
from app.db.session import get_db
from app.users.dependencies import get_current_admin
from app.users.models import User

analytics_router = APIRouter(prefix="/admin/analytics", tags=["analytics"])


@analytics_router.get("/resumo", response_model=ResumoAnalytics)
async def obter_resumo_analytics(
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin)],
    periodo_dias: Annotated[int, Query(ge=1, le=90)] = 30,
) -> ResumoAnalytics:
    """Consolida atividade, catálogo e comunidades para contas administrativas."""

    del admin
    return await AnalyticsService(session).obter_resumo(periodo_dias)
