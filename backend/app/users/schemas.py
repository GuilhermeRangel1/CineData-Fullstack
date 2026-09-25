"""Contratos HTTP para contas e sessão local."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class TokenAcesso(BaseModel):
    """Sessão Bearer devolvida ao cliente após o login."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0)
    usuario: UsuarioLeitura
