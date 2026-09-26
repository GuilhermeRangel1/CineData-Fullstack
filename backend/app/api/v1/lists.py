"""Rotas autenticadas para organizar os filmes da própria conta."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.movies.schemas import FilmeResumo
from app.users.dependencies import get_current_user
from app.users.list_schemas import ListaAtualizacao, ListaCriacao, ListaDetalhe, ListaLeitura
from app.users.list_services import ListasService
from app.users.models import User

lists_router = APIRouter(prefix="/minha-conta", tags=["listas"])


@lists_router.get("/listas", response_model=list[ListaLeitura])
async def listar_listas(
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> list[ListaLeitura]:
    """Lista somente as listas personalizadas pertencentes à conta atual."""

    return await ListasService(session).listar(usuario)


@lists_router.post("/listas", response_model=ListaLeitura, status_code=status.HTTP_201_CREATED)
async def criar_lista(
    dados: ListaCriacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> ListaLeitura:
    """Cria uma lista personalizada inicialmente vazia."""

    return await ListasService(session).criar(dados, usuario)


@lists_router.get("/listas/{lista_id}", response_model=ListaDetalhe)
async def obter_lista(
    lista_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> ListaDetalhe:
    """Obtém uma lista da conta e seus filmes do catálogo."""

    return await ListasService(session).obter(lista_id, usuario)


@lists_router.patch("/listas/{lista_id}", response_model=ListaLeitura)
async def atualizar_lista(
    lista_id: Annotated[str, Path(min_length=1, max_length=32)],
    dados: ListaAtualizacao,
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> ListaLeitura:
    """Altera nome e/ou visibilidade de uma lista da própria conta."""

    return await ListasService(session).atualizar(lista_id, dados, usuario)


@lists_router.delete("/listas/{lista_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_lista(
    lista_id: Annotated[str, Path(min_length=1, max_length=32)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Remove uma lista personalizada sem remover filmes do catálogo."""

    await ListasService(session).remover(lista_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@lists_router.post("/listas/{lista_id}/filmes/{filme_id}", response_model=ListaDetalhe)
async def adicionar_filme_a_lista(
    lista_id: Annotated[str, Path(min_length=1, max_length=32)],
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> ListaDetalhe:
    """Adiciona uma única referência de filme à lista selecionada."""

    return await ListasService(session).adicionar_filme(lista_id, filme_id, usuario)


@lists_router.delete("/listas/{lista_id}/filmes/{filme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_filme_da_lista(
    lista_id: Annotated[str, Path(min_length=1, max_length=32)],
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Remove um filme de uma lista personalizada da conta atual."""

    await ListasService(session).remover_filme(lista_id, filme_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@lists_router.get("/assistir-depois", response_model=list[FilmeResumo])
async def listar_assistir_depois(
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> list[FilmeResumo]:
    """Retorna a lista especial de filmes que a conta quer assistir depois."""

    return await ListasService(session).listar_assistir_depois(usuario)


@lists_router.put("/assistir-depois/{filme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def adicionar_assistir_depois(
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Marca um filme do catálogo para assistir depois."""

    await ListasService(session).adicionar_assistir_depois(filme_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@lists_router.delete("/assistir-depois/{filme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_assistir_depois(
    filme_id: Annotated[str, Path(min_length=1, max_length=50)],
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Desmarca um filme da lista especial da conta atual."""

    await ListasService(session).remover_assistir_depois(filme_id, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@lists_router.get("/filmes-avaliados", response_model=list[FilmeResumo])
async def listar_filmes_avaliados(
    session: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[User, Depends(get_current_user)],
) -> list[FilmeResumo]:
    """Calcula a lista virtual, única e ordenada de filmes avaliados pela conta."""

    return await ListasService(session).listar_filmes_avaliados(usuario)
