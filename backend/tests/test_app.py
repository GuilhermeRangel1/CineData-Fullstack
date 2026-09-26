import httpx

from app.main import app, create_app


async def test_health_check() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_cors_accepts_only_configured_local_origin() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        allowed = await client.options(
            "/api/v1/filmes",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        blocked = await client.options(
            "/api/v1/filmes",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "POST" in allowed.headers["access-control-allow-methods"]
    assert "Authorization" in allowed.headers["access-control-allow-headers"]
    assert blocked.status_code == 400
    assert "access-control-allow-origin" not in blocked.headers


async def test_unexpected_errors_do_not_expose_internal_details() -> None:
    isolated_app = create_app()

    @isolated_app.get("/explode")
    async def explode() -> None:
        raise RuntimeError("segredo-interno-que-nao-pode-vazar")

    transport = httpx.ASGITransport(app=isolated_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/explode")

    assert response.status_code == 500
    assert response.json() == {
        "codigo": "ERRO_INTERNO",
        "mensagem": "Não foi possível concluir a operação no momento.",
    }
    assert "segredo-interno" not in response.text
