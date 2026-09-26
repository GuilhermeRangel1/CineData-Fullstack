"""Contratos HTTP para descoberta e interação em comunidades."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.movies.schemas import FilmeResumo


class ContratoComunidades(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ComunidadeCriacao(ContratoComunidades):
    nome: str = Field(min_length=1, max_length=120)
    descricao: str = Field(min_length=1, max_length=1000)


class ComunidadeAtualizacao(ContratoComunidades):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    descricao: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def exigir_alteracao(self) -> "ComunidadeAtualizacao":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar a comunidade.")
        return self


class PessoaComunidade(BaseModel):
    id: str
    nome: str
    avatar_url: str | None = None


class ComunidadeLeitura(BaseModel):
    id: str
    nome: str
    descricao: str
    quantidade_membros: int = Field(ge=0)
    visualizacoes: int = Field(default=0, ge=0)
    criada_em: datetime


class PublicacaoCriacao(ContratoComunidades):
    conteudo: str = Field(min_length=1, max_length=4000)
    movie_id: str | None = Field(default=None, min_length=1, max_length=50)


class ComentarioCriacao(ContratoComunidades):
    conteudo: str = Field(min_length=1, max_length=2000)


class ReacaoCriacao(ContratoComunidades):
    tipo: Literal["curtir", "amei", "interessante"] = "curtir"


class ReacaoResumo(BaseModel):
    tipo: Literal["curtir", "amei", "interessante"]
    quantidade: int = Field(ge=0)


class ComentarioLeitura(BaseModel):
    id: str
    conteudo: str
    autor: PessoaComunidade
    criado_em: datetime


class PublicacaoLeitura(BaseModel):
    id: str
    comunidade_id: str
    conteudo: str
    autor: PessoaComunidade
    filme: FilmeResumo | None = None
    comentarios: list[ComentarioLeitura]
    reacoes: list[ReacaoResumo]
    criada_em: datetime
