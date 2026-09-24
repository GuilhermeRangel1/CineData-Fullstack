"""Casos de uso do domínio de filmes."""

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas import MetadadosPagina, Pagina
from app.movies.models import DimGenre, DimMovie
from app.movies.schemas import ConsultaCatalogo, FilmeResumo, GeneroResumo


class CatalogoFilmesService:
    """Consulta o catálogo sem expor detalhes do ORM à camada HTTP."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listar(self, consulta: ConsultaCatalogo) -> Pagina[FilmeResumo]:
        """Retorna um catálogo filtrado, ordenado e paginado de forma estável."""

        statement = select(DimMovie).options(
            selectinload(DimMovie.genres),
            selectinload(DimMovie.reviews_summary),
        )

        if consulta.busca:
            termo = self._escapar_like(consulta.busca.casefold())
            statement = statement.where(func.lower(DimMovie.titulo).like(f"%{termo}%", escape="\\"))

        if consulta.genero:
            statement = statement.join(DimMovie.genres).where(
                func.lower(DimGenre.nome_genero) == consulta.genero.casefold()
            )

        statement = statement.distinct()
        total = await self._session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        total_itens = total or 0

        campo_ordenacao = getattr(DimMovie, consulta.ordenar_por)
        ordem_primaria = (
            campo_ordenacao.asc() if consulta.direcao == "asc" else campo_ordenacao.desc()
        )
        offset = (consulta.pagina - 1) * consulta.tamanho_pagina
        result = await self._session.scalars(
            statement.order_by(ordem_primaria, DimMovie.titulo.asc(), DimMovie.id_filme.asc())
            .offset(offset)
            .limit(consulta.tamanho_pagina)
        )
        filmes = list(result.unique())

        return Pagina(
            itens=[self._para_resumo(filme) for filme in filmes],
            meta=MetadadosPagina(
                pagina=consulta.pagina,
                tamanho_pagina=consulta.tamanho_pagina,
                total_itens=total_itens,
                total_paginas=ceil(total_itens / consulta.tamanho_pagina),
            ),
        )

    @staticmethod
    def _escapar_like(valor: str) -> str:
        return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @staticmethod
    def _para_resumo(filme: DimMovie) -> FilmeResumo:
        resumo = filme.reviews_summary
        return FilmeResumo(
            id=filme.id_filme,
            titulo=filme.titulo,
            ano_lancamento=filme.ano_lancamento,
            url_poster=filme.url_poster,
            generos=[
                GeneroResumo(id=genero.sk_genre_id, nome=genero.nome_genero)
                for genero in filme.genres
            ],
            nota_media=resumo.nota_media_usuarios if resumo else None,
            quantidade_avaliacoes=resumo.qtd_avaliacoes_usuarios if resumo else 0,
        )
