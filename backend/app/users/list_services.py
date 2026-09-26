"""Casos de uso de listas pessoais e das listas virtuais da conta."""

import logging

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import (
    FilmeJaEstaNaListaError,
    FilmeNaoEncontradoError,
    FilmePersistenceError,
    ListaNaoEncontradaError,
)
from app.movies.models import DimMovie, MovieReview
from app.movies.services import CatalogoFilmesService
from app.users.list_schemas import ListaAtualizacao, ListaCriacao, ListaDetalhe, ListaLeitura
from app.users.models import User, UserList, watch_later_movies

logger = logging.getLogger(__name__)


class ListasService:
    """Mantém listas personalizadas e referências ao catálogo, sem duplicar filmes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self, user: User) -> list[ListaLeitura]:
        listas = await self._session.scalars(
            select(UserList)
            .where(UserList.user_id == user.id)
            .options(selectinload(UserList.movies))
            .order_by(UserList.created_at.desc(), UserList.id.desc())
        )
        return [self._para_leitura(lista) for lista in listas]

    async def criar(self, dados: ListaCriacao, user: User) -> ListaLeitura:
        try:
            lista = UserList(user_id=user.id, nome=dados.nome, visibilidade=dados.visibilidade)
            self._session.add(lista)
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Cadastro de lista interrompido por falha de persistência.")
            raise FilmePersistenceError from error
        return ListaLeitura(
            id=lista.id,
            nome=lista.nome,
            visibilidade=lista.visibilidade,
            quantidade_filmes=0,
            criada_em=lista.created_at,
        )

    async def obter(self, list_id: str, user: User) -> ListaDetalhe:
        lista = await self._obter_lista(list_id, user.id)
        return ListaDetalhe(
            **self._para_leitura(lista).model_dump(), filmes=self._resumos(lista.movies)
        )

    async def atualizar(self, list_id: str, dados: ListaAtualizacao, user: User) -> ListaLeitura:
        lista = await self._obter_lista(list_id, user.id)
        try:
            for campo in dados.model_fields_set:
                setattr(lista, campo, getattr(dados, campo))
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Atualização de lista interrompida por falha de persistência.")
            raise FilmePersistenceError from error
        return self._para_leitura(lista)

    async def remover(self, list_id: str, user: User) -> None:
        lista = await self._obter_lista(list_id, user.id)
        try:
            await self._session.delete(lista)
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Remoção de lista interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def adicionar_filme(self, list_id: str, movie_id: str, user: User) -> ListaDetalhe:
        lista = await self._obter_lista(list_id, user.id)
        filme = await self._obter_filme(movie_id)
        if any(item.sk_movie_id == filme.sk_movie_id for item in lista.movies):
            raise FilmeJaEstaNaListaError
        try:
            lista.movies.append(filme)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise FilmeJaEstaNaListaError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Inclusão em lista interrompida por falha de persistência.")
            raise FilmePersistenceError from error
        return await self.obter(list_id, user)

    async def remover_filme(self, list_id: str, movie_id: str, user: User) -> None:
        lista = await self._obter_lista(list_id, user.id)
        filme = next((item for item in lista.movies if item.id_filme == movie_id), None)
        if filme is None:
            raise FilmeNaoEncontradoError
        try:
            lista.movies.remove(filme)
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Remoção de filme da lista interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def listar_assistir_depois(self, user: User):
        filmes = await self._session.scalars(
            select(DimMovie)
            .join(watch_later_movies)
            .where(watch_later_movies.c.user_id == user.id)
            .options(selectinload(DimMovie.genres), selectinload(DimMovie.reviews_summary))
            .order_by(watch_later_movies.c.created_at.desc(), DimMovie.id_filme.desc())
        )
        return self._resumos(list(filmes))

    async def adicionar_assistir_depois(self, movie_id: str, user: User) -> None:
        filme = await self._obter_filme(movie_id)
        try:
            await self._session.execute(
                watch_later_movies.insert().values(user_id=user.id, sk_movie_id=filme.sk_movie_id)
            )
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise FilmeJaEstaNaListaError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Inclusão em assistir depois interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def remover_assistir_depois(self, movie_id: str, user: User) -> None:
        filme = await self._obter_filme(movie_id)
        try:
            resultado = await self._session.execute(
                delete(watch_later_movies).where(
                    watch_later_movies.c.user_id == user.id,
                    watch_later_movies.c.sk_movie_id == filme.sk_movie_id,
                )
            )
            if not resultado.rowcount:
                raise FilmeNaoEncontradoError
            await self._session.commit()
        except FilmeNaoEncontradoError:
            await self._session.rollback()
            raise
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Remoção de assistir depois interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def listar_filmes_avaliados(self, user: User):
        avaliacoes = await self._session.scalars(
            select(MovieReview)
            .where(MovieReview.user_id == user.id)
            .options(
                selectinload(MovieReview.movie).selectinload(DimMovie.genres),
                selectinload(MovieReview.movie).selectinload(DimMovie.reviews_summary),
            )
            .order_by(MovieReview.created_at.desc(), MovieReview.sk_movie_review_id.desc())
        )
        filmes_unicos: list[DimMovie] = []
        ids_vistos: set[str] = set()
        for avaliacao in avaliacoes:
            if avaliacao.sk_movie_id not in ids_vistos:
                filmes_unicos.append(avaliacao.movie)
                ids_vistos.add(avaliacao.sk_movie_id)
        return self._resumos(filmes_unicos)

    async def _obter_lista(self, list_id: str, user_id: str) -> UserList:
        lista = await self._session.scalar(
            select(UserList)
            .where(UserList.id == list_id, UserList.user_id == user_id)
            .options(
                selectinload(UserList.movies).selectinload(DimMovie.genres),
                selectinload(UserList.movies).selectinload(DimMovie.reviews_summary),
            )
        )
        if lista is None:
            raise ListaNaoEncontradaError
        return lista

    async def _obter_filme(self, movie_id: str) -> DimMovie:
        filme = await self._session.scalar(
            select(DimMovie)
            .where(DimMovie.id_filme == movie_id)
            .options(selectinload(DimMovie.genres), selectinload(DimMovie.reviews_summary))
        )
        if filme is None:
            raise FilmeNaoEncontradoError
        return filme

    @staticmethod
    def _resumos(filmes: list[DimMovie]):
        return [CatalogoFilmesService._para_resumo(filme) for filme in filmes]

    @staticmethod
    def _para_leitura(lista: UserList) -> ListaLeitura:
        return ListaLeitura(
            id=lista.id,
            nome=lista.nome,
            visibilidade=lista.visibilidade,
            quantidade_filmes=len(lista.movies),
            criada_em=lista.created_at,
        )
