"""Leitura segura dos perfis públicos locais."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.communities.models import Community, community_memberships
from app.core.errors import PerfilNaoEncontradoError
from app.movies.models import DimMovie, MovieReview
from app.movies.schemas import AvaliacaoLeitura
from app.movies.services import CatalogoFilmesService
from app.users.models import FriendshipRequest, User, UserList
from app.users.schemas import (
    AvaliacaoPerfil,
    ComunidadePerfil,
    ListaPerfilProprio,
    ListaPublica,
    PerfilProprio,
    PerfilPublico,
)


class PerfilPublicoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obter(self, user_id: str) -> PerfilPublico:
        usuario = await self._obter_usuario(user_id)
        if usuario is None:
            raise PerfilNaoEncontradoError
        quantidade_amigos = await self._quantidade_amigos(usuario.id)
        avaliacoes = await self._avaliacoes(usuario.id, apenas_publicas=True)
        comunidades = await self._comunidades(usuario.id)
        return PerfilPublico(
            id=usuario.id,
            nome=usuario.nome,
            avatar_url=usuario.avatar_url,
            quantidade_amigos=quantidade_amigos,
            avaliacoes=self._serializar_avaliacoes(avaliacoes),
            listas_publicas=[
                ListaPublica(
                    id=lista.id,
                    nome=lista.nome,
                    quantidade_filmes=len(lista.movies),
                    filmes=[CatalogoFilmesService._para_resumo(filme) for filme in lista.movies],
                )
                for lista in usuario.lists
                if lista.visibilidade == "publica"
            ],
            comunidades=self._serializar_comunidades(comunidades),
        )

    async def obter_proprio(self, user_id: str) -> PerfilProprio:
        """Mostra ao dono suas listas e avaliações privadas junto das públicas."""

        usuario = await self._obter_usuario(user_id)
        if usuario is None:
            raise PerfilNaoEncontradoError
        quantidade_amigos = await self._quantidade_amigos(usuario.id)
        avaliacoes = await self._avaliacoes(usuario.id, apenas_publicas=False)
        comunidades = await self._comunidades(usuario.id)
        return PerfilProprio(
            id=usuario.id,
            nome=usuario.nome,
            avatar_url=usuario.avatar_url,
            quantidade_amigos=quantidade_amigos,
            avaliacoes=self._serializar_avaliacoes(avaliacoes),
            listas=[
                ListaPerfilProprio(
                    id=lista.id,
                    nome=lista.nome,
                    visibilidade=lista.visibilidade,
                    quantidade_filmes=len(lista.movies),
                    filmes=[CatalogoFilmesService._para_resumo(filme) for filme in lista.movies],
                )
                for lista in usuario.lists
            ],
            comunidades=self._serializar_comunidades(comunidades),
        )

    async def _obter_usuario(self, user_id: str) -> User | None:
        return await self._session.scalar(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.lists)
                .selectinload(UserList.movies)
                .selectinload(DimMovie.genres),
                selectinload(User.lists)
                .selectinload(UserList.movies)
                .selectinload(DimMovie.reviews_summary),
            )
        )

    async def _quantidade_amigos(self, user_id: str) -> int:
        quantidade_amigos = await self._session.scalar(
            select(func.count())
            .select_from(FriendshipRequest)
            .where(
                FriendshipRequest.status == "aceita",
                or_(
                    FriendshipRequest.requester_id == user_id,
                    FriendshipRequest.recipient_id == user_id,
                ),
            )
        )
        return quantidade_amigos or 0

    async def _avaliacoes(self, user_id: str, *, apenas_publicas: bool) -> list[MovieReview]:
        consulta = select(MovieReview).where(MovieReview.user_id == user_id)
        if apenas_publicas:
            consulta = consulta.where(MovieReview.visibilidade == "publica")
        avaliacoes = await self._session.scalars(
            consulta
            .options(
                selectinload(MovieReview.movie).selectinload(DimMovie.genres),
                selectinload(MovieReview.movie).selectinload(DimMovie.reviews_summary),
            )
            .order_by(MovieReview.created_at.desc(), MovieReview.sk_movie_review_id.desc())
            .limit(5)
        )
        return list(avaliacoes)

    async def _comunidades(self, user_id: str) -> list[Community]:
        comunidades = await self._session.scalars(
            select(Community)
            .join(
                community_memberships,
                community_memberships.c.community_id == Community.id,
            )
            .where(community_memberships.c.user_id == user_id)
            .order_by(func.lower(Community.nome), Community.id)
        )
        return list(comunidades)

    @staticmethod
    def _serializar_avaliacoes(avaliacoes: list[MovieReview]) -> list[AvaliacaoPerfil]:
        return [
                AvaliacaoPerfil(
                    **AvaliacaoLeitura(
                        id=avaliacao.sk_movie_review_id,
                        nome=avaliacao.nome,
                        nota=avaliacao.nota,
                        comentario=avaliacao.comentario,
                        visibilidade=avaliacao.visibilidade,
                        criada_em=avaliacao.created_at,
                    ).model_dump(),
                    filme=CatalogoFilmesService._para_resumo(avaliacao.movie),
                )
                for avaliacao in avaliacoes
            ]

    @staticmethod
    def _serializar_comunidades(comunidades: list[Community]) -> list[ComunidadePerfil]:
        return [
                ComunidadePerfil(
                    id=comunidade.id,
                    nome=comunidade.nome,
                    descricao=comunidade.descricao,
                )
                for comunidade in comunidades
            ]
