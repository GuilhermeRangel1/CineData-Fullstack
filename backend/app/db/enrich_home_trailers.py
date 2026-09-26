"""Preenche trailers para as fileiras principais da home quando o TMDB está configurado."""

import argparse
import asyncio

from sqlalchemy import func, select

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.movies.models import DimGenre, DimMovie, FactMoviePerformance
from app.movies.services import CatalogoFilmesService

HOME_GENRES = ("Animation", "Adventure")


async def enriquecer_home(meta_por_genero: int, limite_candidatos: int) -> None:
    if not get_settings().tmdb_api_token:
        return

    async with AsyncSessionLocal() as session:
        service = CatalogoFilmesService(session)
        for genero in HOME_GENRES:
            existentes = await session.scalar(
                select(func.count())
                .select_from(DimMovie)
                .join(DimMovie.genres)
                .where(DimGenre.nome_genero == genero, DimMovie.url_trailer.is_not(None))
            )
            faltam = max(meta_por_genero - (existentes or 0), 0)
            if not faltam:
                continue

            candidatos = await session.scalars(
                select(DimMovie)
                .join(DimMovie.genres)
                .outerjoin(DimMovie.performance)
                .where(DimGenre.nome_genero == genero, DimMovie.url_trailer.is_(None))
                .order_by(
                    FactMoviePerformance.popularidade.desc().nullslast(),
                    DimMovie.ano_lancamento.desc().nullslast(),
                )
                .limit(limite_candidatos)
            )
            for filme in candidatos:
                if faltam == 0:
                    break
                trailer = await service.obter_trailer(filme.id_filme)
                if trailer.url_trailer:
                    faltam -= 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta-por-genero", type=int, default=12)
    parser.add_argument("--limite-candidatos", type=int, default=80)
    args = parser.parse_args()
    try:
        asyncio.run(enriquecer_home(args.meta_por_genero, args.limite_candidatos))
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
