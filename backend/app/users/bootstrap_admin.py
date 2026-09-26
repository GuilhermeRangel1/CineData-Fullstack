"""Cria, uma única vez, o administrador inicial configurado no ambiente."""

import asyncio

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.users.schemas import UsuarioCadastroInicial
from app.users.services import AuthService


def _dados_administrador() -> UsuarioCadastroInicial:
    settings = get_settings()
    values = {
        "email": settings.initial_admin_email,
        "nome": settings.initial_admin_name,
        "senha": settings.initial_admin_password,
    }
    if not all(values.values()):
        raise SystemExit(
            "Defina INITIAL_ADMIN_EMAIL, INITIAL_ADMIN_NAME e INITIAL_ADMIN_PASSWORD "
            "para criar o administrador inicial."
        )
    return UsuarioCadastroInicial(**values)


async def main() -> None:
    """Executa o bootstrap e informa apenas se a conta foi criada."""

    dados = _dados_administrador()
    async with AsyncSessionLocal() as session:
        usuario, criado = await AuthService(session).criar_administrador_inicial(dados)
    await engine.dispose()
    mensagem = "Administrador inicial criado" if criado else "Administrador inicial já existe"
    print(f"{mensagem}: {usuario.email}")


if __name__ == "__main__":
    asyncio.run(main())
