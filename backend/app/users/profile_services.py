"""Leitura segura dos perfis públicos locais."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import PerfilNaoEncontradoError
from app.movies.models import DimMovie, MovieReview
from app.movies.schemas import AvaliacaoLeitura
from app.movies.services import CatalogoFilmesService
from app.users.models import FriendshipRequest, User, UserList
from app.users.schemas import AvaliacaoPerfil, ListaPublica, PerfilPublico


class PerfilPublicoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obter(self, user_id: str) -> PerfilPublico:
        usuario = await self._session.scalar(
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
        if usuario is None:
            raise PerfilNaoEncontradoError
        quantidade_amigos = await self._session.scalar(
            select(func.count())
            .select_from(FriendshipRequest)
            .where(
                FriendshipRequest.status == "aceita",
                or_(
                    FriendshipRequest.requester_id == usuario.id,
                    FriendshipRequest.recipient_id == usuario.id,
                ),
            )
        )
        avaliacoes = await self._session.scalars(
            select(MovieReview)
            .where(MovieReview.user_id == usuario.id)
            .options(
                selectinload(MovieReview.movie).selectinload(DimMovie.genres),
                selectinload(MovieReview.movie).selectinload(DimMovie.reviews_summary),
            )
            .order_by(MovieReview.created_at.desc(), MovieReview.sk_movie_review_id.desc())
        )
        return PerfilPublico(
            id=usuario.id,
            nome=usuario.nome,
            avatar_url=usuario.avatar_url,
            quantidade_amigos=quantidade_amigos or 0,
            avaliacoes=[
                AvaliacaoPerfil(
                    **AvaliacaoLeitura(
                        id=avaliacao.sk_movie_review_id,
                        nome=avaliacao.nome,
                        nota=avaliacao.nota,
                        comentario=avaliacao.comentario,
                        criada_em=avaliacao.created_at,
                    ).model_dump(),
                    filme=CatalogoFilmesService._para_resumo(avaliacao.movie),
                )
                for avaliacao in avaliacoes
            ],
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
        )
