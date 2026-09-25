from collections.abc import AsyncIterator

import httpx
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.users.models import User
from app.users.schemas import UsuarioCadastro
from app.users.services import AuthService


@pytest.fixture
async def user_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield session_factory
    finally:
        await engine.dispose()


async def test_public_registration_creates_only_a_standard_user(
    user_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with user_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/cadastro",
                json={
                    "email": "ANA@EXAMPLE.COM",
                    "nome": "Ana Exemplo",
                    "senha": "senha-local-segura",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "email": "ana@example.com",
        "nome": "Ana Exemplo",
        "role": "user",
        "created_at": response.json()["created_at"],
    }

    async with user_session_factory() as session:
        usuario = await session.scalar(select(User).where(User.email == "ana@example.com"))
    assert usuario is not None
    assert usuario.role == "user"
    assert usuario.password_hash != "senha-local-segura"


async def test_registration_rejects_an_administrator_role_from_the_public_request(
    user_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with user_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/cadastro",
                json={
                    "email": "admin@example.com",
                    "nome": "Tentativa de Admin",
                    "senha": "senha-local-segura",
                    "role": "admin",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


async def test_login_returns_a_signed_bearer_token(
    user_session_factory: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "segredo-de-teste-com-tamanho-suficiente")
    get_settings.cache_clear()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with user_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            cadastro = await client.post(
                "/api/v1/auth/cadastro",
                json={
                    "email": "ana@example.com",
                    "nome": "Ana Exemplo",
                    "senha": "senha-local-segura",
                },
            )
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "ana@example.com", "senha": "senha-local-segura"},
            )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert cadastro.status_code == 201
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 3600
    claims = jwt.decode(
        payload["access_token"],
        "segredo-de-teste-com-tamanho-suficiente",
        algorithms=["HS256"],
        issuer="cinedata-analytics",
    )
    assert claims["email"] == "ana@example.com"
    assert claims["role"] == "user"


async def test_login_does_not_reveal_which_credential_is_invalid(
    user_session_factory: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "segredo-de-teste-com-tamanho-suficiente")
    get_settings.cache_clear()

    async with user_session_factory() as session:
        await AuthService(session).cadastrar(
            UsuarioCadastro(
                email="ana@example.com",
                nome="Ana Exemplo",
                senha="senha-local-segura",
            )
        )

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with user_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "ana@example.com", "senha": "senha-incorreta"},
            )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert response.status_code == 401
    assert response.json() == {
        "codigo": "CREDENCIAIS_INVALIDAS",
        "mensagem": "E-mail ou senha inválidos.",
    }


async def test_bootstrap_creates_the_initial_administrator_only_once(
    user_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    dados = UsuarioCadastro(
        email="admin@example.com",
        nome="Administrador Inicial",
        senha="senha-admin-segura",
    )
    async with user_session_factory() as session:
        primeiro, foi_criado = await AuthService(session).criar_administrador_inicial(dados)
        segundo, foi_criado_novamente = await AuthService(session).criar_administrador_inicial(
            dados
        )

    assert primeiro.role == "admin"
    assert foi_criado
    assert segundo.id == primeiro.id
    assert not foi_criado_novamente
