"""Regras de negócio de comunidades e interações sociais."""

import logging
from collections import Counter

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.communities.models import (
    Community,
    CommunityComment,
    CommunityPost,
    CommunityReaction,
    community_memberships,
)
from app.communities.schemas import (
    ComentarioCriacao,
    ComentarioLeitura,
    ComunidadeAtualizacao,
    ComunidadeCriacao,
    ComunidadeLeitura,
    PessoaComunidade,
    PublicacaoCriacao,
    PublicacaoLeitura,
    ReacaoResumo,
)
from app.core.errors import (
    ComunidadeConflitoError,
    ComunidadeNaoEncontradaError,
    FilmeNaoEncontradoError,
    FilmePersistenceError,
    ParticipacaoComunidadeConflitoError,
    ParticipacaoComunidadeNecessariaError,
    PublicacaoComunidadeNaoEncontradaError,
)
from app.movies.models import DimMovie
from app.movies.services import CatalogoFilmesService
from app.users.models import User

logger = logging.getLogger(__name__)

POST_LOAD_OPTIONS = (
    selectinload(CommunityPost.author),
    selectinload(CommunityPost.movie).selectinload(DimMovie.genres),
    selectinload(CommunityPost.movie).selectinload(DimMovie.reviews_summary),
    selectinload(CommunityPost.comments).selectinload(CommunityComment.author),
    selectinload(CommunityPost.reactions),
)


