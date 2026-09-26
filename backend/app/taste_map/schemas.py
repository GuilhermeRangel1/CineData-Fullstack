"""Contratos públicos do mapa de gostos."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContratoMapaGostos(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NoMapaGostos(ContratoMapaGostos):
    id: str = Field(min_length=1, max_length=64)
    titulo: str = Field(min_length=1, max_length=500)
    ano_lancamento: int | None = None
    url_poster: str | None = None
    genero_principal: str | None = None
    generos: list[str] = Field(default_factory=list)
    nota_usuario: float | None = Field(default=None, ge=0, le=10)
    tipo: Literal["avaliado", "recomendado"]
    afinidade: float | None = Field(default=None, ge=0, le=1)


class ArestaMapaGostos(ContratoMapaGostos):
    origem: str = Field(min_length=1, max_length=64)
    destino: str = Field(min_length=1, max_length=64)
    peso: float = Field(ge=0, le=1)
    explicacao: str = Field(min_length=1, max_length=300)


class MapaGostos(ContratoMapaGostos):
    nos: list[NoMapaGostos]
    arestas: list[ArestaMapaGostos]
    total_avaliados: int = Field(ge=0)
    limite_nos: int = Field(ge=6, le=48)
    vizinhos_por_filme: int = Field(ge=1, le=6)
