"""Contratos HTTP para descoberta e interação em comunidades."""

import base64
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.movies.schemas import FilmeResumo


class ContratoComunidades(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def validar_imagem_comunidade(imagem_url: str | None) -> str | None:
    if imagem_url is None:
        return None
    correspondencia = re.fullmatch(
        r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", imagem_url
    )
    if not correspondencia:
        raise ValueError("Envie uma imagem PNG, JPEG ou WebP válida.")
    try:
        conteudo = base64.b64decode(correspondencia.group(2), validate=True)
    except ValueError as error:
        raise ValueError("Envie uma imagem válida.") from error
    if not conteudo or len(conteudo) > 1_000_000:
        raise ValueError("A imagem deve ter no máximo 1 MB.")
    return imagem_url


class ComunidadeCriacao(ContratoComunidades):
    nome: str = Field(min_length=1, max_length=120)
    descricao: str = Field(min_length=1, max_length=1000)
    imagem_url: str | None = Field(default=None, max_length=1_400_000)

    _validar_imagem = field_validator("imagem_url")(validar_imagem_comunidade)


class ComunidadeAtualizacao(ContratoComunidades):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    descricao: str | None = Field(default=None, min_length=1, max_length=1000)
    imagem_url: str | None = Field(default=None, max_length=1_400_000)

    _validar_imagem = field_validator("imagem_url")(validar_imagem_comunidade)

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
    imagem_url: str | None = None
    quantidade_membros: int = Field(ge=0)
    visualizacoes: int = Field(default=0, ge=0)
    criada_em: datetime


class PublicacaoCriacao(ContratoComunidades):
    conteudo: str = Field(min_length=1, max_length=4000)
    movie_id: str | None = Field(default=None, min_length=1, max_length=50)


class ComentarioCriacao(ContratoComunidades):
    conteudo: str = Field(min_length=1, max_length=2000)


class ReacaoCriacao(ContratoComunidades):
    tipo: Literal["curtir", "amei", "interessante", "nao_curti"] = "curtir"


class ReacaoResumo(BaseModel):
    tipo: Literal["curtir", "amei", "interessante", "nao_curti"]
    quantidade: int = Field(ge=0)


class ComentarioLeitura(BaseModel):
    id: str
    conteudo: str
    removida_por_moderacao: bool = False
    autor: PessoaComunidade
    criado_em: datetime


class PublicacaoLeitura(BaseModel):
    id: str
    comunidade_id: str
    conteudo: str
    removida_por_moderacao: bool = False
    autor: PessoaComunidade
    filme: FilmeResumo | None = None
    comentarios: list[ComentarioLeitura]
    reacoes: list[ReacaoResumo]
    criada_em: datetime
