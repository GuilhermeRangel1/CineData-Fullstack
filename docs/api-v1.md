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

## Rotas disponíveis

| Método | Rota | Finalidade | Resposta |
| --- | --- | --- | --- |
| `POST` | `/api/v1/filmes` | Cadastra filme | `201 Created` |
| `GET` | `/api/v1/filmes` | Lista o catálogo paginado | `200 OK` |
| `GET` | `/api/v1/filmes/{filme_id}` | Consulta detalhes do filme | `200 OK` |

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

## Próximas rotas

Estas rotas serão implementadas nos próximos fluxos da atividade:

| Método | Rota | Finalidade | Sucesso |
| --- | --- | --- | --- |
| `PATCH` | `/api/v1/filmes/{filme_id}` | Atualizar filme | `200 OK` |
| `DELETE` | `/api/v1/filmes/{filme_id}` | Remover filme | `204 No Content` |
| `GET` | `/api/v1/filmes/{filme_id}/avaliacoes` | Consultar avaliações | `200 OK` |
| `POST` | `/api/v1/filmes/{filme_id}/avaliacoes` | Adicionar avaliação | `201 Created` |

## Erros

| Situação | Status |
| --- | --- |
| Dados inválidos, como `pagina=0` | `422 Unprocessable Entity` |
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
