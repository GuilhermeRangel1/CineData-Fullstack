"""Motor leve e explicável de recomendações por similaridade de conteúdo."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.movies.models import DimMovie, MovieReview
from app.taste_map.schemas import ArestaMapaGostos, MapaGostos, NoMapaGostos
from app.users.models import User


class MapaGostosService:
    """Monta um subgrafo pequeno a partir dos filmes avaliados pelo usuário.

    Não há treino nem dado externo escondido: cada sugestão vem de gêneros,
    pessoas e proximidade de ano já presentes no catálogo. Isso torna o
    resultado fácil de explicar e mantém o custo previsível para a atividade.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def obter(
        self,
        usuario: User,
        *,
        limite_nos: int,
        vizinhos_por_filme: int,
        busca: str | None = None,
    ) -> MapaGostos:
        avaliacoes = await self._avaliacoes_do_usuario(usuario.id)
        avaliadas = self._avaliadas_distintas(avaliacoes)
        total_avaliados = len(avaliadas)
        if not avaliadas:
            return MapaGostos(
                nos=[],
                arestas=[],
                total_avaliados=0,
                limite_nos=limite_nos,
                vizinhos_por_filme=vizinhos_por_filme,
            )

        # Prioriza o que a pessoa mais gostou e ainda deixa espaço para descobrir.
        max_avaliadas = max(1, limite_nos // 2)
        avaliadas = avaliadas[:max_avaliadas]
        candidatos = await self._catalogo_candidato(
            {avaliacao.sk_movie_id for avaliacao in avaliacoes}
        )
        recomendacoes, arestas = self._construir_conexoes(
            avaliadas,
            candidatos,
            limite_recomendacoes=max(0, limite_nos - len(avaliadas)),
            vizinhos_por_filme=vizinhos_por_filme,
        )
        nos = [self._no_avaliado(avaliacao) for avaliacao in avaliadas]
        nos.extend(self._no_recomendado(filme, afinidade) for filme, afinidade in recomendacoes)

        if busca and busca.strip():
            nos, arestas = self._filtrar_busca(nos, arestas, busca)

        return MapaGostos(
            nos=nos,
            arestas=arestas,
            total_avaliados=total_avaliados,
            limite_nos=limite_nos,
            vizinhos_por_filme=vizinhos_por_filme,
        )

    async def _avaliacoes_do_usuario(self, user_id: str) -> list[MovieReview]:
        resultado = await self._session.execute(
            select(MovieReview)
            .where(MovieReview.user_id == user_id)
            .options(
                selectinload(MovieReview.movie).selectinload(DimMovie.genres),
                selectinload(MovieReview.movie).selectinload(DimMovie.people),
            )
            .order_by(MovieReview.nota.desc(), MovieReview.created_at.desc())
        )
        return list(resultado.scalars())

    async def _catalogo_candidato(self, ids_avaliados: set[str]) -> list[DimMovie]:
        resultado = await self._session.execute(
            select(DimMovie)
            .where(DimMovie.sk_movie_id.not_in(ids_avaliados))
            .options(selectinload(DimMovie.genres), selectinload(DimMovie.people))
            .order_by(DimMovie.titulo)
            .limit(500)
        )
        return list(resultado.scalars().unique())

    @staticmethod
    def _avaliadas_distintas(avaliacoes: Iterable[MovieReview]) -> list[MovieReview]:
        vistas: set[str] = set()
        distintas: list[MovieReview] = []
        for avaliacao in avaliacoes:
            if avaliacao.sk_movie_id in vistas:
                continue
            vistas.add(avaliacao.sk_movie_id)
            distintas.append(avaliacao)
        return distintas

    def _construir_conexoes(
        self,
        avaliadas: list[MovieReview],
        candidatos: list[DimMovie],
        *,
        limite_recomendacoes: int,
        vizinhos_por_filme: int,
    ) -> tuple[list[tuple[DimMovie, float]], list[ArestaMapaGostos]]:
        if not limite_recomendacoes:
            return [], []
        melhores: dict[str, tuple[DimMovie, float]] = {}
        arestas_por_par: dict[tuple[str, str], ArestaMapaGostos] = {}

        for avaliacao in avaliadas:
            filme_origem = avaliacao.movie
            if filme_origem is None:
                continue
            proximos = sorted(
                (
                    (candidato, self._afinidade(filme_origem, candidato, avaliacao.nota))
                    for candidato in candidatos
                ),
                key=lambda item: (-item[1], item[0].titulo.casefold()),
            )
            for candidato, afinidade in proximos[:vizinhos_por_filme]:
                # A época sozinha é insuficiente para sugerir uma história;
                # é apenas um desempate quando já existe afinidade de conteúdo.
                if afinidade < 0.18:
                    continue
                atual = melhores.get(candidato.sk_movie_id)
                if atual is None or afinidade > atual[1]:
                    melhores[candidato.sk_movie_id] = (candidato, afinidade)
                arestas_por_par[(filme_origem.id_filme, candidato.id_filme)] = ArestaMapaGostos(
                    origem=filme_origem.id_filme,
                    destino=candidato.id_filme,
                    peso=round(afinidade, 3),
                    explicacao=self._explicacao(filme_origem, candidato),
                )

        recomendacoes = sorted(
            melhores.values(), key=lambda item: (-item[1], item[0].titulo.casefold())
        )[:limite_recomendacoes]
        ids_recomendados = {filme.id_filme for filme, _ in recomendacoes}
        arestas = [
            aresta
            for aresta in arestas_por_par.values()
            if aresta.destino in ids_recomendados
        ]
        return recomendacoes, sorted(arestas, key=lambda aresta: (-aresta.peso, aresta.origem))

    @staticmethod
    def _afinidade(origem: DimMovie, candidato: DimMovie, nota: float) -> float:
        generos_origem = {genero.nome_genero.casefold() for genero in origem.genres}
        generos_candidato = {genero.nome_genero.casefold() for genero in candidato.genres}
        diretores_origem = {
            pessoa.nome_pessoa.casefold()
            for pessoa in origem.people
            if pessoa.tipo_pessoa == "Diretor"
        }
        diretores_candidato = {
            pessoa.nome_pessoa.casefold()
            for pessoa in candidato.people
            if pessoa.tipo_pessoa == "Diretor"
        }
        elenco_origem = {
            pessoa.nome_pessoa.casefold()
            for pessoa in origem.people
            if pessoa.tipo_pessoa != "Diretor"
        }
        elenco_candidato = {
            pessoa.nome_pessoa.casefold()
            for pessoa in candidato.people
            if pessoa.tipo_pessoa != "Diretor"
        }
        generos = len(generos_origem & generos_candidato) / max(
            1, len(generos_origem | generos_candidato)
        )
        direcao = 1.0 if diretores_origem & diretores_candidato else 0.0
        elenco = min(1.0, len(elenco_origem & elenco_candidato) / 2)
        anos = 0.0
        if origem.ano_lancamento and candidato.ano_lancamento:
            anos = max(0.0, 1 - abs(origem.ano_lancamento - candidato.ano_lancamento) / 30)
        sinal_da_avaliacao = 0.45 + max(0, min(nota, 10)) / 20
        afinidade = 0.55 * generos + 0.25 * direcao + 0.12 * elenco + 0.08 * anos
        return round(afinidade * sinal_da_avaliacao, 3)

    @staticmethod
    def _explicacao(origem: DimMovie, candidato: DimMovie) -> str:
        generos = sorted(
            {genero.nome_genero for genero in origem.genres}
            & {genero.nome_genero for genero in candidato.genres}
        )
        diretores = sorted(
            {
                pessoa.nome_pessoa
                for pessoa in origem.people
                if pessoa.tipo_pessoa == "Diretor"
            }
            & {
                pessoa.nome_pessoa
                for pessoa in candidato.people
                if pessoa.tipo_pessoa == "Diretor"
            }
        )
        pessoas = sorted(
            {pessoa.nome_pessoa for pessoa in origem.people}
            & {pessoa.nome_pessoa for pessoa in candidato.people}
        )
        partes: list[str] = []
        if generos:
            partes.append(f"gênero {generos[0]}")
        if diretores:
            partes.append(f"direção de {diretores[0]}")
        elif pessoas:
            partes.append(f"presença de {pessoas[0]}")
        return "Conexão por " + " e ".join(partes) if partes else "Proximidade de época e estilo"

    @staticmethod
    def _generos(filme: DimMovie) -> list[str]:
        return [genero.nome_genero for genero in filme.genres]

    def _no_avaliado(self, avaliacao: MovieReview) -> NoMapaGostos:
        filme = avaliacao.movie
        assert filme is not None
        generos = self._generos(filme)
        return NoMapaGostos(
            id=filme.id_filme,
            titulo=filme.titulo,
            ano_lancamento=filme.ano_lancamento,
            url_poster=filme.url_poster,
            genero_principal=generos[0] if generos else None,
            generos=generos,
            nota_usuario=avaliacao.nota,
            tipo="avaliado",
        )

    def _no_recomendado(self, filme: DimMovie, afinidade: float) -> NoMapaGostos:
        generos = self._generos(filme)
        return NoMapaGostos(
            id=filme.id_filme,
            titulo=filme.titulo,
            ano_lancamento=filme.ano_lancamento,
            url_poster=filme.url_poster,
            genero_principal=generos[0] if generos else None,
            generos=generos,
            tipo="recomendado",
            afinidade=round(afinidade, 3),
        )

    @staticmethod
    def _filtrar_busca(
        nos: list[NoMapaGostos], arestas: list[ArestaMapaGostos], busca: str
    ) -> tuple[list[NoMapaGostos], list[ArestaMapaGostos]]:
        termo = busca.casefold().strip()
        encontrados = {no.id for no in nos if termo in no.titulo.casefold()}
        if not encontrados:
            return [], []
        adjacentes = {
            ponta
            for aresta in arestas
            for ponta in (aresta.origem, aresta.destino)
            if aresta.origem in encontrados or aresta.destino in encontrados
        }
        ids = encontrados | adjacentes
        return [no for no in nos if no.id in ids], [
            aresta for aresta in arestas if aresta.origem in ids and aresta.destino in ids
        ]
