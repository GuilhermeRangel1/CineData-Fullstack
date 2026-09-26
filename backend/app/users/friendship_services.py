"""Casos de uso de pedidos e relações de amizade."""

import logging

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.errors import (
    AmizadeConflitoError,
    FilmePersistenceError,
    PerfilNaoEncontradoError,
    SolicitacaoAmizadeInvalidaError,
    SolicitacaoAmizadeNaoEncontradaError,
)
from app.users.friendship_schemas import ContatoAmizade, SolicitacaoAmizadeLeitura
from app.users.models import FriendshipRequest, User

logger = logging.getLogger(__name__)


class AmizadesService:
    """Mantém pedidos direcionados, sem criar relações duplicadas entre duas contas."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enviar_solicitacao(
        self, destinatario_id: str, usuario: User
    ) -> SolicitacaoAmizadeLeitura:
        if destinatario_id == usuario.id:
            raise SolicitacaoAmizadeInvalidaError
        destinatario = await self._session.get(User, destinatario_id)
        if destinatario is None:
            raise PerfilNaoEncontradoError
        existente = await self._session.scalar(
            select(FriendshipRequest).where(
                or_(
                    and_(
                        FriendshipRequest.requester_id == usuario.id,
                        FriendshipRequest.recipient_id == destinatario_id,
                    ),
                    and_(
                        FriendshipRequest.requester_id == destinatario_id,
                        FriendshipRequest.recipient_id == usuario.id,
                    ),
                )
            )
        )
        if existente is not None:
            raise AmizadeConflitoError
        try:
            solicitacao = FriendshipRequest(requester_id=usuario.id, recipient_id=destinatario_id)
            self._session.add(solicitacao)
            await self._session.commit()
            await self._session.refresh(solicitacao)
        except IntegrityError as error:
            await self._session.rollback()
            raise AmizadeConflitoError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Pedido de amizade interrompido por falha de persistência.")
            raise FilmePersistenceError from error
        return self._para_solicitacao(solicitacao, "enviada", destinatario)

    async def listar_solicitacoes(self, usuario: User) -> list[SolicitacaoAmizadeLeitura]:
        enviado = await self._session.execute(
            select(FriendshipRequest, User)
            .join(User, User.id == FriendshipRequest.recipient_id)
            .where(FriendshipRequest.requester_id == usuario.id)
            .order_by(FriendshipRequest.created_at.desc(), FriendshipRequest.id.desc())
        )
        recebido = await self._session.execute(
            select(FriendshipRequest, User)
            .join(User, User.id == FriendshipRequest.requester_id)
            .where(FriendshipRequest.recipient_id == usuario.id)
            .order_by(FriendshipRequest.created_at.desc(), FriendshipRequest.id.desc())
        )
        itens = [
            self._para_solicitacao(solicitacao, "enviada", contato)
            for solicitacao, contato in enviado.tuples()
        ]
        itens.extend(
            self._para_solicitacao(solicitacao, "recebida", contato)
            for solicitacao, contato in recebido.tuples()
        )
        return sorted(itens, key=lambda item: (item.criada_em, item.id), reverse=True)

    async def responder(
        self, solicitacao_id: str, acao: str, usuario: User
    ) -> SolicitacaoAmizadeLeitura:
        solicitacao = await self._session.scalar(
            select(FriendshipRequest).where(
                FriendshipRequest.id == solicitacao_id,
                FriendshipRequest.recipient_id == usuario.id,
                FriendshipRequest.status == "pendente",
            )
        )
        if solicitacao is None:
            raise SolicitacaoAmizadeNaoEncontradaError
        solicitacao.status = "aceita" if acao == "aceitar" else "bloqueada"
        try:
            await self._session.commit()
            await self._session.refresh(solicitacao)
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Resposta de amizade interrompida por falha de persistência.")
            raise FilmePersistenceError from error
        solicitante = await self._session.get(User, solicitacao.requester_id)
        if solicitante is None:
            raise SolicitacaoAmizadeNaoEncontradaError
        return self._para_solicitacao(solicitacao, "recebida", solicitante)

    async def listar_amigos(self, usuario: User) -> list[ContatoAmizade]:
        contato = aliased(User)
        amigos = await self._session.execute(
            select(contato)
            .join(
                FriendshipRequest,
                or_(
                    and_(
                        FriendshipRequest.requester_id == usuario.id,
                        FriendshipRequest.recipient_id == contato.id,
                    ),
                    and_(
                        FriendshipRequest.recipient_id == usuario.id,
                        FriendshipRequest.requester_id == contato.id,
                    ),
                ),
            )
            .where(FriendshipRequest.status == "aceita")
            .order_by(func.lower(contato.nome), contato.id)
        )
        return [self._para_contato(amigo) for amigo in amigos.scalars()]

    async def pesquisar_pessoas(self, busca: str, usuario: User) -> list[ContatoAmizade]:
        termo = f"%{busca.strip().lower()}%"
        resultado = await self._session.execute(
            select(User)
            .where(User.id != usuario.id, func.lower(User.nome).like(termo))
            .order_by(func.lower(User.nome), User.id)
            .limit(8)
        )
        return [self._para_contato(pessoa) for pessoa in resultado.scalars()]

    async def remover_amigo(self, amigo_id: str, usuario: User) -> None:
        resultado = await self._session.execute(
            delete(FriendshipRequest).where(
                FriendshipRequest.status == "aceita",
                or_(
                    and_(
                        FriendshipRequest.requester_id == usuario.id,
                        FriendshipRequest.recipient_id == amigo_id,
                    ),
                    and_(
                        FriendshipRequest.requester_id == amigo_id,
                        FriendshipRequest.recipient_id == usuario.id,
                    ),
                ),
            )
        )
        if not resultado.rowcount:
            await self._session.rollback()
            raise SolicitacaoAmizadeNaoEncontradaError
        try:
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Remoção de amizade interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    @staticmethod
    def _para_contato(usuario: User) -> ContatoAmizade:
        return ContatoAmizade(id=usuario.id, nome=usuario.nome, avatar_url=usuario.avatar_url)

    @classmethod
    def _para_solicitacao(
        cls, solicitacao: FriendshipRequest, direcao: str, contato: User
    ) -> SolicitacaoAmizadeLeitura:
        return SolicitacaoAmizadeLeitura(
            id=solicitacao.id,
            status=solicitacao.status,
            direcao=direcao,
            pessoa=cls._para_contato(contato),
            criada_em=solicitacao.created_at,
        )
