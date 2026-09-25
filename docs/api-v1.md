# Convenção da API

Este documento registra como o frontend conversa com o backend. Ele existe para
que ambos usem as mesmas rotas, parâmetros e formatos de resposta.

## Prefixo `/api/v1`

O projeto-base já define `/api/v1` como prefixo das rotas de negócio. O `v1`
significa apenas a primeira versão da API; não acrescenta nenhuma funcionalidade
à atividade. Todas as rotas abaixo seguem esse prefixo.

## Regras gerais

- As rotas usam JSON e nomes de campos em português.
- O ID público de um filme é `id`; chaves internas, como `sk_movie_id`, não são
  expostas.
- Notas e médias usam a escala de 0 a 10.
- Coleções usam paginação e ordenação estável.
- Erros não expõem SQL, exceções ou caminhos locais.
- Rotas autenticadas recebem `Authorization: Bearer <jwt>`.

## Rotas disponíveis

| Método | Rota | Finalidade | Acesso | Resposta |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/auth/cadastro` | Cria uma conta local | Público | `201 Created` |
| `POST` | `/api/v1/auth/login` | Inicia sessão local | Público | `200 OK` |
| `POST` | `/api/v1/filmes` | Cadastra filme | `admin` | `201 Created` |
| `GET` | `/api/v1/filmes` | Lista o catálogo paginado | Público | `200 OK` |
| `GET` | `/api/v1/filmes/{filme_id}` | Consulta detalhes do filme | Público | `200 OK` |
| `PATCH` | `/api/v1/filmes/{filme_id}` | Atualiza parcialmente um filme | `admin` | `200 OK` |
| `DELETE` | `/api/v1/filmes/{filme_id}` | Remove um filme | `admin` | `204 No Content` |
| `GET` | `/api/v1/filmes/{filme_id}/avaliacoes` | Consulta o histórico de avaliações | Público | `200 OK` |
| `POST` | `/api/v1/filmes/{filme_id}/avaliacoes` | Adiciona uma avaliação | Autenticado | `201 Created` |

### Contas e sessão

`POST /api/v1/auth/cadastro` recebe `nome`, `email` e `senha`; a conta sempre
nasce com o papel `user`. `POST /api/v1/auth/login` recebe `email` e `senha` e
devolve o JWT Bearer e os dados públicos da conta. O único `admin` inicial é
criado pelo comando de bootstrap da infraestrutura, nunca pelo cadastro público.

### Catálogo

`GET /api/v1/filmes` aceita parâmetros combináveis:

| Parâmetro | Padrão | Regra |
| --- | --- | --- |
| `busca` | - | Busca no título, sem diferenciar maiúsculas e minúsculas. |
| `genero` | - | Filtra pelo nome do gênero. |
| `pagina` | `1` | Mínimo `1`. |
| `tamanho_pagina` | `12` | Entre `1` e `100`. |
| `ordenar_por` | `titulo` | Aceita `titulo` ou `ano_lancamento`. |
| `direcao` | `asc` | Aceita `asc` ou `desc`. |

Em empates, a API ordena por título e ID. Isso evita que itens mudem de página
entre duas consultas iguais.

Exemplo:

```text
GET /api/v1/filmes?busca=vida&genero=Drama&pagina=2&tamanho_pagina=12&ordenar_por=ano_lancamento&direcao=desc
```

Resposta paginada:

```json
{
  "itens": [],
  "meta": {
    "pagina": 1,
    "tamanho_pagina": 12,
    "total_itens": 0,
    "total_paginas": 0
  }
}
```

### Avaliações

`POST /api/v1/filmes/{filme_id}/avaliacoes` recebe `nota` e `comentario` e
exige uma sessão válida. O autor é derivado da conta autenticada, e a nova
avaliação é vinculada a ela. A nota é um número entre `0` e `10`, inclusive.
A inclusão cria o item no histórico e atualiza a quantidade e a média do filme
na mesma transação. Para preservar o consolidado importado pelos CSVs, a nova
média é ponderada pela quantidade já registrada no resumo do filme.

`GET /api/v1/filmes/{filme_id}/avaliacoes` retorna o histórico disponível, da
avaliação mais recente para a mais antiga. Ambas as rotas retornam `404` quando
o filme não existe.

## Erros

| Situação | Status |
| --- | --- |
| Dados inválidos, como `pagina=0` | `422 Unprocessable Entity` |
| Token ausente ou inválido | `401 Unauthorized` |
| Conta sem o papel exigido | `403 Forbidden` |
| Filme inexistente | `404 Not Found` |
| Conflito de estado | `409 Conflict` |
| Falha inesperada | `500 Internal Server Error` |

Quando houver erro controlado, a resposta usa este formato:

```json
{
  "codigo": "REQUISICAO_INVALIDA",
  "mensagem": "Dados da requisição são inválidos."
}
```

Erros de domínio seguem o mesmo formato. Por exemplo, uma consulta a um filme
inexistente retorna `404` com `FILME_NAO_ENCONTRADO`.
