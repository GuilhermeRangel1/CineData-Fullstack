"""Casos de uso do domínio de filmes."""

import logging
from math import ceil
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas import MetadadosPagina, Pagina
from app.core.errors import FilmeConflitoError, FilmeNaoEncontradoError, FilmePersistenceError
from app.movies.models import (
    DimCompany,
    DimGenre,
    DimMovie,
    DimPerson,
    PersonType,
)
from app.movies.schemas import (
    AvaliacaoLeitura,
    ConsultaCatalogo,
    DesempenhoFilme,
    FilmeAtualizacao,
    FilmeCriacao,
    FilmeDetalhe,
    FilmeResumo,
    GeneroResumo,
    PessoaResumo,
    ProdutoraResumo,
)

logger = logging.getLogger(__name__)
DETALHE_LOAD_OPTIONS = (
    selectinload(DimMovie.genres),
    selectinload(DimMovie.people),
    selectinload(DimMovie.companies),
    selectinload(DimMovie.performance),
    selectinload(DimMovie.reviews_summary),
    selectinload(DimMovie.reviews),
)


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

    async def obter_detalhe(self, filme_id: str) -> FilmeDetalhe:
        """Retorna um filme completo, carregando relações sem consultas N+1."""

        filme = await self._session.scalar(
            select(DimMovie).where(DimMovie.id_filme == filme_id).options(*DETALHE_LOAD_OPTIONS)
        )
        if filme is None:
            raise FilmeNaoEncontradoError
        return GestaoFilmesService._para_detalhe(filme)

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


