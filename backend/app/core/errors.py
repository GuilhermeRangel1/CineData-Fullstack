"""Erros controlados que podem ser convertidos em respostas públicas da API."""


class ErroDominio(Exception):
    """Erro de negócio com status e mensagem seguros para o cliente."""

    status_code = 500
    codigo = "ERRO_INTERNO"
    mensagem = "Não foi possível concluir a operação."
    headers: dict[str, str] | None = None


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


class UsuarioJaExisteError(ErroDominio):
    """O e-mail informado já pertence a uma conta."""

    status_code = 409
    codigo = "USUARIO_JA_EXISTE"
    mensagem = "Já existe uma conta com este e-mail."


class CredenciaisInvalidasError(ErroDominio):
    """O login não pode revelar qual credencial está incorreta."""

    status_code = 401
    codigo = "CREDENCIAIS_INVALIDAS"
    mensagem = "E-mail ou senha inválidos."


class ConfiguracaoAutenticacaoError(ErroDominio):
    """A aplicação não recebeu a chave necessária para assinar tokens."""

    status_code = 503
    codigo = "AUTENTICACAO_INDISPONIVEL"
    mensagem = "A autenticação não está disponível no momento."


class TokenInvalidoError(ErroDominio):
    """O token Bearer está ausente, expirado ou não é confiável."""

    status_code = 401
    codigo = "TOKEN_INVALIDO"
    mensagem = "É necessário iniciar uma sessão válida para esta operação."
    headers = {"WWW-Authenticate": "Bearer"}


class PermissaoNegadaError(ErroDominio):
    """A conta autenticada não possui o papel exigido pela operação."""

    status_code = 403
    codigo = "PERMISSAO_NEGADA"
    mensagem = "Sua conta não possui permissão para esta operação."
