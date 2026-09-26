"""Cliente mínimo e defensivo para pesquisa de metadados no TMDB."""

import asyncio
from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import FonteExternaIndisponivelError

TMDB_API_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/original"


class TmdbResultado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    titulo: str = Field(min_length=1, max_length=500)
    titulo_original: str | None = Field(default=None, max_length=500)
    ano_lancamento: int | None = Field(default=None, ge=1888, le=2100)
    url_poster: str | None = None


class TmdbImportacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, max_length=500)
    diretor: str | None = Field(default=None, max_length=255)
    generos: list[str] = Field(default_factory=list, max_length=20)
    sinopse: str | None = Field(default=None, max_length=4000)
    ano_lancamento: int | None = Field(default=None, ge=1888, le=2100)
    data_lancamento: date | None = None
    url_poster: str | None = Field(default=None, max_length=2048)
    url_backdrop: str | None = Field(default=None, max_length=2048)
    url_trailer: str | None = Field(default=None, max_length=2048)


class TmdbGateway:
    def __init__(
        self, token: str | None, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._token = token
        self._transport = transport

    async def buscar(
        self, busca: str, ano: int | None = None, idioma: str = "pt-BR"
    ) -> list[TmdbResultado]:
        payload = await self._obter(
            "/search/movie",
            {
                "query": busca,
                "language": idioma,
                "include_adult": "false",
                **({"year": ano} if ano else {}),
            },
        )
        resultados = payload.get("results") if isinstance(payload, dict) else []
        if not isinstance(resultados, list):
            return []
        return [resultado for item in resultados[:8] if (resultado := self._para_resultado(item))]

    async def buscar_titulos_equivalentes(
        self, busca: str, ano: int | None = None
    ) -> set[str]:
        resultados_pt, resultados_en = await asyncio.gather(
            self.buscar(busca, ano, "pt-BR"),
            self.buscar(busca, ano, "en-US"),
        )
        return {
            titulo.casefold()
            for resultado in [*resultados_pt, *resultados_en]
            for titulo in (resultado.titulo, resultado.titulo_original)
            if titulo
        }

    async def obter(self, tmdb_id: int) -> TmdbImportacao:
        payload = await self._obter(
            f"/movie/{tmdb_id}", {"language": "pt-BR", "append_to_response": "credits,videos"}
        )
        if not isinstance(payload, dict):
            raise FonteExternaIndisponivelError
        return self._para_importacao(payload)

    async def _obter(self, caminho: str, parametros: dict[str, str | int]) -> Any:
        if not self._token:
            raise FonteExternaIndisponivelError
        try:
            async with httpx.AsyncClient(timeout=8, transport=self._transport) as cliente:
                resposta = await cliente.get(
                    f"{TMDB_API_URL}{caminho}",
                    params=parametros,
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Accept": "application/json",
                    },
                )
                resposta.raise_for_status()
                return resposta.json()
        except (httpx.HTTPError, ValueError) as erro:
            raise FonteExternaIndisponivelError from erro

    @staticmethod
    def _imagem(caminho: object) -> str | None:
        return f"{TMDB_IMAGE_URL}{caminho}" if isinstance(caminho, str) and caminho else None

    def _para_resultado(self, item: object) -> TmdbResultado | None:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int):
            return None
        titulo = item.get("title") or item.get("original_title")
        if not isinstance(titulo, str) or not titulo.strip():
            return None
        titulo_original = item.get("original_title")
        ano = self._ano(item.get("release_date"))
        return TmdbResultado(
            id=item["id"],
            titulo=titulo.strip(),
            titulo_original=(
                titulo_original.strip()
                if isinstance(titulo_original, str) and titulo_original.strip()
                else None
            ),
            ano_lancamento=ano,
            url_poster=self._imagem(item.get("poster_path")),
        )

    def _para_importacao(self, item: dict[str, Any]) -> TmdbImportacao:
        creditos = item.get("credits") if isinstance(item.get("credits"), dict) else {}
        equipe = creditos.get("crew") if isinstance(creditos.get("crew"), list) else []
        diretor = next(
            (
                pessoa.get("name")
                for pessoa in equipe
                if isinstance(pessoa, dict)
                and pessoa.get("job") == "Director"
                and isinstance(pessoa.get("name"), str)
            ),
            None,
        )
        videos = item.get("videos") if isinstance(item.get("videos"), dict) else {}
        trailer = next(
            (
                video.get("key")
                for video in videos.get("results", [])
                if isinstance(video, dict)
                and video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
                and isinstance(video.get("key"), str)
            ),
            None,
        )
        generos = [
            genero["name"]
            for genero in item.get("genres", [])
            if isinstance(genero, dict) and isinstance(genero.get("name"), str)
        ][:20]
        data = self._data(item.get("release_date"))
        titulo = item.get("title") or item.get("original_title")
        return TmdbImportacao(
            titulo=titulo.strip() if isinstance(titulo, str) and titulo.strip() else None,
            diretor=diretor,
            generos=generos,
            sinopse=item.get("overview")
            if isinstance(item.get("overview"), str) and item["overview"].strip()
            else None,
            ano_lancamento=data.year if data else None,
            data_lancamento=data,
            url_poster=self._imagem(item.get("poster_path")),
            url_backdrop=self._imagem(item.get("backdrop_path")),
            url_trailer=f"https://www.youtube.com/watch?v={trailer}" if trailer else None,
        )

    @staticmethod
    def _data(valor: object) -> date | None:
        if not isinstance(valor, str) or not valor:
            return None
        try:
            return date.fromisoformat(valor)
        except ValueError:
            return None

    def _ano(self, valor: object) -> int | None:
        data = self._data(valor)
        return data.year if data and 1888 <= data.year <= 2100 else None
