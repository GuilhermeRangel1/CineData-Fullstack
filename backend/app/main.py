import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.api.v1.schemas import ErroApi
from app.core.config import get_settings
from app.core.errors import ErroDominio
from app.core.logging import configure_logging
from app.db.session import engine

configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Libera recursos de infraestrutura quando a aplicação é encerrada."""

    del app
    # A criação/evolução do schema é responsabilidade exclusiva do Alembic.
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=settings.project_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
        max_age=600,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Evita vazar detalhes internos de validação no contrato público."""

        del request, exc
        erro = ErroApi(
            codigo="REQUISICAO_INVALIDA",
            mensagem="Dados da requisição são inválidos.",
        )
        return JSONResponse(status_code=422, content=erro.model_dump())

    @app.exception_handler(ErroDominio)
    async def domain_error_handler(request: Request, exc: ErroDominio) -> JSONResponse:
        """Converte erros controlados em respostas públicas sem detalhes internos."""

        del request
        erro = ErroApi(codigo=exc.codigo, mensagem=exc.mensagem)
        return JSONResponse(
            status_code=exc.status_code,
            content=erro.model_dump(),
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Registra o erro técnico sem expor detalhes internos ao cliente."""

        logger.exception("Erro inesperado em %s %s", request.method, request.url.path)
        del exc
        erro = ErroApi(
            codigo="ERRO_INTERNO",
            mensagem="Não foi possível concluir a operação no momento.",
        )
        return JSONResponse(status_code=500, content=erro.model_dump())

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
