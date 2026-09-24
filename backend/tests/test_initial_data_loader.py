from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select

from app.core.config import get_settings
from app.db.base import Base
from app.db.seed import InitialDataError, seed_database

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
TEST_TEMPORARY_DIRECTORY = BACKEND_DIRECTORY.parent / "tmp" / "initial-data-loader-tests"


@pytest.fixture
def isolated_path() -> Path:
    path = TEST_TEMPORARY_DIRECTORY / uuid4().hex
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path)


def _write_csvs(data_directory: Path, *, invalid_genre_reference: bool = False) -> None:
    dimensions = data_directory / "dimensions"
    facts = data_directory / "facts"
    dimensions.mkdir(parents=True)
    facts.mkdir()

    files = {
        dimensions / "dim_companies.csv": "nome_produtora,sk_company_id\nEstúdio Exemplo,c1\n",
        dimensions / "dim_genres.csv": "nome_genero,sk_genre_id\nDrama,g1\n",
        dimensions / "dim_movies.csv": (
            "sk_movie_id,id_filme,titulo,data_lancamento,ano_lancamento,duracao_minutos,"
            "status_filme,sinopse,url_poster,url_backdrop\n"
            "m1,100,Filme Exemplo,2024-01-15,2024,120,Lançado,Sinopse,,\n"
        ),
        dimensions
        / "dim_people.csv": "nome_pessoa,tipo_pessoa,sk_person_id\nAna Exemplo,Diretor,p1\n",
        dimensions / "dim_reviews.csv": (
            "sk_review_id,sk_movie_id,qtd_avaliacoes_usuarios,nota_media_usuarios\nrs1,m1,1,8.5\n"
        ),
        facts / "fact_movies_performance.csv": (
            "sk_movie_id,orcamento_usd,receita_usd,lucro_usd,orcamento_brl,receita_brl,"
            "lucro_brl,popularidade,nota_tmdb,qtd_tmdb,nota_imdb,qtd_imdb\n"
            "m1,10,30,20,50,150,100,9.5,8.2,25,7.8,30\n"
        ),
        facts / "movies_reviews.csv": (
            "sk_movie_review_id,sk_movie_id,nome,nota,comentario\nmr1,m1,João,8.5,Ótimo filme\n"
        ),
        facts / "bridge_movie_company.csv": "sk_movie_id,sk_company_id\nm1,c1\n",
        facts / "bridge_movie_genre.csv": (
            f"sk_movie_id,sk_genre_id\nm1,{'g-inexistente' if invalid_genre_reference else 'g1'}\n"
        ),
        facts / "bridge_movie_person.csv": "sk_movie_id,sk_person_id\nm1,p1\n",
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8", newline="")


@pytest.fixture
def migrated_database(isolated_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    database_path = isolated_path / "integration.db"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    command.upgrade(Config(str(BACKEND_DIRECTORY / "alembic.ini")), "head")
    yield database_url
    get_settings.cache_clear()


def _table_counts(database_url: str) -> dict[str, int]:
    engine = create_engine(database_url.replace("+aiosqlite", ""))
    try:
        with engine.connect() as connection:
            return {
                table.name: connection.scalar(select(func.count()).select_from(table))
                for table in Base.metadata.sorted_tables
            }
    finally:
        engine.dispose()


def test_loader_is_idempotent_after_alembic_migration(
    isolated_path: Path, migrated_database: str
) -> None:
    data_directory = isolated_path / "raw"
    _write_csvs(data_directory)

    first_summary = seed_database(migrated_database, data_directory, batch_size=1)
    first_counts = _table_counts(migrated_database)
    second_summary = seed_database(migrated_database, data_directory, batch_size=1)

    assert first_summary.processed == second_summary.processed
    assert first_summary.total == 10
    assert _table_counts(migrated_database) == first_counts
    assert set(first_counts.values()) == {1}


def test_loader_rolls_back_when_a_foreign_key_is_invalid(
    isolated_path: Path, migrated_database: str
) -> None:
    data_directory = isolated_path / "raw"
    _write_csvs(data_directory, invalid_genre_reference=True)

    with pytest.raises(InitialDataError, match="chave inexistente"):
        seed_database(migrated_database, data_directory, batch_size=1)

    assert set(_table_counts(migrated_database).values()) == {0}


def test_loader_rejects_an_invalid_header(isolated_path: Path, migrated_database: str) -> None:
    data_directory = isolated_path / "raw"
    _write_csvs(data_directory)
    (data_directory / "dimensions" / "dim_genres.csv").write_text(
        "id,nome\ng1,Drama\n", encoding="utf-8", newline=""
    )

    with pytest.raises(InitialDataError, match="cabeçalho inválido"):
        seed_database(migrated_database, data_directory)

    assert set(_table_counts(migrated_database).values()) == {0}