class GestaoFilmesService:
    """Coordena escritas atômicas do catálogo de filmes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def criar(self, dados: FilmeCriacao) -> FilmeDetalhe:
        """Cria um filme e reutiliza dimensões já cadastradas quando possível."""

        try:
            generos = await self._obter_ou_criar_generos(dados.generos)
            diretor = await self._obter_ou_criar_pessoa(dados.diretor, "Diretor")
            atores = await self._obter_ou_criar_pessoas(dados.atores, "Ator")
            roteiristas = await self._obter_ou_criar_pessoas(dados.roteiristas, "Roteirista")
            produtoras = await self._obter_ou_criar_produtoras(dados.produtoras)

            filme = DimMovie(
                id_filme=f"local-{uuid4().hex}",
                titulo=dados.titulo,
                data_lancamento=dados.data_lancamento,
                ano_lancamento=dados.ano_lancamento,
                duracao_minutos=dados.duracao_minutos,
                status_filme=dados.status_filme,
                sinopse=dados.sinopse,
                url_poster=dados.url_poster,
                url_backdrop=dados.url_backdrop,
                genres=generos,
                people=[diretor, *atores, *roteiristas],
                companies=produtoras,
            )
            self._session.add(filme)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            logger.warning("Cadastro de filme interrompido por conflito de integridade.")
            raise FilmeConflitoError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Cadastro de filme interrompido por falha de persistência.")
            raise FilmePersistenceError from error

        return await CatalogoFilmesService(self._session).obter_detalhe(filme.id_filme)

    async def atualizar(self, filme_id: str, dados: FilmeAtualizacao) -> FilmeDetalhe:
        """Atualiza somente os campos enviados, incluindo relações quando necessário."""

        filme = await self._obter_filme_para_escrita(filme_id)
        try:
            for campo in (
                "titulo",
                "ano_lancamento",
                "sinopse",
                "data_lancamento",
                "duracao_minutos",
                "status_filme",
                "url_poster",
                "url_backdrop",
            ):
                if campo in dados.model_fields_set:
                    setattr(filme, campo, getattr(dados, campo))

            if "generos" in dados.model_fields_set:
                filme.genres = await self._obter_ou_criar_generos(dados.generos or [])
            if "diretor" in dados.model_fields_set:
                diretor = await self._obter_ou_criar_pessoa(dados.diretor or "", "Diretor")
                self._substituir_pessoas_por_papel(filme, "Diretor", [diretor])
            if "atores" in dados.model_fields_set:
                atores = await self._obter_ou_criar_pessoas(dados.atores or [], "Ator")
                self._substituir_pessoas_por_papel(filme, "Ator", atores)
            if "roteiristas" in dados.model_fields_set:
                roteiristas = await self._obter_ou_criar_pessoas(
                    dados.roteiristas or [], "Roteirista"
                )
                self._substituir_pessoas_por_papel(filme, "Roteirista", roteiristas)
            if "produtoras" in dados.model_fields_set:
                filme.companies = await self._obter_ou_criar_produtoras(dados.produtoras or [])

            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            logger.warning("Atualização de filme interrompida por conflito de integridade.")
            raise FilmeConflitoError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Atualização de filme interrompida por falha de persistência.")
            raise FilmePersistenceError from error

        return await CatalogoFilmesService(self._session).obter_detalhe(filme.id_filme)

    async def remover(self, filme_id: str) -> None:
        """Remove um filme e seus relacionamentos dependentes de forma atômica."""

        filme = await self._obter_filme_para_escrita(filme_id)
        try:
            await self._session.delete(filme)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            logger.warning("Remoção de filme interrompida por conflito de integridade.")
            raise FilmeConflitoError from error
        except SQLAlchemyError as error:
            await self._session.rollback()
            logger.error("Remoção de filme interrompida por falha de persistência.")
            raise FilmePersistenceError from error

    async def _obter_filme_para_escrita(self, filme_id: str) -> DimMovie:
        filme = await self._session.scalar(
            select(DimMovie).where(DimMovie.id_filme == filme_id).options(*DETALHE_LOAD_OPTIONS)
        )
        if filme is None:
            raise FilmeNaoEncontradoError
        return filme

    @staticmethod
    def _substituir_pessoas_por_papel(
        filme: DimMovie, papel: PersonType, pessoas: list[DimPerson]
    ) -> None:
        filme.people = [pessoa for pessoa in filme.people if pessoa.tipo_pessoa != papel] + pessoas

    async def _obter_ou_criar_generos(self, nomes: list[str]) -> list[DimGenre]:
        generos: list[DimGenre] = []
        for nome in nomes:
            genero = await self._session.scalar(
                select(DimGenre).where(func.lower(DimGenre.nome_genero) == nome.lower())
            )
            generos.append(genero or DimGenre(nome_genero=nome))
        return sorted(generos, key=lambda genero: genero.nome_genero.casefold())

    async def _obter_ou_criar_pessoa(self, nome: str, papel: PersonType) -> DimPerson:
        pessoa = await self._session.scalar(
            select(DimPerson).where(
                func.lower(DimPerson.nome_pessoa) == nome.lower(),
                DimPerson.tipo_pessoa == papel,
            )
        )
        return pessoa or DimPerson(nome_pessoa=nome, tipo_pessoa=papel)

    async def _obter_ou_criar_pessoas(self, nomes: list[str], papel: PersonType) -> list[DimPerson]:
        pessoas = [await self._obter_ou_criar_pessoa(nome, papel) for nome in nomes]
        return sorted(pessoas, key=lambda pessoa: pessoa.nome_pessoa.casefold())

    async def _obter_ou_criar_produtoras(self, nomes: list[str]) -> list[DimCompany]:
        produtoras: list[DimCompany] = []
        for nome in nomes:
            produtora = await self._session.scalar(
                select(DimCompany).where(func.lower(DimCompany.nome_produtora) == nome.lower())
            )
            produtoras.append(produtora or DimCompany(nome_produtora=nome))
        return sorted(produtoras, key=lambda produtora: produtora.nome_produtora.casefold())

    @staticmethod
    def _para_detalhe(filme: DimMovie) -> FilmeDetalhe:
        resumo = filme.reviews_summary
        desempenho = filme.performance
        return FilmeDetalhe(
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
            data_lancamento=filme.data_lancamento,
            duracao_minutos=filme.duracao_minutos,
            status_filme=filme.status_filme,
            sinopse=filme.sinopse,
            url_backdrop=filme.url_backdrop,
            pessoas=[
                PessoaResumo(
                    id=pessoa.sk_person_id, nome=pessoa.nome_pessoa, papel=pessoa.tipo_pessoa
                )
                for pessoa in sorted(
                    filme.people,
                    key=lambda pessoa: (pessoa.tipo_pessoa, pessoa.nome_pessoa.casefold()),
                )
            ],
            produtoras=[
                ProdutoraResumo(id=produtora.sk_company_id, nome=produtora.nome_produtora)
                for produtora in filme.companies
            ],
            desempenho=(
                DesempenhoFilme(
                    orcamento_usd=float(desempenho.orcamento_usd)
                    if desempenho.orcamento_usd is not None
                    else None,
                    receita_usd=float(desempenho.receita_usd)
                    if desempenho.receita_usd is not None
                    else None,
                    lucro_usd=float(desempenho.lucro_usd),
                    orcamento_brl=float(desempenho.orcamento_brl)
                    if desempenho.orcamento_brl is not None
                    else None,
                    receita_brl=float(desempenho.receita_brl)
                    if desempenho.receita_brl is not None
                    else None,
                    lucro_brl=float(desempenho.lucro_brl),
                    popularidade=desempenho.popularidade,
                    nota_tmdb=desempenho.nota_tmdb,
                    quantidade_tmdb=desempenho.qtd_tmdb,
                    nota_imdb=desempenho.nota_imdb,
                    quantidade_imdb=desempenho.qtd_imdb,
                )
                if desempenho
                else None
            ),
            avaliacoes=[
                AvaliacaoLeitura(
                    id=avaliacao.sk_movie_review_id,
                    nome=avaliacao.nome,
                    nota=avaliacao.nota,
                    comentario=avaliacao.comentario,
                    criada_em=avaliacao.created_at,
                )
                for avaliacao in filme.reviews
            ],
        )
