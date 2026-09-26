"""Agregações leves e independentes do banco para a área administrativa."""

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas import (
    ComunidadeAnalytics,
    FilmeAnalytics,
    GeneroAnalytics,
    MetricaAnalytics,
    PontoEvolucaoAnalytics,
    ResumoAnalytics,
)
from app.communities.models import Community, CommunityPost, community_memberships
from app.movies.models import DimGenre, DimMovie, MovieReview, bridge_movie_genre
from app.users.models import User, UserList


class AnalyticsService:
    """Produz uma visão administrativa sem expor dados pessoais individuais."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def obter_resumo(self, periodo_dias: int) -> ResumoAnalytics:
        inicio = datetime.now() - timedelta(days=periodo_dias - 1)
        total_filmes = await self._contar(DimMovie)
        total_usuarios = await self._contar(User)
        total_avaliacoes = await self._contar_avaliacoes_da_comunidade()
        total_listas = await self._contar(UserList)
        total_comunidades = await self._contar(Community)

        return ResumoAnalytics(
            periodo_dias=periodo_dias,
            metricas=[
                MetricaAnalytics(
                    chave="filmes",
                    rotulo="Filmes no catálogo",
                    valor=total_filmes,
                    detalhe="Histórias disponíveis para descobrir",
                ),
                MetricaAnalytics(
                    chave="usuarios",
                    rotulo="Pessoas cadastradas",
                    valor=total_usuarios,
                    detalhe="Contas que podem participar da plataforma",
                ),
                MetricaAnalytics(
                    chave="avaliacoes",
                    rotulo="Avaliações da comunidade",
                    valor=total_avaliacoes,
                    detalhe="Opiniões publicadas por contas da plataforma",
                ),
                MetricaAnalytics(
                    chave="listas",
                    rotulo="Listas criadas",
                    valor=total_listas,
                    detalhe="Curadorias pessoais salvas",
                ),
                MetricaAnalytics(
                    chave="comunidades",
                    rotulo="Comunidades ativas",
                    valor=total_comunidades,
                    detalhe="Espaços disponíveis para conversa",
                ),
            ],
            evolucao=await self._evolucao(inicio, periodo_dias),
            generos=await self._generos(inicio),
            filmes_mais_avaliados=await self._filmes_mais_avaliados(inicio),
            comunidades_em_alta=await self._comunidades_em_alta(inicio),
        )

    async def _contar(self, modelo: type[object]) -> int:
        total = await self._session.scalar(select(func.count()).select_from(modelo))
        return int(total or 0)

    async def _contar_avaliacoes_da_comunidade(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(MovieReview)
            .where(self._avaliacao_da_comunidade())
        )
        return int(total or 0)

    @staticmethod
    def _avaliacao_da_comunidade() -> object:
        """Ignora avaliações importadas/semeadas sem uma conta associada."""
        return MovieReview.user_id.is_not(None)

    async def _evolucao(
        self, inicio: datetime, periodo_dias: int
    ) -> list[PontoEvolucaoAnalytics]:
        usuarios = await self._datas(User.created_at, inicio)
        avaliacoes = await self._datas(
            MovieReview.created_at,
            inicio,
            self._avaliacao_da_comunidade(),
        )
        listas = await self._datas(UserList.created_at, inicio)
        publicacoes = await self._datas(CommunityPost.created_at, inicio)
        fim = inicio.date() + timedelta(days=periodo_dias - 1)
        quantidade_dias = (fim - inicio.date()).days + 1
        dias = [inicio.date() + timedelta(days=indice) for indice in range(quantidade_dias)]

        return [
            PontoEvolucaoAnalytics(
                data=dia,
                usuarios=usuarios[dia],
                avaliacoes=avaliacoes[dia],
                listas=listas[dia],
                publicacoes=publicacoes[dia],
            )
            for dia in dias
        ]

    async def _datas(self, coluna: object, inicio: datetime, *filtros: object) -> Counter[date]:
        datas = await self._session.scalars(select(coluna).where(coluna >= inicio, *filtros))
        return Counter(valor.date() for valor in datas if valor is not None)

    async def _generos(self, inicio: datetime) -> list[GeneroAnalytics]:
        resultado = await self._session.execute(
            select(
                DimGenre.nome_genero,
                func.count(MovieReview.sk_movie_review_id),
                func.avg(MovieReview.nota),
            )
            .join(
                bridge_movie_genre,
                bridge_movie_genre.c.sk_genre_id == DimGenre.sk_genre_id,
            )
            .join(MovieReview, MovieReview.sk_movie_id == bridge_movie_genre.c.sk_movie_id)
            .where(self._avaliacao_da_comunidade(), MovieReview.created_at >= inicio)
            .group_by(DimGenre.sk_genre_id, DimGenre.nome_genero)
            .order_by(
                func.count(MovieReview.sk_movie_review_id).desc(),
                func.avg(MovieReview.nota).desc(),
                DimGenre.nome_genero,
            )
            .limit(8)
        )
        return [
            GeneroAnalytics(nome=nome, quantidade=int(quantidade), nota_media=nota_media)
            for nome, quantidade, nota_media in resultado
        ]

    async def _filmes_mais_avaliados(self, inicio: datetime) -> list[FilmeAnalytics]:
        avaliacoes = (
            select(
                MovieReview.sk_movie_id.label("sk_movie_id"),
                func.count(MovieReview.sk_movie_review_id).label("quantidade"),
                func.avg(MovieReview.nota).label("nota_media"),
            )
            .where(self._avaliacao_da_comunidade(), MovieReview.created_at >= inicio)
            .group_by(MovieReview.sk_movie_id)
            .subquery()
        )
        resultado = await self._session.execute(
            select(
                DimMovie.id_filme,
                DimMovie.titulo,
                DimMovie.url_poster,
                avaliacoes.c.quantidade,
                avaliacoes.c.nota_media,
            )
            .join(avaliacoes, avaliacoes.c.sk_movie_id == DimMovie.sk_movie_id)
            .order_by(
                avaliacoes.c.quantidade.desc(),
                avaliacoes.c.nota_media.desc(),
                DimMovie.titulo,
            )
            .limit(5)
        )
        return [
            FilmeAnalytics(
                id=filme_id,
                titulo=titulo,
                url_poster=url_poster,
                quantidade_avaliacoes=int(avaliacoes),
                nota_media=nota_media,
            )
            for filme_id, titulo, url_poster, avaliacoes, nota_media in resultado
        ]

    async def _comunidades_em_alta(self, inicio: datetime) -> list[ComunidadeAnalytics]:
        membros = (
            select(
                community_memberships.c.community_id.label("community_id"),
                func.count(community_memberships.c.user_id).label("membros"),
            )
            .group_by(community_memberships.c.community_id)
            .subquery()
        )
        publicacoes = (
            select(
                CommunityPost.community_id.label("community_id"),
                func.count(CommunityPost.id).label("publicacoes"),
            )
            .where(CommunityPost.created_at >= inicio)
            .group_by(CommunityPost.community_id)
            .subquery()
        )
        membros_total = func.coalesce(membros.c.membros, 0)
        publicacoes_total = func.coalesce(publicacoes.c.publicacoes, 0)
        resultado = await self._session.execute(
            select(
                Community.id,
                Community.nome,
                Community.imagem_url,
                membros_total.label("membros"),
                publicacoes_total.label("publicacoes"),
                Community.visualizacoes,
            )
            .outerjoin(membros, membros.c.community_id == Community.id)
            .outerjoin(publicacoes, publicacoes.c.community_id == Community.id)
            .order_by(
                publicacoes_total.desc(),
                membros_total.desc(),
                Community.visualizacoes.desc(),
                Community.nome,
            )
            .limit(5)
        )
        return [
            ComunidadeAnalytics(
                id=community_id,
                nome=nome,
                imagem_url=imagem_url,
                membros=int(quantidade_membros),
                publicacoes=int(quantidade_publicacoes),
                visualizacoes=visualizacoes,
            )
            for (
                community_id,
                nome,
                imagem_url,
                quantidade_membros,
                quantidade_publicacoes,
                visualizacoes,
            ) in resultado
        ]
