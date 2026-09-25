"""Casos de uso de cadastro, login e criação inicial de administrador."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CredenciaisInvalidasError, UsuarioJaExisteError
from app.users.models import User
from app.users.schemas import CredenciaisLogin, TokenAcesso, UsuarioCadastro, UsuarioLeitura
from app.users.security import gerar_hash_senha, verificar_senha
from app.users.tokens import criar_token_acesso


class AuthService:
    """Coordena operações locais de conta sem expor hashes de senha."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def cadastrar(self, dados: UsuarioCadastro) -> UsuarioLeitura:
        """Cria uma conta pública com papel fixo de usuário comum."""

        usuario = await self._criar_usuario(dados, role="user")
        return UsuarioLeitura.model_validate(usuario)

    async def autenticar(self, dados: CredenciaisLogin) -> TokenAcesso:
        """Valida credenciais locais e devolve um JWT de curta duração."""

        usuario = await self._session.scalar(select(User).where(User.email == dados.email))
        if usuario is None or not verificar_senha(dados.senha, usuario.password_hash):
            raise CredenciaisInvalidasError
        return criar_token_acesso(usuario)

    async def criar_administrador_inicial(
        self,
        dados: UsuarioCadastro,
    ) -> tuple[UsuarioLeitura, bool]:
        """Cria um admin apenas para o bootstrap controlado da infraestrutura."""

        usuario_existente = await self._session.scalar(
            select(User).where(User.email == dados.email)
        )
        if usuario_existente is not None:
            if usuario_existente.role == "admin":
                return UsuarioLeitura.model_validate(usuario_existente), False
            raise UsuarioJaExisteError

        usuario = await self._criar_usuario(dados, role="admin")
        return UsuarioLeitura.model_validate(usuario), True

    async def _criar_usuario(self, dados: UsuarioCadastro, *, role: str) -> User:
        usuario = User(
            email=dados.email,
            nome=dados.nome,
            password_hash=gerar_hash_senha(dados.senha),
            role=role,
        )
        self._session.add(usuario)
        try:
            await self._session.commit()
            await self._session.refresh(usuario)
        except IntegrityError as error:
            await self._session.rollback()
            raise UsuarioJaExisteError from error
        except SQLAlchemyError:
            await self._session.rollback()
            raise
        return usuario
