"""Contratos compartilhados pelas respostas da API v1."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ItemT = TypeVar("ItemT")


class ErroApi(BaseModel):
    """Formato estável e seguro para erros retornados pela API."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(min_length=1, max_length=100)
    mensagem: str = Field(min_length=1, max_length=500)


class MetadadosPagina(BaseModel):
    """Informações necessárias para navegar uma coleção paginada."""

    model_config = ConfigDict(extra="forbid")

    pagina: int = Field(ge=1)
    tamanho_pagina: int = Field(ge=1, le=100)
    total_itens: int = Field(ge=0)
    total_paginas: int = Field(ge=0)


class Pagina(BaseModel, Generic[ItemT]):
    """Envelope padrão para coleções paginadas."""

    model_config = ConfigDict(extra="forbid")

    itens: list[ItemT]
    meta: MetadadosPagina
