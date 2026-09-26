from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimGenre, DimMovie, DimPerson, MovieReview
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
