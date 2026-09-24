from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimCompany, DimGenre, DimMovie, DimPerson


@pytest.fixture
async def catalog_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
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
        ficcao = DimGenre(nome_genero="Ficção científica")
        session.add_all(
            [
                DimMovie(id_filme="movie-2", titulo="Zodíaco", ano_lancamento=2007, genres=[drama]),
                DimMovie(
                    id_filme="movie-1",
                    titulo="A Chegada",
                    ano_lancamento=2016,
                    genres=[ficcao, drama],
                ),
            ]
        )
        await session.commit()

    try:
        yield session_factory
    finally:
        await engine.dispose()


async def test_catalog_endpoint_uses_service_with_stable_pagination(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/filmes",
                params={"genero": "drama", "tamanho_pagina": 1},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"] == {
        "pagina": 1,
        "tamanho_pagina": 1,
        "total_itens": 2,
        "total_paginas": 2,
    }
    assert len(payload["itens"]) == 1
    assert payload["itens"][0]["id"] == "movie-1"
    assert payload["itens"][0]["nota_media"] is None
    assert payload["itens"][0]["quantidade_avaliacoes"] == 0
    assert [genero["nome"] for genero in payload["itens"][0]["generos"]] == [
        "Drama",
        "Ficção científica",
    ]


async def test_catalog_endpoint_returns_public_error_for_invalid_pagination(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/filmes", params={"pagina": 0})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {
        "codigo": "REQUISICAO_INVALIDA",
        "mensagem": "Dados da requisição são inválidos.",
    }


async def test_create_movie_endpoint_persists_required_relationships(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/filmes",
                json={
                    "titulo": "O Filme Criado",
                    "diretor": "Ana Diretora",
                    "ano_lancamento": 2025,
                    "generos": ["Drama", "Mistério"],
                    "sinopse": "Um filme cadastrado pela API.",
                    "atores": ["Bruno Ator"],
                    "roteiristas": ["Carla Roteirista"],
                    "produtoras": ["Estúdio Local"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"].startswith("local-")
    assert payload["titulo"] == "O Filme Criado"
    assert {genero["nome"] for genero in payload["generos"]} == {"Drama", "Mistério"}
    assert {(pessoa["nome"], pessoa["papel"]) for pessoa in payload["pessoas"]} == {
        ("Ana Diretora", "Diretor"),
        ("Bruno Ator", "Ator"),
        ("Carla Roteirista", "Roteirista"),
    }
    assert payload["produtoras"] == [
        {"id": payload["produtoras"][0]["id"], "nome": "Estúdio Local"}
    ]

    async with catalog_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(DimMovie)) == 3
        assert await session.scalar(select(func.count()).select_from(DimGenre)) == 3
        assert await session.scalar(select(func.count()).select_from(DimPerson)) == 3
        assert await session.scalar(select(func.count()).select_from(DimCompany)) == 1


async def test_create_movie_endpoint_rejects_incomplete_payload(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/filmes",
                json={
                    "titulo": "Sem diretor",
                    "generos": ["Drama"],
                    "sinopse": "Este cadastro deve falhar.",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {
        "codigo": "REQUISICAO_INVALIDA",
        "mensagem": "Dados da requisição são inválidos.",
    }
