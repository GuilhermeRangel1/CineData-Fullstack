"""Garante que a administração acumula, sem perder, as permissões de usuário."""

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.communities.models import Community
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.movies.models import DimGenre, DimMovie
from app.users.models import User
from app.users.security import gerar_hash_senha
from app.users.tokens import criar_token_acesso


@pytest.fixture
async def rbac_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
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


async def test_admin_can_execute_all_authenticated_user_flows(
    rbac_session_factory: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "segredo-de-teste-com-tamanho-suficiente")
    get_settings.cache_clear()
    admin = User(
        id="admin-rbac",
        email="admin@example.com",
        nome="Admin",
        password_hash=gerar_hash_senha("senha-segura"),
        role="admin",
    )
    pessoa = User(
        id="pessoa-rbac",
        email="pessoa@example.com",
        nome="Pessoa",
        password_hash=gerar_hash_senha("senha-segura"),
    )
    async with rbac_session_factory() as session:
        session.add_all(
            [
                admin,
                pessoa,
                DimMovie(
                    id_filme="movie-rbac",
                    titulo="Filme para permissões",
                    genres=[DimGenre(nome_genero="Drama")],
                ),
                Community(id="community-rbac", nome="Clube RBAC", descricao="Comunidade de teste."),
            ]
        )
        await session.commit()

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with rbac_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            admin_headers = {"Authorization": f"Bearer {criar_token_acesso(admin).access_token}"}
            person_headers = {"Authorization": f"Bearer {criar_token_acesso(pessoa).access_token}"}

            assert (
                await client.patch(
                    "/api/v1/auth/perfil", headers=admin_headers, json={"nome": "Admin Atualizado"}
                )
            ).status_code == 200

            lista = await client.post(
                "/api/v1/minha-conta/listas",
                headers=admin_headers,
                json={"nome": "Minha lista", "visibilidade": "publica"},
            )
            assert lista.status_code == 201
            lista_id = lista.json()["id"]
            assert (
                await client.post(
                    f"/api/v1/minha-conta/listas/{lista_id}/filmes/movie-rbac",
                    headers=admin_headers,
                )
            ).status_code == 200
            assert (
                await client.patch(
                    f"/api/v1/minha-conta/listas/{lista_id}",
                    headers=admin_headers,
                    json={"nome": "Lista editada"},
                )
            ).status_code == 200
            assert (
                await client.delete(
                    f"/api/v1/minha-conta/listas/{lista_id}/filmes/movie-rbac",
                    headers=admin_headers,
                )
            ).status_code == 204
            assert (
                await client.delete(f"/api/v1/minha-conta/listas/{lista_id}", headers=admin_headers)
            ).status_code == 204
            assert (
                await client.put(
                    "/api/v1/minha-conta/assistir-depois/movie-rbac", headers=admin_headers
                )
            ).status_code == 204
            assert (
                await client.get("/api/v1/minha-conta/assistir-depois", headers=admin_headers)
            ).status_code == 200
            assert (
                await client.delete(
                    "/api/v1/minha-conta/assistir-depois/movie-rbac", headers=admin_headers
                )
            ).status_code == 204
            assert (
                await client.post(
                    "/api/v1/filmes/movie-rbac/avaliacoes",
                    headers=admin_headers,
                    json={"nota": 8, "comentario": "Boa sessão."},
                )
            ).status_code == 201

            pedido_recebido = await client.post(
                "/api/v1/minha-conta/amigos/solicitacoes/admin-rbac", headers=person_headers
            )
            assert pedido_recebido.status_code == 201
            assert (
                await client.patch(
                    f"/api/v1/minha-conta/amigos/solicitacoes/{pedido_recebido.json()['id']}",
                    headers=admin_headers,
                    json={"acao": "aceitar"},
                )
            ).status_code == 200
            assert (
                await client.delete("/api/v1/minha-conta/amigos/pessoa-rbac", headers=admin_headers)
            ).status_code == 204
            assert (
                await client.post(
                    "/api/v1/minha-conta/amigos/solicitacoes/pessoa-rbac", headers=admin_headers
                )
            ).status_code == 201

            assert (
                await client.post(
                    "/api/v1/comunidades/community-rbac/participacao", headers=admin_headers
                )
            ).status_code == 204
            publicacao = await client.post(
                "/api/v1/comunidades/community-rbac/publicacoes",
                headers=admin_headers,
                json={"conteudo": "Admin também participa."},
            )
            assert publicacao.status_code == 201
            publicacao_id = publicacao.json()["id"]
            assert (
                await client.post(
                    f"/api/v1/comunidades/publicacoes/{publicacao_id}/comentarios",
                    headers=admin_headers,
                    json={"conteudo": "Comentário."},
                )
            ).status_code == 201
            assert (
                await client.post(
                    f"/api/v1/comunidades/publicacoes/{publicacao_id}/reacoes",
                    headers=admin_headers,
                    json={"tipo": "curtir"},
                )
            ).status_code == 200
            assert (
                await client.delete(
                    f"/api/v1/comunidades/publicacoes/{publicacao_id}/reacoes",
                    headers=admin_headers,
                )
            ).status_code == 204
            assert (
                await client.delete(
                    "/api/v1/comunidades/community-rbac/participacao", headers=admin_headers
                )
            ).status_code == 204
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
