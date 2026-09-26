"""Contratos públicos do domínio de filmes.

Esses schemas definem a comunicação da API e não expõem os modelos ORM.
"""

from datetime import date, datetime
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PapelPessoa = Literal["Ator", "Diretor", "Roteirista"]
OrdenacaoFilme = Literal["titulo", "ano_lancamento"]
DirecaoOrdenacao = Literal["asc", "desc"]
Visibilidade = Literal["publica", "privada"]
NomeGenero = Annotated[str, Field(min_length=1, max_length=50)]
NomePessoa = Annotated[str, Field(min_length=1, max_length=255)]
NomeProdutora = Annotated[str, Field(min_length=1, max_length=255)]


def validar_url_trailer(url: str | None) -> str | None:
    """Aceita somente URLs HTTPS que podem ser incorporadas com segurança."""

    if url is None:
        return None
    parsed = urlparse(url)
    hosts_validos = {"youtube.com", "www.youtube.com", "youtu.be", "www.youtube-nocookie.com"}
    if parsed.scheme != "https" or parsed.hostname not in hosts_validos:
        raise ValueError("Informe um link HTTPS válido do YouTube para o trailer.")
    return url


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
    nota: float = Field(ge=0, le=10)
    comentario: str = Field(min_length=1, max_length=4000)
    visibilidade: Visibilidade = "publica"


class AvaliacaoLeitura(AvaliacaoCriacao):
    id: str = Field(min_length=1, max_length=64)
    nome: str = Field(min_length=1, max_length=120)
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
    url_trailer: str | None = Field(default=None, max_length=2048)
    atores: list[NomePessoa] = Field(default_factory=list, max_length=200)
    roteiristas: list[NomePessoa] = Field(default_factory=list, max_length=200)
    produtoras: list[NomeProdutora] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validar_data_e_ano(self) -> "FilmeCriacao":
        """Impede ano de lançamento divergente da data informada."""

        if self.data_lancamento and self.ano_lancamento != self.data_lancamento.year:
            raise ValueError("O ano de lançamento deve corresponder à data informada.")
        return self

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

    _validar_url_trailer = field_validator("url_trailer")(validar_url_trailer)


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
    url_trailer: str | None = Field(default=None, max_length=2048)
    atores: list[NomePessoa] | None = Field(default=None, max_length=200)
    roteiristas: list[NomePessoa] | None = Field(default=None, max_length=200)
    produtoras: list[NomeProdutora] | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validar_campos_alterados(self) -> "FilmeAtualizacao":
        """Exige uma alteração e protege relações obrigatórias contra nulos."""

        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar o filme.")
        for campo in ("titulo", "diretor", "generos"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"O campo '{campo}' não pode ser nulo.")
        return self

    @field_validator("generos", "atores", "roteiristas", "produtoras")
    @classmethod
    def nomes_nao_podem_repetir(cls, valores: list[str] | None) -> list[str] | None:
        """Evita relações duplicadas antes de iniciar a transação."""

        if valores is None:
            return valores
        vistos: set[str] = set()
        for valor in valores:
            chave = valor.casefold()
            if chave in vistos:
                raise ValueError("Uma mesma relação não pode ser informada mais de uma vez.")
            vistos.add(chave)
        return valores

    _validar_url_trailer = field_validator("url_trailer")(validar_url_trailer)


class FilmeResumo(ContratoFilmes):
    id: str = Field(min_length=1, max_length=64)
    titulo: str = Field(min_length=1, max_length=500)
    ano_lancamento: int | None = None
    url_poster: str | None = None
    url_backdrop: str | None = None
    generos: list[GeneroResumo]
    nota_media: float | None = Field(default=None, ge=0, le=10)
    quantidade_avaliacoes: int = Field(ge=0)


class FilmeDetalhe(FilmeResumo):
    data_lancamento: date | None = None
    duracao_minutos: int | None = Field(default=None, ge=0)
    status_filme: str | None = None
    sinopse: str | None = None
    url_backdrop: str | None = None
    url_trailer: str | None = None
    pessoas: list[PessoaResumo]
    produtoras: list[ProdutoraResumo]
    desempenho: DesempenhoFilme | None = None
    avaliacoes: list[AvaliacaoLeitura]


class TrailerFilme(ContratoFilmes):
    url_trailer: str | None = None


class ConsultaCatalogo(ContratoFilmes):
    busca: str | None = Field(default=None, min_length=1, max_length=100)
    genero: str | None = Field(default=None, min_length=1, max_length=50)
    pessoa: str | None = Field(default=None, min_length=1, max_length=255)
    produtora: str | None = Field(default=None, min_length=1, max_length=255)
    ano_inicial: int | None = Field(default=None, ge=1888, le=2100)
    ano_final: int | None = Field(default=None, ge=1888, le=2100)
    duracao_minima: int | None = Field(default=None, ge=1, le=1000)
    duracao_maxima: int | None = Field(default=None, ge=1, le=1000)
    nota_minima: float | None = Field(default=None, ge=0, le=10)
    pagina: int = Field(default=1, ge=1)
    tamanho_pagina: int = Field(default=12, ge=1, le=100)
    ordenar_por: OrdenacaoFilme = "titulo"
    direcao: DirecaoOrdenacao = "asc"
    priorizar_capa: bool = False
    priorizar_trailer: bool = False
    somente_com_trailer: bool = False

    @field_validator(
        "pessoa",
        "produtora",
        "ano_inicial",
        "ano_final",
        "duracao_minima",
        "duracao_maxima",
        "nota_minima",
        mode="before",
    )
    @classmethod
    def tratar_filtros_vazios(cls, valor: object) -> object:
        """Evita que campos em branco do formulário virem filtros inválidos."""

        if isinstance(valor, str) and valor.strip().casefold() in {"", "null", "undefined"}:
            return None
        return valor

    @model_validator(mode="after")
    def validar_intervalo_de_anos(self) -> "ConsultaCatalogo":
        if self.ano_inicial and self.ano_final and self.ano_inicial > self.ano_final:
            raise ValueError("O ano inicial não pode ser maior que o ano final.")
        if (
            self.duracao_minima
            and self.duracao_maxima
            and self.duracao_minima > self.duracao_maxima
        ):
            raise ValueError("A duração mínima não pode ser maior que a duração máxima.")
        return self
