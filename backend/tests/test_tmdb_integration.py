import httpx
import pytest

from app.core.errors import FonteExternaIndisponivelError, PermissaoNegadaError
from app.integrations.tmdb import TmdbGateway
from app.main import app
from app.users.dependencies import get_current_admin
from app.users.models import User


async def test_tmdb_gateway_maps_search_and_import_data() -> None:
    def responder(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer token-de-teste"
        if request.url.path.endswith("/search/movie"):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": 4935,
                            "title": "O Castelo Animado",
                            "original_title": "Hauru no Ugoku Shiro",
                            "release_date": "2004-11-20",
                            "poster_path": "/poster.jpg",
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "title": "O Castelo Animado",
                "release_date": "2004-11-20",
                "overview": "Uma jovem encontra um castelo mágico.",
                "genres": [{"name": "Animação"}, {"name": "Fantasia"}],
                "poster_path": "/poster.jpg",
                "backdrop_path": "/backdrop.jpg",
                "credits": {"crew": [{"job": "Director", "name": "Hayao Miyazaki"}]},
                "videos": {
                    "results": [{"site": "YouTube", "type": "Trailer", "key": "trailer-oficial"}]
                },
            },
        )

    gateway = TmdbGateway("token-de-teste", transport=httpx.MockTransport(responder))
    resultados = await gateway.buscar("Castelo")
    importacao = await gateway.obter(4935)

    assert resultados[0].titulo == "O Castelo Animado"
    assert resultados[0].titulo_original == "Hauru no Ugoku Shiro"
    assert resultados[0].ano_lancamento == 2004
    assert resultados[0].url_poster == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert importacao.diretor == "Hayao Miyazaki"
    assert importacao.generos == ["Animação", "Fantasia"]
    assert importacao.url_trailer == "https://www.youtube.com/watch?v=trailer-oficial"


async def test_tmdb_gateway_collects_titles_in_portuguese_and_english() -> None:
    def responder(request: httpx.Request) -> httpx.Response:
        idioma = request.url.params["language"]
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 129,
                        "title": "A Viagem de Chihiro"
                        if idioma == "pt-BR"
                        else "Spirited Away",
                        "original_title": "Sen to Chihiro no kamikakushi",
                        "release_date": "2001-07-20",
                    }
                ]
            },
        )

    gateway = TmdbGateway("token-de-teste", transport=httpx.MockTransport(responder))
    titulos = await gateway.buscar_titulos_equivalentes("A Viagem de Chihiro")

    assert titulos == {
        "a viagem de chihiro",
        "spirited away",
        "sen to chihiro no kamikakushi",
    }


async def test_tmdb_gateway_requires_a_configured_token() -> None:
    with pytest.raises(FonteExternaIndisponivelError):
        await TmdbGateway(None).buscar("Castelo")


async def test_tmdb_route_is_admin_only_and_does_not_expose_the_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def admin() -> User:
        return User(
            id="admin", email="admin@example.com", nome="Admin", password_hash="hash", role="admin"
        )

    async def buscar(self: TmdbGateway, busca: str, ano: int | None = None) -> list:
        del self, busca, ano
        return []

    monkeypatch.setattr(TmdbGateway, "buscar", buscar)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

            async def negado() -> User:
                raise PermissaoNegadaError

            app.dependency_overrides[get_current_admin] = negado
            denied = await client.get(
                "/api/v1/admin/fontes/tmdb/busca", params={"busca": "Castelo"}
            )
            app.dependency_overrides[get_current_admin] = admin
            response = await client.get(
                "/api/v1/admin/fontes/tmdb/busca", params={"busca": "Castelo"}
            )
    finally:
        app.dependency_overrides.clear()

    assert denied.status_code == 403
    assert response.status_code == 200
    assert response.json() == []
