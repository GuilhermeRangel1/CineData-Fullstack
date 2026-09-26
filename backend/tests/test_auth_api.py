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
from app.movies.models import MovieReview
from app.users.models import User
from app.users.schemas import UsuarioCadastro, UsuarioCadastroInicial
from app.users.security import gerar_hash_senha
from app.users.services import AuthService
from app.users.tokens import criar_token_acesso


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
                    "senha": "senha-local-segura1",
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
        "avatar_url": None,
    }

    async with user_session_factory() as session:
        usuario = await session.scalar(select(User).where(User.email == "ana@example.com"))
    assert usuario is not None
    assert usuario.role == "user"
    assert usuario.password_hash != "senha-local-segura1"


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
                    "senha": "senha-local-segura1",
                    "role": "admin",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("senha", "mensagem"),
    [
        ("abc1234", "A senha precisa ter pelo menos 8 caracteres."),
        ("somenteletras", "Use uma senha com pelo menos uma letra e um número."),
    ],
)
async def test_registration_explains_how_to_choose_a_valid_password(
    user_session_factory: async_sessionmaker[AsyncSession], senha: str, mensagem: str
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
                json={"email": "ana@example.com", "nome": "Ana", "senha": senha},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {"codigo": "REQUISICAO_INVALIDA", "mensagem": mensagem}


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
                    "senha": "senha-local-segura1",
                },
            )
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "ana@example.com", "senha": "senha-local-segura1"},
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
                senha="senha-local-segura1",
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
        "mensagem": "E-mail ou senha inválidos. Confira os dados e tente novamente.",
    }


async def test_user_can_update_avatar_and_expose_a_safe_public_profile(
    user_session_factory: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "segredo-de-teste-com-tamanho-suficiente")
    get_settings.cache_clear()
    async with user_session_factory() as session:
        usuario = User(
            id="user-profile",
            email="perfil@example.com",
            nome="Perfil",
            password_hash=gerar_hash_senha("senha-local-segura1"),
        )
        session.add(usuario)
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with user_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/auth/perfil",
                headers={"Authorization": f"Bearer {criar_token_acesso(usuario).access_token}"},
                json={
                    "nome": "Perfil Atualizado",
                    "avatar_url": "data:image/png;base64,aGVsbG8=",
                },
            )
            public_profile = await client.get("/api/v1/perfis/user-profile")
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["nome"] == "Perfil Atualizado"
    assert response.json()["avatar_url"] == "data:image/png;base64,aGVsbG8="
    assert public_profile.status_code == 200
    assert public_profile.json()["quantidade_amigos"] == 0
    assert public_profile.json()["avatar_url"] == "data:image/png;base64,aGVsbG8="
    assert "email" not in public_profile.json()


async def test_bootstrap_creates_the_initial_administrator_only_once(
    user_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    dados = UsuarioCadastroInicial(
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


async def test_catalog_is_public_but_writes_require_the_expected_account_role(
    user_session_factory: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "segredo-de-teste-com-tamanho-suficiente")
    get_settings.cache_clear()
    async with user_session_factory() as session:
        usuario = User(
            id="user-1",
            email="ana@example.com",
            nome="Ana",
            password_hash=gerar_hash_senha("senha-local-segura1"),
        )
        admin = User(
            id="admin-1",
            email="admin@example.com",
            nome="Admin",
            password_hash=gerar_hash_senha("senha-admin-segura1"),
            role="admin",
        )
        session.add_all([usuario, admin])
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with user_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            public_catalog = await client.get("/api/v1/filmes")
            no_session = await client.post(
                "/api/v1/filmes",
                json={"titulo": "Novo", "diretor": "Diretora", "generos": ["Drama"]},
            )
            regular_user = await client.post(
                "/api/v1/filmes",
                headers={"Authorization": f"Bearer {criar_token_acesso(usuario).access_token}"},
                json={"titulo": "Novo", "diretor": "Diretora", "generos": ["Drama"]},
            )
            administrator = await client.post(
                "/api/v1/filmes",
                headers={"Authorization": f"Bearer {criar_token_acesso(admin).access_token}"},
                json={"titulo": "Novo", "diretor": "Diretora", "generos": ["Drama"]},
            )
            review = await client.post(
                f"/api/v1/filmes/{administrator.json()['id']}/avaliacoes",
                headers={"Authorization": f"Bearer {criar_token_acesso(usuario).access_token}"},
                json={"nota": 9, "comentario": "Ótimo filme."},
            )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert public_catalog.status_code == 200
    assert no_session.status_code == 401
    assert no_session.headers["www-authenticate"] == "Bearer"
    assert regular_user.status_code == 403
    assert administrator.status_code == 201
    assert review.status_code == 201
    assert review.json()["nome"] == "Ana"

    async with user_session_factory() as session:
        saved_review = await session.scalar(select(MovieReview).where(MovieReview.nome == "Ana"))
    assert saved_review is not None
    assert saved_review.user_id == "user-1"
