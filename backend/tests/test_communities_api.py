from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.communities.models import Community, CommunityComment, CommunityPost, CommunityReaction
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimGenre, DimMovie
from app.users.dependencies import get_current_admin, get_current_user
from app.users.models import User


@pytest.fixture
async def communities_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        genre = DimGenre(nome_genero="Fantasia")
        session.add_all(
            [
                User(
                    id="admin",
                    email="admin@example.com",
                    nome="Admin",
                    password_hash="hash",
                    role="admin",
                ),
                User(id="ana", email="ana@example.com", nome="Ana", password_hash="hash"),
                User(id="bia", email="bia@example.com", nome="Bia", password_hash="hash"),
                DimMovie(id_filme="movie-1", titulo="O Castelo Animado", genres=[genre]),
            ]
        )
        await session.commit()
    try:
        yield session_factory
    finally:
        await engine.dispose()


async def test_views_are_persisted_and_sort_discovery_without_counting_reads(
    communities_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with communities_session_factory() as session:
        session.add_all([
            Community(id="a", nome="Animação", descricao="Animações"),
            Community(id="z", nome="Suspense", descricao="Mistérios"),
        ])
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with communities_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            initial = (await client.get("/api/v1/comunidades")).json()
            assert [item["id"] for item in initial] == ["a", "z"]
            assert all(item["visualizacoes"] == 0 for item in initial)
            for count in (1, 2):
                seen = await client.post("/api/v1/comunidades/z/visualizacoes")
                assert seen.status_code == 200
                assert seen.json()["visualizacoes"] == count
            await client.get("/api/v1/comunidades/z/publicacoes")
            await client.get("/api/v1/comunidades/z")
            listed = (await client.get("/api/v1/comunidades")).json()
            assert [item["id"] for item in listed] == ["z", "a"]
            assert listed[0]["visualizacoes"] == 2
            missing = await client.post("/api/v1/comunidades/missing/visualizacoes")
            assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()


async def test_admin_manages_communities_and_people_can_participate(
    communities_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with communities_session_factory() as session:
            yield session

    async def admin() -> User:
        return User(
            id="admin", email="admin@example.com", nome="Admin", password_hash="hash", role="admin"
        )

    async def ana() -> User:
        return User(id="ana", email="ana@example.com", nome="Ana", password_hash="hash")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_admin] = admin
    app.dependency_overrides[get_current_user] = ana
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/comunidades",
                json={
                    "nome": "Fãs de fantasia",
                    "descricao": "Conversas sobre mundos imaginários.",
                    "imagem_url": "data:image/png;base64,aGVsbG8=",
                },
            )
            community_id = created.json()["id"]
            listed = await client.get("/api/v1/comunidades")
            joined = await client.post(f"/api/v1/comunidades/{community_id}/participacao")
            duplicate_join = await client.post(f"/api/v1/comunidades/{community_id}/participacao")
            members = await client.get(f"/api/v1/comunidades/{community_id}/membros")
            updated = await client.patch(
                f"/api/v1/comunidades/{community_id}",
                json={"descricao": "Fantasia no cinema.", "imagem_url": None},
            )
            left = await client.delete(f"/api/v1/comunidades/{community_id}/participacao")
            deleted = await client.delete(f"/api/v1/comunidades/{community_id}")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["imagem_url"] == "data:image/png;base64,aGVsbG8="
    assert listed.json()[0]["quantidade_membros"] == 0
    assert joined.status_code == 204
    assert duplicate_join.status_code == 409
    assert members.json() == [{"id": "ana", "nome": "Ana", "avatar_url": None}]
    assert updated.json()["descricao"] == "Fantasia no cinema."
    assert updated.json()["imagem_url"] is None
    assert left.status_code == 204
    assert deleted.status_code == 204


async def test_only_admin_can_create_a_community(
    communities_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with communities_session_factory() as session:
            yield session

    async def denied_admin() -> User:
        from app.core.errors import PermissaoNegadaError

        raise PermissaoNegadaError

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_admin] = denied_admin
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/comunidades", json={"nome": "Livre", "descricao": "Não deve criar."}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["codigo"] == "PERMISSAO_NEGADA"


