"""Contratos HTTP para contas e sessão local."""

import base64
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.movies.schemas import AvaliacaoLeitura, FilmeResumo


class ContratoAuth(BaseModel):
    """Regras comuns aos dados de autenticação recebidos pela API."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CredenciaisLogin(ContratoAuth):
    email: str = Field(min_length=3, max_length=320)
    senha: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, email: str) -> str:
        """Aceita um e-mail simples e persiste uma forma canônica."""

        local, separador, dominio = email.partition("@")
        if not separador or not local or not dominio or "." not in dominio:
            raise ValueError("Informe um e-mail válido.")
        return email.casefold()


class UsuarioCadastro(CredenciaisLogin):
    nome: str = Field(min_length=1, max_length=120)


class UsuarioLeitura(BaseModel):
    """Dados públicos de uma conta, sem senha ou hash."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    nome: str
    role: Literal["user", "admin"]
    created_at: datetime
    avatar_url: str | None = None


class UsuarioAtualizacao(ContratoAuth):
    """Campos que uma pessoa pode alterar no próprio perfil."""

    nome: str | None = Field(default=None, min_length=1, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=1_400_000)

    @field_validator("avatar_url")
    @classmethod
    def validar_avatar(cls, avatar_url: str | None) -> str | None:
        if avatar_url is None:
            return None
        correspondencia = re.fullmatch(
            r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)", avatar_url
        )
        if not correspondencia:
            raise ValueError("Envie uma imagem PNG, JPEG ou WebP válida.")
        try:
            conteudo = base64.b64decode(correspondencia.group(2), validate=True)
        except ValueError as error:
            raise ValueError("Envie uma imagem válida.") from error
        if not conteudo or len(conteudo) > 1_000_000:
            raise ValueError("A imagem deve ter no máximo 1 MB.")
        return avatar_url

    @model_validator(mode="after")
    def exigir_alteracao(self) -> "UsuarioAtualizacao":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar o perfil.")
        return self


class AvaliacaoPerfil(AvaliacaoLeitura):
    filme: FilmeResumo


class PerfilPublico(BaseModel):
    """Visão pública de uma conta, sem e-mail ou dados de autenticação."""

    model_config = ConfigDict(extra="forbid")

    id: str
    nome: str
    avatar_url: str | None = None
    quantidade_amigos: int = Field(ge=0)
    avaliacoes: list[AvaliacaoPerfil]
    listas_publicas: list["ListaPublica"]


class ListaPublica(BaseModel):
    id: str
    nome: str
    quantidade_filmes: int = Field(ge=0)
    filmes: list[FilmeResumo]


class TokenAcesso(BaseModel):
    """Sessão Bearer devolvida ao cliente após o login."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0)
    usuario: UsuarioLeitura
