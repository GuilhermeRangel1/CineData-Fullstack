from collections.abc import AsyncIterator
from datetime import datetime

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimGenre, DimMovie, MovieReview
from app.users.dependencies import get_current_user
from app.users.models import User


@pytest.fixture
async def lists_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        drama = DimGenre(nome_genero="Drama")
        session.add_all(
            [
                User(id="user-1", email="ana@example.com", nome="Ana", password_hash="hash"),
                User(id="user-2", email="bia@example.com", nome="Bia", password_hash="hash"),
                DimMovie(id_filme="movie-1", titulo="A Chegada", genres=[drama]),
                DimMovie(id_filme="movie-2", titulo="Zodíaco", genres=[drama]),
            ]
        )
        await session.commit()

    try:
        yield session_factory
    finally:
        await engine.dispose()


async def test_user_can_manage_a_private_custom_list_with_catalog_movies(
    lists_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with lists_session_factory() as session:
            yield session

    async def current_user() -> User:
        return User(id="user-1", email="ana@example.com", nome="Ana", password_hash="hash")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = current_user
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post("/api/v1/minha-conta/listas", json={"nome": "Favoritos"})
            list_id = created.json()["id"]
            added = await client.post(f"/api/v1/minha-conta/listas/{list_id}/filmes/movie-1")
            duplicate = await client.post(f"/api/v1/minha-conta/listas/{list_id}/filmes/movie-1")
            updated = await client.patch(
                f"/api/v1/minha-conta/listas/{list_id}",
                json={"nome": "Drama favorito", "visibilidade": "publica"},
            )
            empty_update = await client.patch(f"/api/v1/minha-conta/listas/{list_id}", json={})
            removed = await client.delete(f"/api/v1/minha-conta/listas/{list_id}/filmes/movie-1")
            details = await client.get(f"/api/v1/minha-conta/listas/{list_id}")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["visibilidade"] == "privada"
    assert created.json()["quantidade_filmes"] == 0
    assert added.status_code == 200
    assert added.json()["filmes"][0]["id"] == "movie-1"
    assert duplicate.status_code == 409
    assert duplicate.json()["codigo"] == "FILME_JA_ESTA_NA_LISTA"
    assert updated.status_code == 200
    assert updated.json()["nome"] == "Drama favorito"
    assert updated.json()["visibilidade"] == "publica"
    assert empty_update.status_code == 422
    assert removed.status_code == 204
    assert details.status_code == 200
    assert details.json()["filmes"] == []


async def test_lists_cannot_be_read_or_changed_by_another_account(
    lists_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with lists_session_factory() as session:
            yield session

    async def ana() -> User:
        return User(id="user-1", email="ana@example.com", nome="Ana", password_hash="hash")

    async def bia() -> User:
        return User(id="user-2", email="bia@example.com", nome="Bia", password_hash="hash")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = ana
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post("/api/v1/minha-conta/listas", json={"nome": "Pessoal"})
            app.dependency_overrides[get_current_user] = bia
            other_account = await client.get(f"/api/v1/minha-conta/listas/{created.json()['id']}")
    finally:
        app.dependency_overrides.clear()

    assert other_account.status_code == 404
    assert other_account.json()["codigo"] == "LISTA_NAO_ENCONTRADA"


async def test_virtual_reviewed_and_watch_later_lists_are_unique_and_personal(
    lists_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with lists_session_factory() as session:
        movie = await session.scalar(select(DimMovie).where(DimMovie.id_filme == "movie-1"))
        assert movie is not None
        session.add_all(
            [
                MovieReview(
                    sk_movie_id=movie.sk_movie_id,
                    user_id="user-1",
                    nome="Ana",
                    nota=8,
                    comentario="Primeira avaliação.",
                    created_at=datetime(2025, 1, 1),
                ),
                MovieReview(
                    sk_movie_id=movie.sk_movie_id,
                    user_id="user-1",
                    nome="Ana",
                    nota=9,
                    comentario="Avaliação mais nova.",
                    created_at=datetime(2025, 2, 1),
                ),
            ]
        )
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with lists_session_factory() as session:
            yield session

    async def current_user() -> User:
        return User(id="user-1", email="ana@example.com", nome="Ana", password_hash="hash")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = current_user
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            reviewed = await client.get("/api/v1/minha-conta/filmes-avaliados")
            added = await client.put("/api/v1/minha-conta/assistir-depois/movie-2")
            watch_later = await client.get("/api/v1/minha-conta/assistir-depois")
            duplicate = await client.put("/api/v1/minha-conta/assistir-depois/movie-2")
    finally:
        app.dependency_overrides.clear()

    assert reviewed.status_code == 200
    assert [movie["id"] for movie in reviewed.json()] == ["movie-1"]
    assert added.status_code == 204
    assert [movie["id"] for movie in watch_later.json()] == ["movie-2"]
    assert duplicate.status_code == 409