async def test_members_can_post_comment_and_react_to_a_mentioned_movie(
    communities_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with communities_session_factory() as session:
            yield session

    async def admin() -> User:
        return User(
            id="admin", email="admin@example.com", nome="Admin", password_hash="hash", role="admin"
        )

    async def ana() -> User:
        return User(id="ana", email="ana@example.com", nome="Ana", password_hash="hash")

    async def bia() -> User:
        return User(id="bia", email="bia@example.com", nome="Bia", password_hash="hash")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_admin] = admin
    app.dependency_overrides[get_current_user] = ana
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            community = await client.post(
                "/api/v1/comunidades",
                json={"nome": "Animação", "descricao": "Cinema animado."},
            )
            community_id = community.json()["id"]
            blocked_post = await client.post(
                f"/api/v1/comunidades/{community_id}/publicacoes",
                json={"conteudo": "Quero conversar sobre este filme."},
            )
            await client.post(f"/api/v1/comunidades/{community_id}/participacao")
            post = await client.post(
                f"/api/v1/comunidades/{community_id}/publicacoes",
                json={"conteudo": "Quero conversar sobre este filme.", "movie_id": "movie-1"},
            )
            post_id = post.json()["id"]
            app.dependency_overrides[get_current_user] = bia
            blocked_comment = await client.post(
                f"/api/v1/comunidades/publicacoes/{post_id}/comentarios",
                json={"conteudo": "Ainda não entrei."},
            )
            await client.post(f"/api/v1/comunidades/{community_id}/participacao")
            comment = await client.post(
                f"/api/v1/comunidades/publicacoes/{post_id}/comentarios",
                json={"conteudo": "Adoro a direção de arte."},
            )
            reaction = await client.post(
                f"/api/v1/comunidades/publicacoes/{post_id}/reacoes", json={"tipo": "amei"}
            )
            posts = await client.get(f"/api/v1/comunidades/{community_id}/publicacoes")
            removed_reaction = await client.delete(
                f"/api/v1/comunidades/publicacoes/{post_id}/reacoes"
            )
    finally:
        app.dependency_overrides.clear()

    assert blocked_post.status_code == 403
    assert blocked_post.json()["codigo"] == "PARTICIPACAO_NECESSARIA"
    assert post.status_code == 201
    assert post.json()["filme"]["titulo"] == "O Castelo Animado"
    assert blocked_comment.status_code == 403
    assert comment.status_code == 201
    assert comment.json()["autor"]["nome"] == "Bia"
    assert reaction.json() == [{"tipo": "amei", "quantidade": 1}]
    assert posts.json()[0]["comentarios"][0]["conteudo"] == "Adoro a direção de arte."
    assert posts.json()[0]["reacoes"] == [{"tipo": "amei", "quantidade": 1}]
    assert removed_reaction.status_code == 204


async def test_admin_moderation_redacts_post_and_preserves_conversation(
    communities_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with communities_session_factory() as session:
        session.add_all(
            [
                Community(id="c1", nome="Animação", descricao="Conversas."),
                CommunityPost(
                    id="p1",
                    community_id="c1",
                    author_id="ana",
                    sk_movie_id="movie-1",
                    conteudo="Mensagem imprópria",
                    comments=[
                        CommunityComment(
                            id="comment-1", author_id="bia", conteudo="Resposta imprópria"
                        )
                    ],
                    reactions=[CommunityReaction(user_id="bia", tipo="amei")],
                ),
            ]
        )
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with communities_session_factory() as session:
            yield session

    async def admin() -> User:
        return User(
            id="admin", email="admin@example.com", nome="Admin", password_hash="hash", role="admin"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_admin] = admin
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            removed = await client.delete("/api/v1/comunidades/publicacoes/p1")
            posts = await client.get("/api/v1/comunidades/c1/publicacoes")
    finally:
        app.dependency_overrides.clear()

    assert removed.status_code == 204
    assert posts.status_code == 200
    assert posts.json() == [
        {
            "id": "p1",
            "comunidade_id": "c1",
            "conteudo": "",
            "removida_por_moderacao": True,
            "autor": {"id": "ana", "nome": "Ana", "avatar_url": None},
            "filme": None,
            "comentarios": [
                {
                    "id": "comment-1",
                    "conteudo": "",
                    "removida_por_moderacao": True,
                    "autor": {"id": "bia", "nome": "Bia", "avatar_url": None},
                    "criado_em": posts.json()[0]["comentarios"][0]["criado_em"],
                }
            ],
            "reacoes": [],
            "criada_em": posts.json()[0]["criada_em"],
        }
    ]
    async with communities_session_factory() as session:
        post = await session.get(CommunityPost, "p1")
        comment = await session.get(CommunityComment, "comment-1")
        assert post is not None and post.conteudo == ""
        assert comment is not None and comment.conteudo == ""


async def test_only_admin_can_moderate_comment_and_removed_post_cannot_be_replied_to(
    communities_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with communities_session_factory() as session:
        session.add_all(
            [
                Community(id="c1", nome="Animação", descricao="Conversas."),
                CommunityPost(
                    id="p1", community_id="c1", author_id="ana", conteudo="Publicação"
                ),
                CommunityComment(
                    id="comment-1", post_id="p1", author_id="bia", conteudo="Comentário"
                ),
            ]
        )
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with communities_session_factory() as session:
            yield session

    async def ana() -> User:
        return User(id="ana", email="ana@example.com", nome="Ana", password_hash="hash")

    async def denied_admin() -> User:
        from app.core.errors import PermissaoNegadaError

        raise PermissaoNegadaError

    async def admin() -> User:
        return User(
            id="admin", email="admin@example.com", nome="Admin", password_hash="hash", role="admin"
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = ana
    app.dependency_overrides[get_current_admin] = denied_admin
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            denied = await client.delete("/api/v1/comunidades/comentarios/comment-1")
            app.dependency_overrides[get_current_admin] = admin
            removed = await client.delete("/api/v1/comunidades/comentarios/comment-1")
            posts = await client.get("/api/v1/comunidades/c1/publicacoes")
            removed_post = await client.delete("/api/v1/comunidades/publicacoes/p1")
            reply_to_removed_post = await client.post(
                "/api/v1/comunidades/publicacoes/p1/comentarios",
                json={"conteudo": "Ainda posso responder?"},
            )
    finally:
        app.dependency_overrides.clear()

    assert denied.status_code == 403
    assert removed.status_code == 204
    assert posts.json()[0]["comentarios"][0]["conteudo"] == ""
    assert posts.json()[0]["comentarios"][0]["removida_por_moderacao"] is True
    assert removed_post.status_code == 204
    assert reply_to_removed_post.status_code == 409
    assert reply_to_removed_post.json()["codigo"] == "PUBLICACAO_MODERADA"
