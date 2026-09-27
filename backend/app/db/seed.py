"""Seed/importação dos CSVs iniciais para um banco já preparado pelo Alembic.

O módulo não cria tabelas. Antes de usá-lo, aplique as migrações com
``alembic upgrade head``. A carga é transacional e pode ser repetida: as chaves
substitutas versionadas nos CSVs são usadas como conflito dos upserts.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from math import isfinite
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, Engine, create_engine, event, inspect, select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.sql.schema import Table

from app.db.base import Base
from app.movies import models  # noqa: F401  Registra as tabelas no metadata.

DEFAULT_BATCH_SIZE = 10_000
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIRECTORY = REPOSITORY_ROOT / "data" / "raw"


class InitialDataError(ValueError):
    """Erro de validação que impede a importação completa dos CSVs."""


@dataclass
class LoadSummary:
    """Quantidade de linhas processadas por arquivo de origem."""

    processed: dict[str, int] = field(default_factory=dict)
    skipped: bool = False

    def add(self, file_name: str, count: int) -> None:
        self.processed[file_name] = count

    @property
    def total(self) -> int:
        return sum(self.processed.values())


RowTransformer = Callable[[dict[str, str | None], int, str], dict[str, Any]]


def _location(file_name: str, row_number: int, column: str) -> str:
    return f"{file_name}, linha {row_number}, coluna '{column}'"


def _value(row: dict[str, str | None], file_name: str, row_number: int, column: str) -> str | None:
    value = row[column]
    if value is None:
        return None
    value = value.strip()
    return value or None


def _required_text(
    row: dict[str, str | None], file_name: str, row_number: int, column: str, max_length: int
) -> str:
    value = _value(row, file_name, row_number, column)
    if value is None:
        raise InitialDataError(f"{_location(file_name, row_number, column)} é obrigatório.")
    if len(value) > max_length:
        raise InitialDataError(
            f"{_location(file_name, row_number, column)} excede {max_length} caracteres."
        )
    return value


def _optional_text(
    row: dict[str, str | None], file_name: str, row_number: int, column: str, max_length: int
) -> str | None:
    value = _value(row, file_name, row_number, column)
    if value is not None and len(value) > max_length:
        raise InitialDataError(
            f"{_location(file_name, row_number, column)} excede {max_length} caracteres."
        )
    return value


def _optional_date(
    row: dict[str, str | None], file_name: str, row_number: int, column: str
) -> date | None:
    value = _value(row, file_name, row_number, column)
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise InitialDataError(
            f"{_location(file_name, row_number, column)} deve estar no formato AAAA-MM-DD."
        ) from error


def _optional_decimal(
    row: dict[str, str | None], file_name: str, row_number: int, column: str
) -> Decimal | None:
    value = _value(row, file_name, row_number, column)
    if value is None:
        return None
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise InitialDataError(
            f"{_location(file_name, row_number, column)} deve ser numérico."
        ) from error
    if not result.is_finite():
        raise InitialDataError(f"{_location(file_name, row_number, column)} deve ser finito.")
    return result


def _optional_int(
    row: dict[str, str | None], file_name: str, row_number: int, column: str
) -> int | None:
    value = _optional_decimal(row, file_name, row_number, column)
    if value is None:
        return None
    if value != value.to_integral_value():
        raise InitialDataError(f"{_location(file_name, row_number, column)} deve ser inteiro.")
    return int(value)


def _required_int(row: dict[str, str | None], file_name: str, row_number: int, column: str) -> int:
    value = _optional_int(row, file_name, row_number, column)
    if value is None:
        raise InitialDataError(f"{_location(file_name, row_number, column)} é obrigatório.")
    return value


def _optional_float(
    row: dict[str, str | None], file_name: str, row_number: int, column: str
) -> float | None:
    value = _optional_decimal(row, file_name, row_number, column)
    if value is None:
        return None
    result = float(value)
    if not isfinite(result):
        raise InitialDataError(f"{_location(file_name, row_number, column)} deve ser finito.")
    return result


def _required_float(
    row: dict[str, str | None], file_name: str, row_number: int, column: str
) -> float:
    value = _optional_float(row, file_name, row_number, column)
    if value is None:
        raise InitialDataError(f"{_location(file_name, row_number, column)} é obrigatório.")
    return value


def _read_csv(
    path: Path, expected_headers: Sequence[str]
) -> Iterator[tuple[int, dict[str, str | None]]]:
    if not path.is_file():
        raise InitialDataError(f"Arquivo obrigatório não encontrado: {path.name}.")

    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = reader.fieldnames
        if headers != list(expected_headers):
            found = ", ".join(headers or []) or "sem cabeçalho"
            expected = ", ".join(expected_headers)
            raise InitialDataError(
                f"{path.name} possui cabeçalho inválido. Esperado: {expected}. Encontrado: {found}."
            )
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise InitialDataError(
                    f"{path.name}, linha {row_number}, possui mais colunas que o cabeçalho."
                )
            yield row_number, row


def _assert_migrations_applied(engine: Engine) -> None:
    expected_tables = set(Base.metadata.tables)
    actual_tables = set(inspect(engine).get_table_names())
    missing = sorted(expected_tables - actual_tables)
    if missing or "alembic_version" not in actual_tables:
        missing_description = ", ".join(missing) if missing else "alembic_version"
        raise InitialDataError(
            "O banco não está preparado pelas migrações do Alembic "
            f"(tabelas ausentes: {missing_description}). "
            "Execute 'alembic upgrade head' antes da carga."
        )


def _existing_keys(connection: Connection, table: Table, column: str) -> set[str]:
    return set(connection.scalars(select(table.c[column])))


def _configure_seed_engine(engine: Engine) -> None:
    """Use SQLite settings suited to one large, atomic initial import."""

    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _set_seed_pragmas(dbapi_connection: Any, connection_record: object) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = -65536")
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.close()

    # WAL keeps the database consistent if the import is interrupted and avoids
    # repeatedly syncing the rollback journal during this single transaction.
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode = WAL")
        connection.commit()


def _load_rows(
    connection: Connection,
    *,
    path: Path,
    table: Table,
    headers: Sequence[str],
    transformer: RowTransformer,
    conflict_columns: Sequence[str],
    update_columns: Sequence[str] = (),
    foreign_keys: Sequence[tuple[str, set[str]]] = (),
    unique_values: Callable[[dict[str, Any]], Iterable[str | tuple[str, ...]]] | None = None,
    track_conflicts: bool = True,
    batch_size: int,
) -> int:
    statement = sqlite_insert(table)
    if update_columns:
        statement = statement.on_conflict_do_update(
            index_elements=list(conflict_columns),
            set_={column: getattr(statement.excluded, column) for column in update_columns},
        )
    else:
        statement = statement.on_conflict_do_nothing(index_elements=list(conflict_columns))

    count = 0
    next_progress = 100_000
    last_reported = 0
    batch: list[dict[str, Any]] = []
    seen_conflicts: set[tuple[Any, ...]] = set()
    seen_unique: set[str | tuple[str, ...]] = set()
    for row_number, row in _read_csv(path, headers):
        item = transformer(row, row_number, path.name)
        conflict_value = tuple(item[column] for column in conflict_columns)
        if track_conflicts:
            if conflict_value in seen_conflicts:
                raise InitialDataError(
                    f"{path.name}, linha {row_number}, repete a chave primária {conflict_value}."
                )
            seen_conflicts.add(conflict_value)
        if unique_values is not None:
            for value in unique_values(item):
                if value in seen_unique:
                    raise InitialDataError(
                        f"{path.name}, linha {row_number}, "
                        f"repete uma chave única de negócio: {value}."
                    )
                seen_unique.add(value)
        for column, valid_keys in foreign_keys:
            if item[column] not in valid_keys:
                raise InitialDataError(
                    f"{_location(path.name, row_number, column)} referencia uma chave inexistente: "
                    f"{item[column]}."
                )
        batch.append(item)
        if len(batch) == batch_size:
            connection.execute(statement, batch)
            count += len(batch)
            batch.clear()
            if count >= next_progress:
                print(f"{path.name}: {count:,} registros importados...", flush=True)
                last_reported = count
                next_progress = (count // 100_000 + 1) * 100_000
    if batch:
        connection.execute(statement, batch)
        count += len(batch)
    if count != last_reported:
        print(f"{path.name}: {count:,} registros importados.", flush=True)
    return count


def _company(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
    return {
        "sk_company_id": _required_text(row, file_name, row_number, "sk_company_id", 64),
        "nome_produtora": _required_text(row, file_name, row_number, "nome_produtora", 255),
    }


def _genre(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
    return {
        "sk_genre_id": _required_text(row, file_name, row_number, "sk_genre_id", 64),
        "nome_genero": _required_text(row, file_name, row_number, "nome_genero", 50),
    }


def _movie(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
    duration = _optional_int(row, file_name, row_number, "duracao_minutos")
    return {
        "sk_movie_id": _required_text(row, file_name, row_number, "sk_movie_id", 64),
        "id_filme": _required_text(row, file_name, row_number, "id_filme", 50),
        "titulo": _required_text(row, file_name, row_number, "titulo", 500),
        "data_lancamento": _optional_date(row, file_name, row_number, "data_lancamento"),
        "ano_lancamento": _optional_int(row, file_name, row_number, "ano_lancamento"),
        # Zero and negative durations mean “unknown” in source catalogs; keeping
        # them as NULL avoids presenting impossible runtimes to people.
        "duracao_minutos": duration if duration is not None and duration > 0 else None,
        "status_filme": _optional_text(row, file_name, row_number, "status_filme", 50),
        "sinopse": _optional_text(row, file_name, row_number, "sinopse", 4000),
        "url_poster": _optional_text(row, file_name, row_number, "url_poster", 2048),
        "url_backdrop": _optional_text(row, file_name, row_number, "url_backdrop", 2048),
    }


def _person(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
    person_type = _required_text(row, file_name, row_number, "tipo_pessoa", 20)
    if person_type not in models.PERSON_TYPES:
        raise InitialDataError(
            f"{_location(file_name, row_number, 'tipo_pessoa')} deve ser um de: "
            f"{', '.join(models.PERSON_TYPES)}."
        )
    return {
        "sk_person_id": _required_text(row, file_name, row_number, "sk_person_id", 64),
        "nome_pessoa": _required_text(row, file_name, row_number, "nome_pessoa", 255),
        "tipo_pessoa": person_type,
    }


def _performance(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
    orcamento_usd = _optional_decimal(row, file_name, row_number, "orcamento_usd")
    receita_usd = _optional_decimal(row, file_name, row_number, "receita_usd")
    orcamento_brl = _optional_decimal(row, file_name, row_number, "orcamento_brl")
    receita_brl = _optional_decimal(row, file_name, row_number, "receita_brl")
    popularidade = _optional_float(row, file_name, row_number, "popularidade")
    nota_tmdb = _optional_float(row, file_name, row_number, "nota_tmdb")
    qtd_tmdb = _optional_int(row, file_name, row_number, "qtd_tmdb")
    nota_imdb = _optional_float(row, file_name, row_number, "nota_imdb")
    qtd_imdb = _optional_int(row, file_name, row_number, "qtd_imdb")

    for column, value in (
        ("orcamento_usd", orcamento_usd),
        ("receita_usd", receita_usd),
        ("orcamento_brl", orcamento_brl),
        ("receita_brl", receita_brl),
    ):
        if value is not None and value < 0:
            raise InitialDataError(
                f"{_location(file_name, row_number, column)} não pode ser negativo."
            )
    if popularidade is not None and popularidade < 0:
        raise InitialDataError(
            f"{_location(file_name, row_number, 'popularidade')} não pode ser negativa."
        )
    for column, score in (("nota_tmdb", nota_tmdb), ("nota_imdb", nota_imdb)):
        if score is not None and not 0 <= score <= 10:
            raise InitialDataError(
                f"{_location(file_name, row_number, column)} deve estar entre 0 e 10."
            )
    for column, votes in (("qtd_tmdb", qtd_tmdb), ("qtd_imdb", qtd_imdb)):
        if votes is not None and votes < 0:
            raise InitialDataError(
                f"{_location(file_name, row_number, column)} não pode ser negativo."
            )

    # Sem votos, a nota não representa uma avaliação confiável; NULL evita
    # exibir uma nota como se houvesse avaliações registradas.
    if qtd_tmdb == 0:
        nota_tmdb = None
    if qtd_imdb == 0:
        nota_imdb = None

    return {
        "sk_movie_id": _required_text(row, file_name, row_number, "sk_movie_id", 64),
        "orcamento_usd": orcamento_usd,
        "receita_usd": receita_usd,
        "lucro_usd": _required_decimal(row, file_name, row_number, "lucro_usd"),
        "orcamento_brl": orcamento_brl,
        "receita_brl": receita_brl,
        "lucro_brl": _required_decimal(row, file_name, row_number, "lucro_brl"),
        "popularidade": popularidade,
        "nota_tmdb": nota_tmdb,
        "qtd_tmdb": qtd_tmdb,
        "nota_imdb": nota_imdb,
        "qtd_imdb": qtd_imdb,
    }


def _required_decimal(
    row: dict[str, str | None], file_name: str, row_number: int, column: str
) -> Decimal:
    value = _optional_decimal(row, file_name, row_number, column)
    if value is None:
        raise InitialDataError(f"{_location(file_name, row_number, column)} é obrigatório.")
    return value


def _review_summary(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
    score = _optional_float(row, file_name, row_number, "nota_media_usuarios")
    if score is not None and not 0 <= score <= 10:
        raise InitialDataError(
            f"{_location(file_name, row_number, 'nota_media_usuarios')} deve estar entre 0 e 10."
        )
    count = _required_int(row, file_name, row_number, "qtd_avaliacoes_usuarios")
    if count < 0:
        raise InitialDataError(
            f"{_location(file_name, row_number, 'qtd_avaliacoes_usuarios')} não pode ser negativo."
        )
    return {
        "sk_review_id": _required_text(row, file_name, row_number, "sk_review_id", 64),
        "sk_movie_id": _required_text(row, file_name, row_number, "sk_movie_id", 64),
        "qtd_avaliacoes_usuarios": count,
        "nota_media_usuarios": score,
    }


def _movie_review(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
    score = _required_float(row, file_name, row_number, "nota")
    if not 0 <= score <= 10:
        raise InitialDataError(
            f"{_location(file_name, row_number, 'nota')} deve estar entre 0 e 10."
        )
    return {
        "sk_movie_review_id": _required_text(row, file_name, row_number, "sk_movie_review_id", 64),
        "sk_movie_id": _required_text(row, file_name, row_number, "sk_movie_id", 64),
        "nome": _required_text(row, file_name, row_number, "nome", 120),
        "nota": score,
        "comentario": _required_text(row, file_name, row_number, "comentario", 4000),
    }


def _bridge(
    right_column: str,
) -> RowTransformer:
    def transform(row: dict[str, str | None], row_number: int, file_name: str) -> dict[str, Any]:
        return {
            "sk_movie_id": _required_text(row, file_name, row_number, "sk_movie_id", 64),
            right_column: _required_text(row, file_name, row_number, right_column, 64),
        }

    return transform


def _synchronous_url(database_url: str) -> str:
    """Converte a URL async usada pela aplicação para a conexão síncrona da CLI."""

    return database_url.replace("+aiosqlite", "")


def seed_database(
    database_url: str,
    data_directory: Path = DEFAULT_DATA_DIRECTORY,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    skip_if_populated: bool = False,
) -> LoadSummary:
    """Carrega todos os CSVs em uma transação e devolve seu resumo."""

    if batch_size < 1:
        raise ValueError("batch_size deve ser maior que zero.")
    if not data_directory.is_dir():
        raise InitialDataError(f"Diretório de dados não encontrado: {data_directory}.")

    engine = create_engine(_synchronous_url(database_url))
    try:
        _configure_seed_engine(engine)
        _assert_migrations_applied(engine)
        tables = Base.metadata.tables
        if skip_if_populated:
            with engine.connect() as connection:
                has_movies = connection.scalar(text("SELECT EXISTS (SELECT 1 FROM dim_movies)"))
            if has_movies:
                return LoadSummary(skipped=True)

        summary = LoadSummary()
        with engine.begin() as connection:
            company_table = tables["dim_companies"]
            summary.add(
                "dim_companies.csv",
                _load_rows(
                    connection,
                    path=data_directory / "dimensions" / "dim_companies.csv",
                    table=company_table,
                    headers=("nome_produtora", "sk_company_id"),
                    transformer=_company,
                    conflict_columns=("sk_company_id",),
                    update_columns=("nome_produtora",),
                    unique_values=lambda item: (item["nome_produtora"],),
                    batch_size=batch_size,
                ),
            )
            genre_table = tables["dim_genres"]
            summary.add(
                "dim_genres.csv",
                _load_rows(
                    connection,
                    path=data_directory / "dimensions" / "dim_genres.csv",
                    table=genre_table,
                    headers=("nome_genero", "sk_genre_id"),
                    transformer=_genre,
                    conflict_columns=("sk_genre_id",),
                    update_columns=("nome_genero",),
                    unique_values=lambda item: (item["nome_genero"],),
                    batch_size=batch_size,
                ),
            )
            movie_table = tables["dim_movies"]
            summary.add(
                "dim_movies.csv",
                _load_rows(
                    connection,
                    path=data_directory / "dimensions" / "dim_movies.csv",
                    table=movie_table,
                    headers=(
                        "sk_movie_id",
                        "id_filme",
                        "titulo",
                        "data_lancamento",
                        "ano_lancamento",
                        "duracao_minutos",
                        "status_filme",
                        "sinopse",
                        "url_poster",
                        "url_backdrop",
                    ),
                    transformer=_movie,
                    conflict_columns=("sk_movie_id",),
                    update_columns=(
                        "id_filme",
                        "titulo",
                        "data_lancamento",
                        "ano_lancamento",
                        "duracao_minutos",
                        "status_filme",
                        "sinopse",
                        "url_poster",
                        "url_backdrop",
                    ),
                    unique_values=lambda item: (item["id_filme"],),
                    batch_size=batch_size,
                ),
            )
            person_table = tables["dim_people"]
            summary.add(
                "dim_people.csv",
                _load_rows(
                    connection,
                    path=data_directory / "dimensions" / "dim_people.csv",
                    table=person_table,
                    headers=("nome_pessoa", "tipo_pessoa", "sk_person_id"),
                    transformer=_person,
                    conflict_columns=("sk_person_id",),
                    update_columns=("nome_pessoa", "tipo_pessoa"),
                    unique_values=lambda item: ((item["nome_pessoa"], item["tipo_pessoa"]),),
                    batch_size=batch_size,
                ),
            )

            movie_keys = _existing_keys(connection, movie_table, "sk_movie_id")
            company_keys = _existing_keys(connection, company_table, "sk_company_id")
            genre_keys = _existing_keys(connection, genre_table, "sk_genre_id")
            person_keys = _existing_keys(connection, person_table, "sk_person_id")

            performance_table = tables["fact_movies_performance"]
            summary.add(
                "fact_movies_performance.csv",
                _load_rows(
                    connection,
                    path=data_directory / "facts" / "fact_movies_performance.csv",
                    table=performance_table,
                    headers=(
                        "sk_movie_id",
                        "orcamento_usd",
                        "receita_usd",
                        "lucro_usd",
                        "orcamento_brl",
                        "receita_brl",
                        "lucro_brl",
                        "popularidade",
                        "nota_tmdb",
                        "qtd_tmdb",
                        "nota_imdb",
                        "qtd_imdb",
                    ),
                    transformer=_performance,
                    conflict_columns=("sk_movie_id",),
                    update_columns=(
                        "orcamento_usd",
                        "receita_usd",
                        "lucro_usd",
                        "orcamento_brl",
                        "receita_brl",
                        "lucro_brl",
                        "popularidade",
                        "nota_tmdb",
                        "qtd_tmdb",
                        "nota_imdb",
                        "qtd_imdb",
                    ),
                    foreign_keys=(("sk_movie_id", movie_keys),),
                    batch_size=batch_size,
                ),
            )
            review_summary_table = tables["dim_reviews"]
            summary.add(
                "dim_reviews.csv",
                _load_rows(
                    connection,
                    path=data_directory / "dimensions" / "dim_reviews.csv",
                    table=review_summary_table,
                    headers=(
                        "sk_review_id",
                        "sk_movie_id",
                        "qtd_avaliacoes_usuarios",
                        "nota_media_usuarios",
                    ),
                    transformer=_review_summary,
                    conflict_columns=("sk_review_id",),
                    update_columns=(
                        "sk_movie_id",
                        "qtd_avaliacoes_usuarios",
                        "nota_media_usuarios",
                    ),
                    foreign_keys=(("sk_movie_id", movie_keys),),
                    unique_values=lambda item: (item["sk_movie_id"],),
                    batch_size=batch_size,
                ),
            )
            movie_review_table = tables["movie_reviews"]
            summary.add(
                "movies_reviews.csv",
                _load_rows(
                    connection,
                    path=data_directory / "facts" / "movies_reviews.csv",
                    table=movie_review_table,
                    headers=("sk_movie_review_id", "sk_movie_id", "nome", "nota", "comentario"),
                    transformer=_movie_review,
                    conflict_columns=("sk_movie_review_id",),
                    update_columns=("sk_movie_id", "nome", "nota", "comentario"),
                    foreign_keys=(("sk_movie_id", movie_keys),),
                    batch_size=batch_size,
                ),
            )

            for file_name, table_name, right_column, right_keys in (
                ("bridge_movie_company.csv", "bridge_movie_company", "sk_company_id", company_keys),
                ("bridge_movie_genre.csv", "bridge_movie_genre", "sk_genre_id", genre_keys),
                ("bridge_movie_person.csv", "bridge_movie_person", "sk_person_id", person_keys),
            ):
                summary.add(
                    file_name,
                    _load_rows(
                        connection,
                        path=data_directory / "facts" / file_name,
                        table=tables[table_name],
                        headers=("sk_movie_id", right_column),
                        transformer=_bridge(right_column),
                        conflict_columns=("sk_movie_id", right_column),
                        foreign_keys=(("sk_movie_id", movie_keys), (right_column, right_keys)),
                        # Bridge conflicts are intentionally ignored by SQLite;
                        # retaining every pair in Python duplicates the much
                        # more memory-efficient composite primary-key index.
                        track_conflicts=False,
                        batch_size=batch_size,
                    ),
                )
        return summary
    finally:
        engine.dispose()


def _parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importa os CSVs iniciais do CineData.")
    parser.add_argument(
        "--database-url",
        required=True,
        help="URL do banco já migrado, por exemplo sqlite+aiosqlite:///./rocketlab.db.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIRECTORY,
        help="Diretório que contém dimensions/ e facts/.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Quantidade de registros por lote (padrão: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--skip-if-populated",
        action="store_true",
        help="Pula a carga quando dim_movies já contém dados.",
    )
    return parser.parse_args(arguments)


def main(arguments: Sequence[str] | None = None) -> int:
    """Executa a CLI e retorna um código apropriado para automação."""

    args = _parse_arguments(arguments)
    try:
        summary = seed_database(
            args.database_url,
            args.data_dir,
            batch_size=args.batch_size,
            skip_if_populated=args.skip_if_populated,
        )
    except (InitialDataError, ValueError) as error:
        print(f"Carga não realizada: {error}", file=sys.stderr)
        return 1

    if summary.skipped:
        print("Carga ignorada: o catálogo já contém filmes.")
        return 0

    print("Carga concluída com sucesso:")
    for file_name, count in summary.processed.items():
        print(f"- {file_name}: {count} registros processados")
    print(f"Total: {summary.total} registros processados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
