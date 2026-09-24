"""Contratos públicos do domínio de filmes.

Esses schemas definem a comunicação da API e não expõem os modelos ORM.
"""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PapelPessoa = Literal["Ator", "Diretor", "Roteirista"]
OrdenacaoFilme = Literal["titulo", "ano_lancamento"]
DirecaoOrdenacao = Literal["asc", "desc"]
NomeGenero = Annotated[str, Field(min_length=1, max_length=50)]
NomePessoa = Annotated[str, Field(min_length=1, max_length=255)]
NomeProdutora = Annotated[str, Field(min_length=1, max_length=255)]


class ContratoFilmes(BaseModel):
    """Configuração compartilhada pelos contratos de filmes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GeneroResumo(ContratoFilmes):
    id: str = Field(min_length=1, max_length=64)
    nome: str = Field(min_length=1, max_length=50)


class ProdutoraResumo(ContratoFilmes):
    id: str = Field(min_length=1, max_length=64)
    nome: str = Field(min_length=1, max_length=255)


class PessoaResumo(ContratoFilmes):
    id: str = Field(min_length=1, max_length=64)
    nome: str = Field(min_length=1, max_length=255)
    papel: PapelPessoa


class AvaliacaoCriacao(ContratoFilmes):
    nome: str = Field(min_length=1, max_length=120)
    nota: float = Field(ge=0, le=10)
    comentario: str = Field(min_length=1, max_length=4000)


class AvaliacaoLeitura(AvaliacaoCriacao):
    id: str = Field(min_length=1, max_length=64)
    criada_em: datetime


class DesempenhoFilme(ContratoFilmes):
    orcamento_usd: float | None = None
    receita_usd: float | None = None
    lucro_usd: float | None = None
    orcamento_brl: float | None = None
    receita_brl: float | None = None
    lucro_brl: float | None = None
    popularidade: float | None = None
    nota_tmdb: float | None = Field(default=None, ge=0, le=10)
    quantidade_tmdb: int | None = Field(default=None, ge=0)
    nota_imdb: float | None = Field(default=None, ge=0, le=10)
    quantidade_imdb: int | None = Field(default=None, ge=0)


class FilmeCriacao(ContratoFilmes):
    titulo: str = Field(min_length=1, max_length=500)
    diretor: str = Field(min_length=1, max_length=255)
    ano_lancamento: int | None = Field(default=None, ge=1888, le=2100)
    generos: list[NomeGenero] = Field(min_length=1, max_length=20)
    sinopse: str | None = Field(default=None, max_length=4000)
    data_lancamento: date | None = None
    duracao_minutos: int | None = Field(default=None, ge=0)
    status_filme: str | None = Field(default=None, max_length=50)
    url_poster: str | None = Field(default=None, max_length=2048)
    url_backdrop: str | None = Field(default=None, max_length=2048)
    atores: list[NomePessoa] = Field(default_factory=list, max_length=200)
    roteiristas: list[NomePessoa] = Field(default_factory=list, max_length=200)
    produtoras: list[NomeProdutora] = Field(default_factory=list, max_length=100)

    @field_validator("generos", "atores", "roteiristas", "produtoras")
    @classmethod
    def nomes_nao_podem_repetir(cls, valores: list[str]) -> list[str]:
        """Evita relações duplicadas antes de iniciar a transação."""

        vistos: set[str] = set()
        for valor in valores:
            chave = valor.casefold()
            if chave in vistos:
                raise ValueError("Uma mesma relação não pode ser informada mais de uma vez.")
            vistos.add(chave)
        return valores


class FilmeAtualizacao(ContratoFilmes):
    titulo: str | None = Field(default=None, min_length=1, max_length=500)
    diretor: str | None = Field(default=None, min_length=1, max_length=255)
    ano_lancamento: int | None = Field(default=None, ge=1888, le=2100)
    generos: list[NomeGenero] | None = Field(default=None, min_length=1, max_length=20)
    sinopse: str | None = Field(default=None, max_length=4000)
    data_lancamento: date | None = None
    duracao_minutos: int | None = Field(default=None, ge=0)
    status_filme: str | None = Field(default=None, max_length=50)
    url_poster: str | None = Field(default=None, max_length=2048)
    url_backdrop: str | None = Field(default=None, max_length=2048)
    atores: list[NomePessoa] | None = Field(default=None, max_length=200)
    roteiristas: list[NomePessoa] | None = Field(default=None, max_length=200)
    produtoras: list[NomeProdutora] | None = Field(default=None, max_length=100)


class FilmeResumo(ContratoFilmes):
    id: str = Field(min_length=1, max_length=64)
    titulo: str = Field(min_length=1, max_length=500)
    ano_lancamento: int | None = None
    url_poster: str | None = None
    generos: list[GeneroResumo]
    nota_media: float | None = Field(default=None, ge=0, le=10)
    quantidade_avaliacoes: int = Field(ge=0)


class FilmeDetalhe(FilmeResumo):
    data_lancamento: date | None = None
    duracao_minutos: int | None = Field(default=None, ge=0)
    status_filme: str | None = None
    sinopse: str | None = None
    url_backdrop: str | None = None
    pessoas: list[PessoaResumo]
    produtoras: list[ProdutoraResumo]
    desempenho: DesempenhoFilme | None = None
    avaliacoes: list[AvaliacaoLeitura]


class ConsultaCatalogo(ContratoFilmes):
    busca: str | None = Field(default=None, min_length=1, max_length=100)
    genero: str | None = Field(default=None, min_length=1, max_length=50)
    pagina: int = Field(default=1, ge=1)
    tamanho_pagina: int = Field(default=12, ge=1, le=100)
    ordenar_por: OrdenacaoFilme = "titulo"
    direcao: DirecaoOrdenacao = "asc"
