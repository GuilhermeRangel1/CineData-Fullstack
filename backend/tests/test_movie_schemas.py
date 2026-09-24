import pytest
from pydantic import ValidationError

from app.movies.schemas import AvaliacaoCriacao, ConsultaCatalogo, FilmeCriacao


def test_movie_creation_contract_accepts_required_fields() -> None:
    filme = FilmeCriacao(
        titulo="A Viagem de Chihiro",
        diretor="Hayao Miyazaki",
        ano_lancamento=2001,
        generos=["Animação", "Fantasia"],
        sinopse="Uma jovem atravessa um mundo fantástico.",
    )

    assert filme.titulo == "A Viagem de Chihiro"
    assert filme.generos == ["Animação", "Fantasia"]


def test_review_contract_accepts_rating_on_zero_to_ten_scale() -> None:
    avaliacao = AvaliacaoCriacao(nome="Ana", nota=10, comentario="Ótimo filme.")

    assert avaliacao.nota == 10


def test_review_contract_rejects_rating_outside_zero_to_ten_scale() -> None:
    with pytest.raises(ValidationError):
        AvaliacaoCriacao(nome="Ana", nota=10.1, comentario="Ótimo filme.")


def test_catalog_query_contract_defines_stable_default_order() -> None:
    consulta = ConsultaCatalogo()

    assert consulta.ordenar_por == "titulo"
    assert consulta.direcao == "asc"
