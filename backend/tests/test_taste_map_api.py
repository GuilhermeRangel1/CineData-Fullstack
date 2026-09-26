from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.errors import PermissaoNegadaError
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimGenre, DimMovie, DimPerson, FactMoviePerformance, MovieReview
from app.taste_map.services import MapaGostosService, PesosSimilaridade
from app.users.dependencies import get_current_user
from app.users.models import User


@pytest.fixture
async def taste_map_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        user = User(id="user-map", email="mapa@example.com", nome="Mapa", password_hash="hash")
        ficcao = DimGenre(nome_genero="Ficção científica")
        drama = DimGenre(nome_genero="Drama")
        diretora = DimPerson(nome_pessoa="Ana Diretora", tipo_pessoa="Diretor")
        favorita = DimMovie(
            id_filme="favorita",
            titulo="Minha ficção favorita",
            ano_lancamento=2018,
            genres=[ficcao],
            people=[diretora],
            reviews=[
                MovieReview(
                    user_id="user-map", nome="Mapa", nota=9.5, comentario="Adorei."
                )
            ],
        )
        proxima = DimMovie(
            id_filme="proxima",
            titulo="Outra viagem espacial",
            ano_lancamento=2020,
            genres=[ficcao],
            people=[diretora],
        )
        distante = DimMovie(
            id_filme="distante",
            titulo="Drama distante",
            ano_lancamento=1970,
            genres=[drama],
        )
        session.add_all([user, favorita, proxima, distante])
        await session.commit()
    try:
        yield session_factory
    finally:
        await engine.dispose()


async def test_taste_map_connects_rated_movies_to_explainable_recommendations(
    taste_map_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def database_override() -> AsyncIterator[AsyncSession]:
        async with taste_map_session_factory() as session:
            yield session

    async def current_user() -> User:
        return User(id="user-map", email="mapa@example.com", nome="Mapa", password_hash="hash")

    transport = httpx.ASGITransport(app=app)
    try:
        app.dependency_overrides[get_db] = database_override
        app.dependency_overrides[get_current_user] = current_user
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/mapa-de-gostos",
                params={"limite_nos": 12, "vizinhos_por_filme": 2},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total_avaliados"] == 1
    nos = {no["id"]: no for no in payload["nos"]}
    assert nos["favorita"]["tipo"] == "avaliado"
    assert nos["favorita"]["nota_usuario"] == 9.5
    assert nos["proxima"]["tipo"] == "recomendado"
    assert nos["proxima"]["afinidade"] > 0
    assert payload["arestas"] == [
        {
            "origem": "favorita",
            "destino": "proxima",
            "peso": payload["arestas"][0]["peso"],
            "explicacao": "Conexão por gênero Ficção científica e direção de Ana Diretora",
        }
    ]


async def test_taste_map_requires_an_authenticated_user() -> None:
    async def denied() -> User:
        raise PermissaoNegadaError

    transport = httpx.ASGITransport(app=app)
    try:
        app.dependency_overrides[get_current_user] = denied
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/mapa-de-gostos")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


async def test_refresh_excludes_previous_suggestions_and_keeps_rated_nodes(
    taste_map_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def database_override() -> AsyncIterator[AsyncSession]:
        async with taste_map_session_factory() as session:
            yield session

    async def current_user() -> User:
        return User(id="user-map", email="mapa@example.com", nome="Mapa", password_hash="hash")

    async with taste_map_session_factory() as session:
        genre = DimGenre(nome_genero="Aventura")
        # Reutiliza a direção existente para adicionar uma alternativa menos próxima.
        director = await session.scalar(
            select(DimPerson).where(DimPerson.nome_pessoa == "Ana Diretora")
        )
        session.add(DimMovie(id_filme="alternativa", titulo="Nova aventura",
                             genres=[genre], people=[director]))
        await session.commit()

    try:
        app.dependency_overrides[get_db] = database_override
        app.dependency_overrides[get_current_user] = current_user
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = (await client.get("/api/v1/mapa-de-gostos?vizinhos_por_filme=1")).json()
            assert {no["id"] for no in first["nos"]} == {"favorita", "proxima"}
            refreshed = await client.get(
                "/api/v1/mapa-de-gostos",
                params=[("excluir", "proxima"), ("vizinhos_por_filme", "1")],
            )
            assert refreshed.status_code == 200
            assert {no["id"] for no in refreshed.json()["nos"]} == {"favorita", "alternativa"}
            empty = await client.get(
                "/api/v1/mapa-de-gostos",
                params=[("excluir", "proxima"), ("excluir", "alternativa")],
            )
            assert [no["id"] for no in empty.json()["nos"]] == ["favorita"]
            assert empty.json()["arestas"] == []
    finally:
        app.dependency_overrides.clear()


def test_taste_map_similarity_uses_synopsis_metrics_and_configurable_weights() -> None:
    origem = DimMovie(
        id_filme="origem",
        titulo="Sinal no espaço",
        sinopse="Astronauta investiga sinal extraterrestre durante viagem espacial.",
        performance=FactMoviePerformance(nota_tmdb=8.2, nota_imdb=8.0, popularidade=44),
    )
    proximo = DimMovie(
        id_filme="proximo",
        titulo="Outro sinal",
        sinopse="Astronauta rastreia sinal extraterrestre em viagem espacial.",
        performance=FactMoviePerformance(nota_tmdb=8.1, nota_imdb=8.1, popularidade=42),
    )
    distante = DimMovie(
        id_filme="distante",
        titulo="Mesmo tema, outra recepção",
        sinopse="Astronauta rastreia sinal extraterrestre em viagem espacial.",
        performance=FactMoviePerformance(nota_tmdb=2.0, nota_imdb=2.0, popularidade=1),
    )
    diferente = DimMovie(
        id_filme="diferente",
        titulo="Sem ligação",
        sinopse="Uma família encontra uma casa antiga no interior.",
    )

    service = MapaGostosService(None)
    assert service._afinidade(origem, proximo, 9) > service._afinidade(origem, distante, 9)
    assert service._afinidade(origem, proximo, 9) > 0.12
    assert service._afinidade(origem, diferente, 9) == 0

    somente_sinopse = MapaGostosService(
        None,
        PesosSimilaridade(generos=0, direcao=0, elenco=0, sinopse=1, ano=0, metricas=0),
    )
    assert somente_sinopse._afinidade(origem, proximo, 9) > 0
