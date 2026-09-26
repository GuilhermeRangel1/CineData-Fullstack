"""Contratos públicos do painel administrativo."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MetricaAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chave: str
    rotulo: str
    valor: int = Field(ge=0)
    detalhe: str


class PontoEvolucaoAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: date
    usuarios: int = Field(ge=0)
    avaliacoes: int = Field(ge=0)
    listas: int = Field(ge=0)
    publicacoes: int = Field(ge=0)


class GeneroAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str
    quantidade: int = Field(ge=0)
    nota_media: float | None = Field(default=None, ge=0, le=10)


class FilmeAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    titulo: str
    url_poster: str | None = None
    quantidade_avaliacoes: int = Field(ge=0)
    nota_media: float | None = Field(default=None, ge=0, le=10)


class ComunidadeAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    nome: str
    imagem_url: str | None = None
    membros: int = Field(ge=0)
    publicacoes: int = Field(ge=0)
    visualizacoes: int = Field(ge=0)


class ResumoAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodo_dias: int = Field(ge=1)
    metricas: list[MetricaAnalytics]
    evolucao: list[PontoEvolucaoAnalytics]
    generos: list[GeneroAnalytics]
    filmes_mais_avaliados: list[FilmeAnalytics]
    comunidades_em_alta: list[ComunidadeAnalytics]
