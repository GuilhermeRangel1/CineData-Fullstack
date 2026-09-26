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

| Método | Rota | Finalidade | Acesso |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/cadastro` | Cria conta de usuário | Público |
| `POST` | `/api/v1/auth/login` | Inicia sessão e devolve JWT | Público |
| `GET`, `PATCH` | `/api/v1/auth/perfil` | Consulta ou edita o próprio perfil | Autenticado |
| `GET` | `/api/v1/perfis/{usuario_id}` | Consulta perfil público | Público |
| `GET` | `/api/v1/filmes` | Catálogo, busca, filtros e paginação | Público |
| `GET` | `/api/v1/filmes/{filme_id}` | Detalhes de filme | Público |
| `POST`, `PATCH`, `DELETE` | `/api/v1/filmes[/{filme_id}]` | Gestão do catálogo | `admin` |
| `GET` | `/api/v1/filmes/{filme_id}/avaliacoes` | Histórico público de avaliações | Público |
| `GET`, `POST`, `DELETE` | `/api/v1/filmes/{filme_id}/minha-avaliacao` ou `/avaliacoes` | Consulta, cria/edita ou apaga a própria avaliação | Autenticado |
| `GET` | `/api/v1/filmes/{filme_id}/trailer` | Consulta trailer disponível | Público |
| `GET` | `/api/v1/minha-conta/listas...` | Lista personalizada e filmes avaliados | Autenticado |
| `GET`, `PUT`, `DELETE` | `/api/v1/minha-conta/assistir-depois...` | Lista especial “assistir depois” | Autenticado |
| `GET`, `POST`, `PATCH`, `DELETE` | `/api/v1/minha-conta/amigos...` | Pesquisa, pedidos e amizades | Autenticado |
| `GET`, `POST`, `PATCH`, `DELETE` | `/api/v1/comunidades...` | Comunidades, participação e publicações | Público/autenticado/`admin` conforme operação |
| `GET` | `/api/v1/admin/analytics/resumo` | Indicadores agregados da plataforma | `admin` |
| `GET` | `/api/v1/admin/fontes/tmdb...` | Busca e consulta de dados TMDB | `admin` |
| `GET` | `/api/v1/mapa-de-gostos` | Subgrafo pessoal de recomendações | Autenticado |

As rotas exatas de cada grupo estão nos routers do backend e também na
documentação OpenAPI em `/docs` durante a execução local. A sessão de teste do
Compose (`POST /api/v1/auth/sessao-teste`) só existe no ambiente Docker e fica
oculta da OpenAPI.

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
| `pessoa` | - | Filtra por pessoa associada ao filme. |
| `produtora` | - | Filtra por produtora. |
| `ano_inicial`, `ano_final` | - | Limites inclusivos do ano de lançamento. |
| `duracao_minima`, `duracao_maxima` | - | Limites inclusivos em minutos. |
| `nota_minima` | - | Nota externa mínima disponível. |
| `pagina` | `1` | Mínimo `1`. |
| `tamanho_pagina` | `12` | Entre `1` e `100`. |
| `ordenar_por` | `titulo` | Aceita `titulo` ou `ano_lancamento`. |
| `direcao` | `asc` | Aceita `asc` ou `desc`. |
| `priorizar_capa`, `priorizar_trailer`, `somente_com_trailer` | `false` | Ordena por mídia disponível ou restringe a filmes com trailer. |

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

`POST /api/v1/filmes/{filme_id}/avaliacoes` recebe `nota`, `comentario` e, se
desejado, `visibilidade`; exige uma sessão válida. A nota aceita qualquer valor
numérico entre `0` e `10`, inclusive. A conta pode ter no máximo uma avaliação
por filme: a primeira gravação retorna `201 Created`; novas chamadas atualizam
a mesma avaliação e retornam `200 OK`. O banco aplica uma restrição única para
proteger também envios simultâneos. A operação atualiza quantidade e média do
filme; avaliações importadas sem conta permanecem separadas.

`GET /api/v1/filmes/{filme_id}/avaliacoes` retorna o histórico disponível, da
avaliação mais recente para a mais antiga. Ambas as rotas retornam `404` quando
o filme não existe.

`GET /api/v1/filmes/{filme_id}/minha-avaliacao` retorna a avaliação privada ou
pública da conta autenticada. `DELETE` no mesmo caminho apaga somente a
avaliação da conta e recompõe o resumo do filme.

### Listas, comunidades e descoberta

As rotas sob `/api/v1/minha-conta/listas` e `/assistir-depois` só expõem dados da
conta autenticada. O perfil público contém apenas avaliações e listas públicas;
`GET /api/v1/auth/perfil` permite ao dono ver também os próprios itens privados.

As operações de comunidade que alteram a conversa exigem participação; a
criação, edição e remoção de comunidades exige `admin`. O painel em
`/api/v1/admin/analytics/resumo?periodo_dias=30` agrega atividade e rankings, com
um intervalo configurável de 1 a 90 dias. O mapa aceita `limite_nos` (6 a 48),
`vizinhos_por_filme` (1 a 6), `busca` e parâmetros repetidos `excluir` para
renovar sugestões sem repetir os nós recomendados da rodada anterior.

`/api/v1/admin/fontes/tmdb` é protegido por papel `admin`; o token TMDB é lido
somente pelo backend e nunca faz parte da resposta ao navegador.

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
