from collections.abc import AsyncIterator
from datetime import datetime

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.communities.models import Community, CommunityPost
from app.core.errors import PermissaoNegadaError
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimGenre, DimMovie, DimReview, MovieReview
from app.users.dependencies import get_current_admin
from app.users.models import User, UserList


@pytest.fixture
async def analytics_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        admin = User(
            id="admin",
            email="admin@example.com",
            nome="Admin",
            password_hash="hash",
            role="admin",
        )
        member = User(id="member", email="member@example.com", nome="Membro", password_hash="hash")
        genre = DimGenre(nome_genero="Drama")
        movie = DimMovie(
            id_filme="movie-1",
            titulo="Filme com avaliações",
            genres=[genre],
            reviews_summary=DimReview(qtd_avaliacoes_usuarios=2, nota_media_usuarios=8.5),
            reviews=[
                MovieReview(
                    user_id="member",
                    nome="Membro",
                    nota=8.5,
                    comentario="Muito bom.",
                    created_at=datetime.now(),
                )
            ],
        )
        community = Community(
            nome="Clube do drama",
            descricao="Conversas sobre drama.",
            members=[member],
        )
        session.add_all(
            [
                admin,
                member,
                movie,
                DimMovie(id_filme="movie-2", titulo="Outro filme", genres=[genre]),
                UserList(id="list-1", user_id="member", nome="Favoritos"),
                community,
            ]
        )
        await session.flush()
        session.add(
            CommunityPost(
                community_id=community.id,
                author_id="member",
                conteudo="Uma publicação recente.",
                created_at=datetime.now(),
            )
        )
        await session.commit()

    try:
        yield session_factory
    finally:
        await engine.dispose()


async def test_analytics_summary_is_admin_only_and_aggregates_platform_data(
    analytics_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def database_override() -> AsyncIterator[AsyncSession]:
        async with analytics_session_factory() as session:
            yield session

    async def admin() -> User:
        return User(
            id="admin",
            email="admin@example.com",
            nome="Admin",
            password_hash="hash",
            role="admin",
        )

    async def denied() -> User:
        raise PermissaoNegadaError

    transport = httpx.ASGITransport(app=app)
    try:
        app.dependency_overrides[get_db] = database_override
        app.dependency_overrides[get_current_admin] = denied
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            forbidden = await client.get("/api/v1/admin/analytics/resumo")
            assert forbidden.status_code == 403

            app.dependency_overrides[get_current_admin] = admin
            response = await client.get(
                "/api/v1/admin/analytics/resumo", params={"periodo_dias": 7}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["periodo_dias"] == 7
    assert {metric["chave"]: metric["valor"] for metric in payload["metricas"]} == {
        "filmes": 2,
        "usuarios": 2,
        "avaliacoes": 1,
        "listas": 1,
        "comunidades": 1,
    }
    assert payload["generos"] == [{"nome": "Drama", "quantidade": 1, "nota_media": 8.5}]
    assert payload["filmes_mais_avaliados"][0]["titulo"] == "Filme com avaliações"
    assert payload["comunidades_em_alta"][0]["publicacoes"] == 1
    assert len(payload["evolucao"]) == 7
