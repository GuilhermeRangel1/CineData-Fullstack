"""Erros controlados que podem ser convertidos em respostas públicas da API."""


class ErroDominio(Exception):
    """Erro de negócio com status e mensagem seguros para o cliente."""

    status_code = 500
    codigo = "ERRO_INTERNO"
    mensagem = "Não foi possível concluir a operação."


class FilmeNaoEncontradoError(ErroDominio):
    """Filme solicitado não existe no catálogo."""

    status_code = 404
    codigo = "FILME_NAO_ENCONTRADO"
    mensagem = "Filme não encontrado."


class FilmeConflitoError(ErroDominio):
    """Escrita de filme conflita com uma restrição de integridade."""

    status_code = 409
    codigo = "CONFLITO_DE_DADOS"
    mensagem = "Não foi possível concluir a operação devido a um conflito de dados."


class FilmePersistenceError(ErroDominio):
    """Falha inesperada de persistência durante uma escrita de filme."""

    status_code = 500
    codigo = "FALHA_DE_PERSISTENCIA"
    mensagem = "Não foi possível concluir a operação no momento."
