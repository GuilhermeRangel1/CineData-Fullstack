"""Contratos da rede de amizades local."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContatoAmizade(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=32)
    nome: str = Field(min_length=1, max_length=120)
    avatar_url: str | None = None


class SolicitacaoAmizadeLeitura(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=32)
    status: Literal["pendente", "aceita", "bloqueada"]
    direcao: Literal["enviada", "recebida"]
    pessoa: ContatoAmizade
    criada_em: datetime


class RespostaSolicitacaoAmizade(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acao: Literal["aceitar", "bloquear"]
