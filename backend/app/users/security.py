"""Funções de hash e verificação de senhas locais."""

from pwdlib import PasswordHash

_password_hasher = PasswordHash.recommended()


def gerar_hash_senha(senha: str) -> str:
    """Gera um hash Argon2 para uma senha que acabou de ser cadastrada."""

    return _password_hasher.hash(senha)


def verificar_senha(senha: str, password_hash: str) -> bool:
    """Compara uma senha de login ao hash persistido sem expor a senha."""

    return _password_hasher.verify(senha, password_hash)
