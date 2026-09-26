"""Contratos da área pessoal: listas e filmes marcados pelo usuário."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.movies.schemas import FilmeResumo


class ContratoListas(BaseModel):
    """Regras comuns às listas persistidas de uma conta."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ListaCriacao(ContratoListas):
    nome: str = Field(min_length=1, max_length=120)
    visibilidade: Literal["publica", "privada"] = "privada"


class ListaAtualizacao(ContratoListas):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    visibilidade: Literal["publica", "privada"] | None = None

    @model_validator(mode="after")
    def exigir_alteracao(self) -> "ListaAtualizacao":
        """Impede uma atualização vazia antes de chegar ao caso de uso."""

        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar a lista.")
        return self


class ListaLeitura(ContratoListas):
    id: str = Field(min_length=1, max_length=32)
    nome: str = Field(min_length=1, max_length=120)
    visibilidade: Literal["publica", "privada"]
    quantidade_filmes: int = Field(ge=0)
    criada_em: datetime


class ListaDetalhe(ListaLeitura):
    filmes: list[FilmeResumo]
