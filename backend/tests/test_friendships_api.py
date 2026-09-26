from collections.abc import AsyncIterator
from datetime import datetime, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.communities.models import Community
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimMovie, MovieReview
from app.users.dependencies import get_current_user
from app.users.models import User


@pytest.fixture
async def friendship_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        ana = User(id="ana", email="ana@example.com", nome="Ana", password_hash="hash")
        filme = DimMovie(id_filme="movie-profile", titulo="Filme do perfil")
        session.add_all(
            [
                ana,
                User(id="bia", email="bia@example.com", nome="Bia", password_hash="hash"),
                User(id="caio", email="caio@example.com", nome="Caio", password_hash="hash"),
                Community(
                    id="cinema-brasileiro",
                    nome="Cinema brasileiro",
                    descricao="Conversas sobre produções nacionais.",
                    members=[ana],
                ),
                filme,
            ]
        )
        await session.flush()
        session.add_all(
            [
                MovieReview(
                    sk_movie_id=filme.sk_movie_id,
                    user_id="ana",
                    nome="Ana",
                    nota=indice + 4,
                    comentario=f"Comentário {indice}",
                    visibilidade="publica",
                    created_at=datetime(2026, 1, 1) + timedelta(days=indice),
                )
                for indice in range(6)
            ]
        )
        await session.commit()
    try:
        yield session_factory
    finally:
        await engine.dispose()


async def test_friendship_request_can_be_accepted_listed_and_removed(
    friendship_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with friendship_session_factory() as session:
            yield session

    async def ana() -> User:
        return User(id="ana", email="ana@example.com", nome="Ana", password_hash="hash")

    async def bia() -> User:
        return User(id="bia", email="bia@example.com", nome="Bia", password_hash="hash")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = ana
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            people = await client.get("/api/v1/minha-conta/amigos/pesquisa?busca=bi")
            created = await client.post("/api/v1/minha-conta/amigos/solicitacoes/bia")
            duplicate = await client.post("/api/v1/minha-conta/amigos/solicitacoes/bia")
            self_request = await client.post("/api/v1/minha-conta/amigos/solicitacoes/ana")
            app.dependency_overrides[get_current_user] = bia
            requests = await client.get("/api/v1/minha-conta/amigos/solicitacoes")
            accepted = await client.patch(
                f"/api/v1/minha-conta/amigos/solicitacoes/{created.json()['id']}",
                json={"acao": "aceitar"},
            )
            app.dependency_overrides[get_current_user] = ana
            friends = await client.get("/api/v1/minha-conta/amigos")
            profile = await client.get("/api/v1/perfis/ana")
            removed = await client.delete("/api/v1/minha-conta/amigos/bia")
            empty_friends = await client.get("/api/v1/minha-conta/amigos")
            requested_again = await client.post("/api/v1/minha-conta/amigos/solicitacoes/bia")
    finally:
        app.dependency_overrides.clear()

    assert people.status_code == 200
    assert people.json() == [{"id": "bia", "nome": "Bia", "avatar_url": None}]
    assert created.status_code == 201
    assert created.json()["status"] == "pendente"
    assert duplicate.status_code == 409
    assert self_request.status_code == 422
    assert requests.status_code == 200
    assert requests.json()[0]["direcao"] == "recebida"
    assert requests.json()[0]["pessoa"]["nome"] == "Ana"
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "aceita"
    assert friends.json() == [{"id": "bia", "nome": "Bia", "avatar_url": None}]
    assert profile.json()["quantidade_amigos"] == 1
    assert profile.json()["comunidades"] == [
        {
            "id": "cinema-brasileiro",
            "nome": "Cinema brasileiro",
            "descricao": "Conversas sobre produções nacionais.",
        }
    ]
    assert len(profile.json()["avaliacoes"]) == 5
    assert profile.json()["avaliacoes"][0]["comentario"] == "Comentário 5"
    assert profile.json()["avaliacoes"][-1]["comentario"] == "Comentário 1"
    assert removed.status_code == 204
    assert empty_friends.json() == []
    assert requested_again.status_code == 201
    assert requested_again.json()["status"] == "pendente"


async def test_received_request_can_be_blocked(
    friendship_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with friendship_session_factory() as session:
            yield session

    async def bia() -> User:
        return User(id="bia", email="bia@example.com", nome="Bia", password_hash="hash")

    async def caio() -> User:
        return User(id="caio", email="caio@example.com", nome="Caio", password_hash="hash")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = bia
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post("/api/v1/minha-conta/amigos/solicitacoes/caio")
            app.dependency_overrides[get_current_user] = caio
            blocked = await client.patch(
                f"/api/v1/minha-conta/amigos/solicitacoes/{created.json()['id']}",
                json={"acao": "bloquear"},
            )
            app.dependency_overrides[get_current_user] = bia
            requests = await client.get("/api/v1/minha-conta/amigos/solicitacoes")
    finally:
        app.dependency_overrides.clear()

    assert blocked.status_code == 200
    assert blocked.json()["status"] == "bloqueada"
    assert requests.json()[0]["status"] == "bloqueada"
