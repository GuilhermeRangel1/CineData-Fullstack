from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import (
    DimCompany,
    DimGenre,
    DimMovie,
    DimPerson,
    DimReview,
    FactMoviePerformance,
    MovieReview,
)


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
        diretora = DimPerson(nome_pessoa="Denis Villeneuve", tipo_pessoa="Diretor")
        atriz = DimPerson(nome_pessoa="Amy Adams", tipo_pessoa="Ator")
        produtora = DimCompany(nome_produtora="Paramount Pictures")
        chegada = DimMovie(
            id_filme="movie-1",
            titulo="A Chegada",
            ano_lancamento=2016,
            genres=[ficcao, drama],
            people=[diretora, atriz],
            companies=[produtora],
            performance=FactMoviePerformance(
                orcamento_usd=Decimal("47000000"),
                receita_usd=Decimal("203388186"),
                lucro_usd=Decimal("156388186"),
                orcamento_brl=Decimal("147921000"),
                receita_brl=Decimal("640673785"),
                lucro_brl=Decimal("492752785"),
                popularidade=31.5,
                nota_tmdb=7.6,
                qtd_tmdb=17200,
                nota_imdb=7.9,
                qtd_imdb=780000,
            ),
            reviews_summary=DimReview(qtd_avaliacoes_usuarios=1, nota_media_usuarios=8.5),
            reviews=[
                MovieReview(
                    nome="Maria",
                    nota=8.5,
                    comentario="Ficção científica envolvente.",
                    # Distinguish history from new writes even within the same SQLite second.
                    created_at=datetime(2020, 1, 1),
                )
            ],
        )
        session.add_all(
            [
                DimMovie(id_filme="movie-2", titulo="Zodíaco", ano_lancamento=2007, genres=[drama]),
                chegada,
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
    assert payload["itens"][0]["nota_media"] == 8.5
    assert payload["itens"][0]["quantidade_avaliacoes"] == 1
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


async def test_catalog_endpoint_combines_case_insensitive_search_and_pagination(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with catalog_session_factory() as session:
        session.add(DimMovie(id_filme="movie-3", titulo="Chegada Final", ano_lancamento=2024))
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/filmes",
                params={"busca": "CHEGADA", "pagina": 2, "tamanho_pagina": 1},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "itens": [
            {
                "id": "movie-3",
                "titulo": "Chegada Final",
                "ano_lancamento": 2024,
                "url_poster": None,
                "url_backdrop": None,
                "generos": [],
                "nota_media": None,
                "quantidade_avaliacoes": 0,
            }
        ],
        "meta": {
            "pagina": 2,
            "tamanho_pagina": 1,
            "total_itens": 2,
            "total_paginas": 2,
        },
    }


async def test_catalog_endpoint_prioritizes_records_with_a_cover(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with catalog_session_factory() as session:
        session.add(
            DimMovie(
                id_filme="movie-cover",
                titulo="Zeta com imagem",
                ano_lancamento=2024,
                url_backdrop="https://example.com/backdrop.jpg",
            )
        )
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/filmes", params={"priorizar_capa": "true"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["itens"][0]["id"] == "movie-cover"


async def test_movie_detail_endpoint_returns_full_loaded_data(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/filmes/movie-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "movie-1"
    assert payload["nota_media"] == 8.5
    assert payload["quantidade_avaliacoes"] == 1
    assert [genero["nome"] for genero in payload["generos"]] == ["Drama", "Ficção científica"]
    assert {(pessoa["nome"], pessoa["papel"]) for pessoa in payload["pessoas"]} == {
        ("Denis Villeneuve", "Diretor"),
        ("Amy Adams", "Ator"),
    }
    assert payload["produtoras"][0]["nome"] == "Paramount Pictures"
    assert payload["desempenho"] == {
        "orcamento_usd": 47000000.0,
        "receita_usd": 203388186.0,
        "lucro_usd": 156388186.0,
        "orcamento_brl": 147921000.0,
        "receita_brl": 640673785.0,
        "lucro_brl": 492752785.0,
        "popularidade": 31.5,
        "nota_tmdb": 7.6,
        "quantidade_tmdb": 17200,
        "nota_imdb": 7.9,
        "quantidade_imdb": 780000,
    }
    assert payload["avaliacoes"][0]["nome"] == "Maria"
    assert payload["avaliacoes"][0]["nota"] == 8.5
    assert payload["avaliacoes"][0]["criada_em"]


async def test_movie_detail_endpoint_returns_not_found_for_unknown_movie(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/filmes/inexistente")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "codigo": "FILME_NAO_ENCONTRADO",
        "mensagem": "Filme não encontrado.",
    }


async def test_reviews_endpoints_create_history_and_keep_average_consistent(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            creation_response = await client.post(
                "/api/v1/filmes/movie-1/avaliacoes",
                json={
                    "nome": "Ana",
                    "nota": 10,
                    "comentario": "Uma avaliação excelente.",
                },
            )
            history_response = await client.get("/api/v1/filmes/movie-1/avaliacoes")
            detail_response = await client.get("/api/v1/filmes/movie-1")
            catalog_response = await client.get("/api/v1/filmes")
    finally:
        app.dependency_overrides.clear()

    assert creation_response.status_code == 201
    created = creation_response.json()
    assert created["id"]
    assert created["nota"] == 10
    assert created["criada_em"]
    assert history_response.status_code == 200
    assert [item["nome"] for item in history_response.json()] == ["Ana", "Maria"]
    assert detail_response.json()["quantidade_avaliacoes"] == 2
    assert detail_response.json()["nota_media"] == 9.25
    movie_in_catalog = next(
        item for item in catalog_response.json()["itens"] if item["id"] == "movie-1"
    )
    assert movie_in_catalog["quantidade_avaliacoes"] == 2
    assert movie_in_catalog["nota_media"] == 9.25


async def test_review_endpoints_validate_payload_and_return_not_found(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            invalid_score = await client.post(
                "/api/v1/filmes/movie-1/avaliacoes",
                json={"nome": "Ana", "nota": 10.1, "comentario": "Inválida."},
            )
            invalid_text = await client.post(
                "/api/v1/filmes/movie-1/avaliacoes",
                json={"nome": " ", "nota": 0, "comentario": " "},
            )
            missing_movie = await client.get("/api/v1/filmes/inexistente/avaliacoes")
    finally:
        app.dependency_overrides.clear()

    assert invalid_score.status_code == 422
    assert invalid_text.status_code == 422
    assert invalid_score.json() == {
        "codigo": "REQUISICAO_INVALIDA",
        "mensagem": "Dados da requisição são inválidos.",
    }
    assert missing_movie.status_code == 404
    assert missing_movie.json() == {
        "codigo": "FILME_NAO_ENCONTRADO",
        "mensagem": "Filme não encontrado.",
    }


async def test_update_movie_endpoint_changes_only_sent_fields_and_relationships(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/filmes/movie-1",
                json={
                    "titulo": "A Chegada Atualizada",
                    "diretor": "Nova Diretora",
                    "generos": ["Drama"],
                    "atores": ["Novo Ator"],
                    "sinopse": None,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["titulo"] == "A Chegada Atualizada"
    assert payload["sinopse"] is None
    assert [genero["nome"] for genero in payload["generos"]] == ["Drama"]
    assert {(pessoa["nome"], pessoa["papel"]) for pessoa in payload["pessoas"]} == {
        ("Nova Diretora", "Diretor"),
        ("Novo Ator", "Ator"),
    }
    assert payload["produtoras"][0]["nome"] == "Paramount Pictures"
    assert payload["desempenho"]["nota_tmdb"] == 7.6


async def test_update_movie_endpoint_returns_not_found_for_unknown_movie(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch("/api/v1/filmes/inexistente", json={"titulo": "Novo"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


async def test_delete_movie_endpoint_removes_dependents_and_returns_no_content(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/v1/filmes/movie-1")
            detail_response = await client.get("/api/v1/filmes/movie-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
    assert detail_response.status_code == 404
    async with catalog_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(DimMovie)) == 1
        assert await session.scalar(select(func.count()).select_from(DimReview)) == 0
        assert await session.scalar(select(func.count()).select_from(FactMoviePerformance)) == 0
        assert await session.scalar(select(func.count()).select_from(MovieReview)) == 0


async def test_delete_movie_endpoint_returns_not_found_for_unknown_movie(
    catalog_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/v1/filmes/inexistente")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


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
        assert await session.scalar(select(func.count()).select_from(DimPerson)) == 5
        assert await session.scalar(select(func.count()).select_from(DimCompany)) == 2


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


async def test_create_movie_endpoint_rolls_back_and_hides_persistence_failure(
    catalog_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_commit(self: AsyncSession) -> None:
        del self
        raise SQLAlchemyError("falha simulada")

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with catalog_session_factory() as session:
            yield session

    monkeypatch.setattr(AsyncSession, "commit", failing_commit)
    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/filmes",
                json={
                    "titulo": "Filme que falha",
                    "diretor": "Diretora",
                    "ano_lancamento": 2024,
                    "generos": ["Drama"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "codigo": "FALHA_DE_PERSISTENCIA",
        "mensagem": "Não foi possível concluir a operação no momento.",
    }
    async with catalog_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(DimMovie)) == 2