class ComunidadesService:
    """Mantém comunidades abertas, mas interações exclusivas de participantes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self) -> list[ComunidadeLeitura]:
        comunidades = await self._session.scalars(
            select(Community).order_by(func.lower(Community.nome), Community.id)
        )
        return [await self._para_comunidade(comunidade) for comunidade in comunidades]

    async def obter(self, community_id: str) -> ComunidadeLeitura:
        return await self._para_comunidade(await self._obter_comunidade(community_id))

    async def criar(self, dados: ComunidadeCriacao) -> ComunidadeLeitura:
        try:
            comunidade = Community(nome=dados.nome, descricao=dados.descricao)
            self._session.add(comunidade)
            await self._session.commit()
            await self._session.refresh(comunidade)
        except IntegrityError as error:
            await self._session.rollback()
            raise ComunidadeConflitoError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Cadastro de comunidade interrompido por falha de persistência.")
            raise FilmePersistenceError from error
        return await self._para_comunidade(comunidade)

    async def atualizar(self, community_id: str, dados: ComunidadeAtualizacao) -> ComunidadeLeitura:
        comunidade = await self._obter_comunidade(community_id)
        try:
            for campo in dados.model_fields_set:
                setattr(comunidade, campo, getattr(dados, campo))
            await self._session.commit()
            await self._session.refresh(comunidade)
        except IntegrityError as error:
            await self._session.rollback()
            raise ComunidadeConflitoError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Atualização de comunidade interrompida por falha de persistência.")
            raise FilmePersistenceError from error
        return await self._para_comunidade(comunidade)

    async def remover(self, community_id: str) -> None:
        comunidade = await self._obter_comunidade(community_id)
        try:
            await self._session.delete(comunidade)
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Remoção de comunidade interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def listar_membros(self, community_id: str) -> list[PessoaComunidade]:
        await self._obter_comunidade(community_id)
        membros = await self._session.scalars(
            select(User)
            .join(community_memberships)
            .where(community_memberships.c.community_id == community_id)
            .order_by(func.lower(User.nome), User.id)
        )
        return [self._para_pessoa(membro) for membro in membros]

    async def entrar(self, community_id: str, usuario: User) -> None:
        await self._obter_comunidade(community_id)
        try:
            await self._session.execute(
                community_memberships.insert().values(community_id=community_id, user_id=usuario.id)
            )
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ParticipacaoComunidadeConflitoError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Entrada em comunidade interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def sair(self, community_id: str, usuario: User) -> None:
        resultado = await self._session.execute(
            delete(community_memberships).where(
                community_memberships.c.community_id == community_id,
                community_memberships.c.user_id == usuario.id,
            )
        )
        if not resultado.rowcount:
            await self._session.rollback()
            raise ParticipacaoComunidadeNecessariaError
        try:
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Saída de comunidade interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def listar_publicacoes(self, community_id: str) -> list[PublicacaoLeitura]:
        await self._obter_comunidade(community_id)
        publicacoes = await self._session.scalars(
            select(CommunityPost)
            .where(CommunityPost.community_id == community_id)
            .options(*POST_LOAD_OPTIONS)
            .order_by(CommunityPost.created_at.desc(), CommunityPost.id.desc())
        )
        return [self._para_publicacao(publicacao) for publicacao in publicacoes]

    async def criar_publicacao(
        self, community_id: str, dados: PublicacaoCriacao, usuario: User
    ) -> PublicacaoLeitura:
        await self._exigir_participacao(community_id, usuario.id)
        movie = await self._obter_filme(dados.movie_id) if dados.movie_id else None
        try:
            publicacao = CommunityPost(
                community_id=community_id,
                author_id=usuario.id,
                sk_movie_id=movie.sk_movie_id if movie else None,
                conteudo=dados.conteudo,
            )
            self._session.add(publicacao)
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Publicação em comunidade interrompida por falha de persistência.")
            raise FilmePersistenceError from error
        return self._para_publicacao(await self._obter_publicacao(publicacao.id))

    async def comentar(
        self, post_id: str, dados: ComentarioCriacao, usuario: User
    ) -> ComentarioLeitura:
        publicacao = await self._obter_publicacao(post_id)
        await self._exigir_participacao(publicacao.community_id, usuario.id)
        try:
            comentario = CommunityComment(
                post_id=publicacao.id, author_id=usuario.id, conteudo=dados.conteudo
            )
            self._session.add(comentario)
            await self._session.commit()
            await self._session.refresh(comentario)
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Comentário em comunidade interrompido por falha de persistência.")
            raise FilmePersistenceError from error
        return ComentarioLeitura(
            id=comentario.id,
            conteudo=comentario.conteudo,
            autor=self._para_pessoa(usuario),
            criado_em=comentario.created_at,
        )

    async def reagir(self, post_id: str, tipo: str, usuario: User) -> list[ReacaoResumo]:
        publicacao = await self._obter_publicacao(post_id)
        await self._exigir_participacao(publicacao.community_id, usuario.id)
        try:
            reacao = await self._session.get(CommunityReaction, (publicacao.id, usuario.id))
            if reacao is None:
                self._session.add(
                    CommunityReaction(post_id=publicacao.id, user_id=usuario.id, tipo=tipo)
                )
            else:
                reacao.tipo = tipo
            await self._session.commit()
            await self._session.refresh(publicacao, attribute_names=["reactions"])
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Reação em comunidade interrompida por falha de persistência.")
            raise FilmePersistenceError from error
        return self._reacoes(publicacao)

    async def remover_reacao(self, post_id: str, usuario: User) -> None:
        publicacao = await self._obter_publicacao(post_id)
        await self._exigir_participacao(publicacao.community_id, usuario.id)
        resultado = await self._session.execute(
            delete(CommunityReaction).where(
                CommunityReaction.post_id == publicacao.id,
                CommunityReaction.user_id == usuario.id,
            )
        )
        if not resultado.rowcount:
            await self._session.rollback()
            return
        try:
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Remoção de reação em comunidade interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def _obter_comunidade(self, community_id: str) -> Community:
        comunidade = await self._session.get(Community, community_id)
        if comunidade is None:
            raise ComunidadeNaoEncontradaError
        return comunidade

    async def _obter_publicacao(self, post_id: str) -> CommunityPost:
        publicacao = await self._session.scalar(
            select(CommunityPost).where(CommunityPost.id == post_id).options(*POST_LOAD_OPTIONS)
        )
        if publicacao is None:
            raise PublicacaoComunidadeNaoEncontradaError
        return publicacao

    async def _obter_filme(self, movie_id: str) -> DimMovie:
        filme = await self._session.scalar(
            select(DimMovie)
            .where(DimMovie.id_filme == movie_id)
            .options(selectinload(DimMovie.genres), selectinload(DimMovie.reviews_summary))
        )
        if filme is None:
            raise FilmeNaoEncontradoError
        return filme

    async def _exigir_participacao(self, community_id: str, user_id: str) -> None:
        await self._obter_comunidade(community_id)
        participacao = await self._session.scalar(
            select(community_memberships.c.user_id).where(
                community_memberships.c.community_id == community_id,
                community_memberships.c.user_id == user_id,
            )
        )
        if participacao is None:
            raise ParticipacaoComunidadeNecessariaError

    async def _para_comunidade(self, comunidade: Community) -> ComunidadeLeitura:
        quantidade_membros = await self._session.scalar(
            select(func.count())
            .select_from(community_memberships)
            .where(community_memberships.c.community_id == comunidade.id)
        )
        return ComunidadeLeitura(
            id=comunidade.id,
            nome=comunidade.nome,
            descricao=comunidade.descricao,
            quantidade_membros=quantidade_membros or 0,
            criada_em=comunidade.created_at,
        )

    @staticmethod
    def _para_pessoa(usuario: User) -> PessoaComunidade:
        return PessoaComunidade(id=usuario.id, nome=usuario.nome, avatar_url=usuario.avatar_url)

    @classmethod
    def _para_comentario(cls, comentario: CommunityComment) -> ComentarioLeitura:
        return ComentarioLeitura(
            id=comentario.id,
            conteudo=comentario.conteudo,
            autor=cls._para_pessoa(comentario.author),
            criado_em=comentario.created_at,
        )

    @classmethod
    def _para_publicacao(cls, publicacao: CommunityPost) -> PublicacaoLeitura:
        return PublicacaoLeitura(
            id=publicacao.id,
            comunidade_id=publicacao.community_id,
            conteudo=publicacao.conteudo,
            autor=cls._para_pessoa(publicacao.author),
            filme=CatalogoFilmesService._para_resumo(publicacao.movie)
            if publicacao.movie
            else None,
            comentarios=[cls._para_comentario(comentario) for comentario in publicacao.comments],
            reacoes=cls._reacoes(publicacao),
            criada_em=publicacao.created_at,
        )

    @staticmethod
    def _reacoes(publicacao: CommunityPost) -> list[ReacaoResumo]:
        quantidades = Counter(reacao.tipo for reacao in publicacao.reactions)
        return [
            ReacaoResumo(tipo=tipo, quantidade=quantidades[tipo])
            for tipo in ("curtir", "amei", "interessante")
            if quantidades[tipo]
        ]
