# CineData Analytics

Plataforma full-stack de descoberta, avaliação e conversa sobre filmes,
desenvolvida para a atividade DEV do Visagio Rocket Lab 2026.2. O CineData
combina um catálogo cinematográfico com recursos sociais e ferramentas de
análise para quem administra a plataforma.

O projeto é uma aplicação de demonstração executada localmente. Os dados são
armazenados em SQLite, os serviços podem ser iniciados juntos com Docker Compose
e a integração externa com o TMDB é opcional. O código não depende de uma conta
TMDB para as funções principais.

## O que a aplicação oferece

| Área | O que permite fazer |
| --- | --- |
| Início e catálogo | Descobrir filmes em cards com pôsteres, pesquisar, filtrar, ordenar e navegar por páginas. |
| Detalhes de filme | Consultar sinopse, elenco/equipe, produtoras, métricas, avaliações e trailers disponíveis. |
| Avaliações | Criar, editar ou apagar a própria nota e resenha; notas podem ser qualquer valor numérico entre 0 e 10. |
| Listas | Criar curadorias pessoais, escolher a lista diretamente no detalhe de um filme e acompanhar os filmes já avaliados. |
| Perfis e amizades | Editar o próprio nome e avatar, consultar perfis públicos e enviar ou responder a pedidos de amizade. |
| Comunidades | Participar de conversas sobre cinema, mencionar filmes, comentar publicações e reagir; admins podem moderar publicações e comentários individuais. |
| Mapa de gostos | Explorar recomendações conectadas aos filmes avaliados, com sinais de afinidade explicáveis. |
| Analytics | Acompanhar indicadores agregados e tendências calculados a partir da atividade registrada no banco. |
| Ferramentas administrativas | Manter o catálogo e as comunidades, importar dados de filmes do TMDB e consultar analytics. |

O tema visual é escuro, com identidade em vermelho e destaque editorial na home.
O Castelo Animado aparece como seleção editorial acompanhada por um trailer
oficial incorporado do YouTube. Esse destaque não finge ser um registro do
catálogo local: o filme não faz parte dos CSVs fornecidos.

## Experiência no frontend

O frontend é uma aplicação de página única (SPA) feita em React, TypeScript e
CSS. A navegação reúne as áreas funcionais do produto sem expor ações
administrativas para contas comuns.

### Catálogo, pesquisa e detalhes

- O catálogo consulta a API e apresenta os filmes em cards visuais com pôsteres.
  Quando a imagem principal não está disponível, usa o backdrop ou uma
  apresentação alternativa com o título.
- A busca local procura pelo título; filtros combináveis incluem gênero,
  pessoa, produtora, ano, duração mínima/máxima e nota externa mínima. Há também
  ordenação, paginação e opções para priorizar filmes com imagem ou trailer.
- Quando a busca não encontra um título local, a API pode consultar títulos
  equivalentes em português e inglês no TMDB e localizar o registro já
  existente no catálogo, sem criar uma cópia. Esse complemento depende do token
  TMDB; sem ele, a busca continua funcionando pelos títulos locais.
- A interface traduz os nomes dos gêneros para português sem alterar os dados
  originais do catálogo.
- A janela de detalhes reúne sinopse, equipe, produtoras, desempenho e histórico
  de avaliações. Se houver trailer cadastrado, oferece sua reprodução.
- Catálogo e detalhes usam cache em memória por até um minuto. Uma escrita
  invalida o cache para que as telas recarreguem os dados atualizados.
- Estados de carregamento, erro, lista vazia e nova tentativa são tratados na
  interface. Respostas antigas de pesquisas substituídas não devem sobrescrever
  a pesquisa mais recente.

### Avaliações e listas pessoais

- Uma conta pode manter uma avaliação por filme. A nota é digitada livremente
  em qualquer valor entre `0` e `10`, inclusive valores fracionários; não há
  seletor que force incrementos de meio ponto.
- A pessoa pode alterar a nota e o comentário ou apagar sua própria avaliação.
  A API diferencia criação e edição pelas respostas `201` e `200`.
- Listas personalizadas são opcionais: adicionar um filme não obriga a usar
  uma lista de “assistir depois”. No detalhe do filme, a pessoa escolhe a lista
  desejada.
- A área de listas exibe capas, permite editar nome e visibilidade, adicionar
  ou remover títulos e consultar uma coleção automática dos filmes avaliados.
- Listas privadas são visíveis à própria conta; perfis públicos mostram somente
  o conteúdo marcado como público.

### Perfis, amizades e comunidades

- O perfil próprio permite atualizar nome e foto e consultar a mesma visão
  social disponível para outros perfis, incluindo também listas e avaliações
  privadas da própria conta.
- Perfis públicos podem exibir avaliações recentes, listas públicas,
  comunidades e conexões, conforme a visibilidade e os dados existentes.
- A área de amizades permite pesquisar pessoas, enviar e responder solicitações,
  consultar pedidos recebidos/enviados e remover conexões. As prévias são
  limitadas para manter a página compacta, com acesso à lista completa.
- Comunidades têm imagem opcional, descrição, membros e conversa. Publicações
  podem mencionar filmes; pessoas participantes podem comentar e reagir.
- Administradores podem remover uma publicação ou comentário específico. O
  conteúdo é substituído por um aviso de moderação; remover uma publicação
  também remove a menção ao filme, as reações e o conteúdo dos comentários
  associados, preservando a posição da conversa.
- Enquanto uma conversa está aberta e visível, o frontend consulta atualizações
  periodicamente. A implementação atual usa polling, não WebSocket.

### Mapa de gostos e analytics

- O mapa de gostos é pessoal e requer login. Os filmes avaliados formam os
  pontos de origem; recomendações relacionadas aparecem conectadas e podem ser
  renovadas sem repetir as sugestões descartadas.
- A recomendação é um cálculo de similaridade de conteúdo, não um modelo de
  machine learning treinado. Considera gêneros, pessoas da equipe, termos da
  sinopse, época e métricas disponíveis no catálogo; as conexões carregam
  sinais de afinidade para explicar por que os itens se relacionam.
- Analytics é exclusivo para administradores. Os indicadores e gráficos vêm de
  consultas ao banco, com período configurável de 1 a 90 dias, incluindo
  atividade recente, gêneros avaliados, filmes mais avaliados e comunidades em
  alta. Não há um histórico artificial de atividade social: se a aplicação
  acabou de ser inicializada, parte desses gráficos terá poucos dados.

## Perfis de acesso

| Ação | Visitante | `user` | `admin` |
| --- | :---: | :---: | :---: |
| Consultar catálogo, detalhes, trailers e perfis públicos | ✓ | ✓ | ✓ |
| Criar conta e iniciar sessão | ✓ | ✓ | ✓ |
| Avaliar filmes, criar listas e participar socialmente | — | ✓ | ✓ |
| Editar o próprio perfil e ver seus dados privados | — | ✓ | ✓ |
| Criar, editar e remover filmes do catálogo | — | — | ✓ |
| Criar e administrar comunidades | — | — | ✓ |
| Consultar analytics e usar a importação administrativa do TMDB | — | — | ✓ |

O cadastro público sempre cria uma conta `user`. A promoção a `admin` é feita
por configuração e bootstrap; não existe opção de se tornar administrador pelo
formulário de cadastro.

## Arquitetura

```mermaid
flowchart LR
    U[Pessoa usuária] --> FE[Frontend React + TypeScript]
    FE -->|JSON /api/v1| API[API FastAPI]
    API --> S[Serviços de domínio]
    S --> DB[(SQLite)]
    MIG[Alembic] --> DB
    CSV[CSVs dimensions/ e facts/] --> SEED[Seed transacional]
    SEED --> DB
    API -->|somente admin| TMDB[API do TMDB]
    FE -->|iframe oficial| YT[YouTube]
```

### Tecnologias

| Camada | Tecnologias e responsabilidades |
| --- | --- |
| Interface | React 19, TypeScript, Vite e CSS; componentes por área do produto. |
| Cliente HTTP | `fetch`, tipos TypeScript para contratos, cache de leitura, sessão Bearer e invalidação após alterações. |
| API | Python 3.11+, FastAPI, Pydantic e Uvicorn; routers versionados sob `/api/v1`. |
| Domínio e persistência | SQLAlchemy assíncrono, SQLite com `aiosqlite`, serviços por domínio e relações explícitas. |
| Schema e carga | Alembic para migrações; comando de seed separado e transacional para os CSVs. |
| Integração externa | Cliente TMDB no backend; trailers de vídeo reproduzidos pelo iframe oficial do YouTube. |
| Testes e qualidade | pytest e Ruff no backend; Vitest, Testing Library e oxlint no frontend. |
| Execução local | Docker Compose com serviços de backend e frontend e volume nomeado para o banco. |

### Organização do repositório

```text
backend/
  app/
    analytics/       Agregações e schemas do painel administrativo
    api/v1/          Rotas HTTP versionadas
    communities/     Modelos, regras e schemas das comunidades
    core/            Configuração, logging e erros públicos
    db/              Sessão, importador CSV e tarefas de dados
    integrations/    Cliente para a API TMDB
    movies/          Catálogo, avaliações e modelos relacionais
    taste_map/       Cálculo do mapa de gostos e recomendações
    users/           Contas, segurança, perfis, listas e amizades
  migrations/        Histórico Alembic do schema
  tests/             Testes de API, domínio, segurança e carga
frontend/
  src/
    api/             Cliente HTTP e tipos de integração
    auth/            Persistência da sessão no navegador
    components/      Catálogo, formulários, listas e áreas sociais
    pages/           Telas principais
    hooks/           Carregamento de recursos e mutações
    lib/             Conversões e utilitários de interface
data/raw/
  dimensions/        CSVs de dimensões do catálogo
  facts/             CSVs de métricas, avaliações e relações
docs/
  api-v1.md          Contratos e regras da API
  frontend.md        Comportamentos detalhados da interface e mídia
TODO.md              Escopo, etapas e critérios de conclusão
docker-compose.yml   Execução local dos dois serviços
```

## Backend e API

O backend separa transporte HTTP, regras de domínio e acesso a dados. Os
routers recebem e validam requisições; serviços encapsulam operações como
avaliações, listas, amizades, comunidades, recomendações e agregações. Erros
controlados retornam um envelope seguro `codigo`/`mensagem`, sem expor SQL,
caminhos locais ou detalhes internos.

| Grupo de rotas | Principais recursos | Acesso típico |
| --- | --- | --- |
| `/api/v1/auth` | Cadastro, login, perfil próprio e sessão de demonstração no Compose | Público/autenticado; demonstração apenas no Compose |
| `/api/v1/filmes` | Catálogo, filtros, detalhes, trailers e avaliações | Consulta pública; escrita administrativa ou do dono da avaliação |
| `/api/v1/perfis` | Consulta de perfis públicos | Público |
| `/api/v1/minha-conta` | Listas, assistir-depois, amizades e solicitações | Autenticado |
| `/api/v1/comunidades` | Descoberta, participação, publicações, comentários e reações | Público/autenticado; gestão administrativa |
| `/api/v1/mapa-de-gostos` | Grafo pessoal de filmes e recomendações | Autenticado |
| `/api/v1/admin/analytics` | Indicadores agregados da plataforma | `admin` |
| `/api/v1/admin/fontes/tmdb` | Busca e importação assistida de dados de filmes | `admin` |

Consulte [docs/api-v1.md](docs/api-v1.md) para parâmetros, exemplos, respostas,
regras de acesso e códigos de erro. Durante a execução, a documentação
interativa fica em `http://localhost:8000/docs`; a rota de sessão de demonstração
é intencionalmente omitida da OpenAPI.

### Regras de integridade e segurança

- Senhas nunca são armazenadas em texto puro; o backend usa hash Argon2.
- O login devolve um JWT Bearer. O frontend guarda a sessão no armazenamento
  local do navegador e envia o token nas requisições autenticadas.
- A API verifica autenticação, propriedade dos recursos e papel administrativo
  no servidor; esconder um botão no frontend não substitui a autorização.
- Uma restrição única parcial no banco impede mais de uma avaliação por conta
  e filme, inclusive quando duas escritas chegam simultaneamente. Avaliações
  importadas, sem conta associada, não são limitadas por essa regra.
- Migrações Alembic são a única autoridade para criar e evoluir o schema. O
  importador não cria tabelas e falha se o banco ainda não estiver migrado.
- CORS permite somente as origens configuradas. A configuração padrão local é
  `http://localhost:5173`; o Compose também permite `http://localhost:8080`.
- O token do TMDB permanece no backend e não é retornado ao navegador.

## Dados e modelo relacional

O catálogo local parte de dez CSVs versionados em `data/raw/`. Eles representam
dimensões, métricas, avaliações e relações muitos-para-muitos. A carga inicial
do Compose processa aproximadamente 1,7 milhão de registros; entre eles estão
95.645 filmes e as relações com gêneros, pessoas e produtoras. O conjunto é
usado localmente e a carga pode ser repetida sem duplicar as chaves fornecidas.

### Inventário das tabelas

As tabelas do catálogo preservam o esquema relacional de origem dos dados. As
chaves `sk_*` são as chaves substitutas importadas dos CSVs; `id_filme` é o
identificador de negócio único exposto pela API.

| Tabela | Grão / chave principal | Conteúdo e relações |
| --- | --- | --- |
| `dim_movies` | Um registro por filme (`sk_movie_id`) | `id_filme` único, título, data e ano de lançamento, duração, status, sinopse, URL do pôster, backdrop e trailer. É a entidade central; possui relações com equipe, gêneros, produtoras, métricas e avaliações. |
| `dim_genres` | Um registro por gênero (`sk_genre_id`) | Nome de gênero único. Relaciona-se a filmes por `bridge_movie_genre`. |
| `dim_people` | Uma pessoa em um papel (`sk_person_id`) | Nome e papel (`Ator`, `Diretor` ou `Roteirista`); combinação nome/papel é única. Relaciona-se a filmes por `bridge_movie_person`. |
| `dim_companies` | Uma produtora (`sk_company_id`) | Nome de produtora/estúdio único. Relaciona-se a filmes por `bridge_movie_company`. |
| `fact_movies_performance` | No máximo uma linha por filme (`sk_movie_id`) | Orçamento, receita e lucro em USD/BRL, popularidade, notas e quantidades de votos de TMDB/IMDb. Métricas desconhecidas permanecem nulas quando aplicável. |
| `dim_reviews` | Um resumo por filme (`sk_review_id`; `sk_movie_id` único) | Quantidade e média agregada das avaliações importadas. Não contém a resenha individual da conta. |
| `movie_reviews` | Uma avaliação individual (`sk_movie_review_id`) | Filme, autor exibido, nota, comentário e data. `user_id` é nulo para avaliações importadas e aponta para `users` nas avaliações da aplicação; contém também a visibilidade. |
| `bridge_movie_genre` | Um par filme/gênero | Chave composta por filme e gênero; impede relações repetidas e permite consultas por gênero. |
| `bridge_movie_person` | Um par filme/pessoa | Chave composta por filme e pessoa; contém índice para busca por pessoa. |
| `bridge_movie_company` | Um par filme/produtora | Chave composta por filme e produtora. |
| `users` | Uma conta (`id`) | E-mail único, nome, hash de senha, papel (`user`/`admin`), avatar e timestamps. |
| `user_lists` | Uma lista pessoal (`id`) | Dono, nome, visibilidade (`publica`/`privada`) e timestamps. Cada lista pertence a uma conta. |
| `user_list_movies` | Um par lista/filme | Associação com chave composta e data de inclusão; um filme não se repete na mesma lista. |
| `watch_later_movies` | Um par conta/filme | Associação da funcionalidade especial “assistir depois”. É opcional na experiência e separada das listas personalizadas. |
| `friendship_requests` | Um pedido direcionado (`id`) | Solicitante, destinatário, estado (`pendente`, `aceita`, `bloqueada`) e timestamps; não permite autorrelacionamento nem repetir o mesmo par direcionado. |
| `communities` | Uma comunidade (`id`) | Nome único, descrição, URL de imagem opcional, contador de visualizações e timestamps. |
| `community_memberships` | Um par comunidade/conta | Associação de participação com chave composta e data de entrada. |
| `community_posts` | Uma publicação (`id`) | Comunidade, autor, conteúdo, timestamps, filme opcional mencionado e indicador de remoção por moderação. Se o filme for apagado, a publicação permanece sem a referência. |
| `community_comments` | Um comentário (`id`) | Publicação, autor, conteúdo, data e indicador de remoção por moderação. Comentários pertencem a uma publicação. |
| `community_reactions` | Um par publicação/conta | Uma reação por pessoa e publicação; tipos permitidos: `curtir`, `amei` e `interessante`. |

#### Relações e regras de integridade

- As três tabelas `bridge_*` resolvem relações muitos-para-muitos entre filmes,
  gêneros, pessoas e produtoras. Chaves compostas impedem duplicar o mesmo
  vínculo.
- `fact_movies_performance` e `dim_reviews` são relações um-para-um com o filme.
  Os valores da origem não são misturados com colunas próprias da interface.
- `movie_reviews` reúne registros importados e avaliações criadas na aplicação.
  A distinção é `user_id IS NULL` versus uma FK para `users`; apagar a conta
  deixa a avaliação sem vínculo, não apaga o histórico (`ON DELETE SET NULL`).
- Existe no máximo uma avaliação com conta por filme, garantido no banco por
  índice único parcial em `(user_id, sk_movie_id)` apenas quando `user_id` não
  é nulo. Isso mantém avaliações importadas sem usuário fora da restrição e
  protege também escritas simultâneas.
- Notas têm `CHECK` de `0` a `10`; papéis, visibilidades, tipos de pessoa,
  estados de amizade e reações também têm restrições de domínio no schema.
- Exclusões de entidades proprietárias usam `ON DELETE CASCADE` para limpar
  associações dependentes, com exceções explícitas como a referência opcional
  de filme em uma publicação (`SET NULL`).
- `alembic_version` é a tabela técnica do Alembic e registra a revisão aplicada.
  Analytics não cria tabelas próprias: as métricas são agregadas a partir das
  avaliações, contas, listas, comunidades e publicações existentes.
- `movie_synopsis_fts` é uma tabela virtual FTS5 do SQLite, não um modelo de
  negócio do ORM. Triggers a mantêm sincronizada com inserções, alterações de
  sinopse e exclusões em `dim_movies`.
- Publicações e comentários moderados permanecem como registros de contexto,
  mas o conteúdo é apagado e a API os marca com `removida_por_moderacao`. A
  mensagem original não é retornada. Moderar uma publicação também redige seus
  comentários, remove a menção a filme e apaga as reações associadas.

### Histórico de evolução do schema

As revisões formam uma cadeia linear; a inicialização aplica todas as
migrações pendentes com `alembic upgrade head`. As revisões 0013–0015 acrescentam
integridade de avaliações, desempenho do mapa e moderação de conteúdo.

| Revisão | Alteração persistente |
| --- | --- |
| `0001_initial_movie_schema` | Cria dimensões e relações do catálogo, métricas financeiras/externas, resumos e avaliações individuais importadas. Inclui chaves, FKs, unicidades e validação da escala de notas. |
| `0002_add_catalog_filter_index` | Adiciona índice em `bridge_movie_genre.sk_genre_id` para acelerar filtro por gênero. |
| `0003_add_local_users` | Cria `users`, com e-mail único, papel restrito a `user` ou `admin`, hash de senha e datas de auditoria. |
| `0004_link_reviews_to_users` | Adiciona `movie_reviews.user_id` nullable. Preserva avaliações anteriores sem autor autenticado. |
| `0005_add_user_lists` | Cria `user_lists`, `user_list_movies` e `watch_later_movies`, com visibilidade e unicidades por associação. |
| `0006_add_trailer_to_movies` | Adiciona `dim_movies.url_trailer`, opcional. |
| `0007_add_user_avatars` | Adiciona `users.avatar_url`, opcional. |
| `0008_add_friendship_requests` | Cria `friendship_requests`, estados controlados, FKs e unicidade do par solicitante/destinatário. |
| `0009_add_review_visibility` | Adiciona visibilidade pública/privada às avaliações, com padrão público e `CHECK`. |
| `0010_add_communities` | Cria `communities`, `community_memberships`, `community_posts`, `community_comments` e `community_reactions`. |
| `0011_add_community_views` | Adiciona contador `communities.visualizacoes` para ordenação de descoberta. |
| `0012_add_community_image` | Adiciona `communities.imagem_url`, opcional. |
| `0013_unique_user_movie_review` | Verifica duplicatas existentes e cria índice parcial único conta/filme; falha sem apagar dados se encontrar conflitos. |
| `0014_add_taste_map_synopsis_index` | Cria `movie_synopsis_fts`, preenche-a com sinopses atuais e adiciona triggers de sincronização para otimizar a seleção de candidatos do mapa. |
| `0015_add_community_moderation` | Adiciona `removida_por_moderacao` a `community_posts` e `community_comments`, permitindo ocultar conteúdo sem remover o contexto da conversa. |

As migrations ficam em [`backend/migrations/versions/`](backend/migrations/versions/).
O modelo declarativo correspondente está em `backend/app/movies/models.py`,
`backend/app/users/models.py` e `backend/app/communities/models.py`. As
migrações são mantidas separadas dos modelos para que bancos existentes possam
evoluir sem recriar o schema ou perder os dados carregados.

O arquivo de modelo dimensional descreve o catálogo carregado pela aplicação;
este repositório não afirma executar o pipeline Bronze/Silver/Gold do projeto de
Engenharia de Dados. O seed importa os CSVs preparados diretamente para o
schema relacional SQLite do CineData.

### Fonte de dados externa e trailers

Quando `TMDB_API_TOKEN` está configurado, administradores podem pesquisar o
TMDB durante o cadastro de um filme e importar metadados, imagens e vídeos
disponíveis. Sem token, catálogo local, avaliações e recursos sociais continuam
funcionando; a busca de catálogo também perde somente a resolução de títulos
equivalentes em português/inglês. A chave não deve ser colocada no frontend nem
enviada ao Git.

Os trailers são apresentados por recursos de vídeo disponíveis para o filme e
por incorporação oficial do YouTube. O vídeo de destaque da home usa a fonte
oficial em `youtube-nocookie.com`; não há download nem cópia do arquivo de vídeo
no repositório. Reprodução automática pode ser bloqueada pelo navegador, e o
conteúdo depende da disponibilidade da fonte externa.

## Banco, migrações e seed

O schema atual tem migrações sequenciais de `0001` a `0015`. Entre outras
evoluções, elas adicionam contas, listas, trailers, amizades, privacidade de
avaliações, comunidades, unicidade de avaliações por conta/filme, índice FTS5
para apoiar a busca textual usada pelo mapa de gostos e campos de moderação para
mensagens das comunidades.

O comando `python -m app.db.seed`:

1. verifica se as migrações foram aplicadas e se os arquivos e cabeçalhos são os
   esperados;
2. valida tipos, valores de domínio e referências entre CSVs;
3. grava os dados em lotes dentro de uma única transação;
4. apresenta as quantidades processadas por arquivo; em caso de erro, desfaz a
   transação inteira.

A carga atualiza ou mantém registros pelas chaves existentes, então pode ser
reexecutada. O banco do Compose fica no volume Docker `cinedata-db` e sobrevive
a `docker compose down`; somente `docker compose down -v` remove esse volume.

### Desempenho do mapa de gostos

O mapa não carrega as relações do catálogo inteiro no ORM. Primeiro seleciona
no banco candidatos que compartilham gêneros, pessoas ou termos de sinopse;
sinopses usam o índice SQLite FTS5. Só então carrega as relações completas dos
melhores candidatos e calcula as similaridades detalhadas. O limite atual da
pré-seleção é 2.500 candidatos; os parâmetros finais e limites visuais são
descritos em [docs/api-v1.md](docs/api-v1.md).

Na medição local registrada em 26/09/2026 com os 95.645 filmes, uma geração do
mapa levou aproximadamente 4 segundos e atingiu cerca de 48 MB de pico de
memória Python. O tempo é uma referência daquele ambiente, não uma garantia
para todo hardware ou conjunto de dados.

## Como executar

### Opção recomendada: Docker Compose

1. Instale e inicie o Docker Desktop, usando o modo de containers Linux.
2. Na raiz do projeto, configure um `.env` local para o Compose com os valores
   usados para `JWT_SECRET_KEY`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME` e
   `INITIAL_ADMIN_PASSWORD`. A senha deve ser forte. Esse arquivo é ignorado
   pelo Git.
3. Copie `backend/.env.example` para `backend/.env` se ainda não existir. Se
   quiser importar filmes do TMDB ou preencher automaticamente trailers da
   home, configure `TMDB_API_TOKEN` nesse arquivo.
4. Execute na raiz:

```powershell
docker compose up --build
```

Na primeira execução, o backend constrói o schema, aplica as migrações e carrega
os CSVs antes de ficar saudável; com esse catálogo, a preparação inicial pode
levar alguns minutos. Depois, o frontend inicia automaticamente.

Se o `.env` da raiz definir `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME` e
`INITIAL_ADMIN_PASSWORD`, o backend também cria a conta inicial com papel
`admin` durante a inicialização. As três variáveis são obrigatórias; sem elas,
nenhuma conta administrativa é criada automaticamente. O bootstrap pode rodar
novamente sem duplicar a conta existente. Não há credenciais padrão.

| Serviço | Endereço |
| --- | --- |
| Aplicação web | `http://localhost:8080` |
| API | `http://localhost:8000` |
| Documentação OpenAPI | `http://localhost:8000/docs` |
| Health check | `http://localhost:8000/health` |

Para encerrar sem apagar os dados, use `Ctrl+C` ou `docker compose down`. Para
apagar também o banco local do Compose, use `docker compose down -v`; isso é
irreversível para aquele volume, então faça-o somente se realmente quiser
recomeçar a carga do zero.

No ambiente Compose, `POST /api/v1/auth/sessao-teste` devolve uma sessão da
primeira conta `admin` preparada, útil para demonstração. Essa rota não existe
no modo de desenvolvimento local e só funciona se a conta administrativa tiver
sido configurada.

### Execução local sem Docker

É necessário Python 3.11 ou superior e Node.js compatível com Vite 8 (Node 22 é
usado pela imagem Docker).

#### Backend

No PowerShell, a partir da raiz:

```powershell
Copy-Item backend\.env.example backend\.env
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Edite `backend/.env` para definir pelo menos uma `JWT_SECRET_KEY` segura. Para
criar o primeiro administrador, informe também `INITIAL_ADMIN_EMAIL`,
`INITIAL_ADMIN_NAME` e `INITIAL_ADMIN_PASSWORD`. `TMDB_API_TOKEN` é opcional.
Depois, ainda em `backend/`:

```powershell
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\python -m app.db.seed --database-url "sqlite+aiosqlite:///./rocketlab.db"
.\.venv\Scripts\uvicorn app.main:app --reload
```

A API ficará em `http://localhost:8000`. Para preparar o administrador após as
migrações, se as variáveis estiverem configuradas, execute em outro terminal:

```powershell
Set-Location backend
.\.venv\Scripts\python -m app.users.bootstrap_admin
```

O bootstrap é seguro para repetir com o mesmo e-mail: não cria uma segunda
conta. Não há credenciais padrão embutidas no código.

#### Frontend

Em outro terminal PowerShell, a partir da raiz:

```powershell
Copy-Item frontend\.env.example frontend\.env
Set-Location frontend
npm install
npm run dev
```

O frontend ficará em `http://localhost:5173`. A variável
`VITE_API_BASE_URL` pode apontar para outro endereço da API; por padrão usa
`http://localhost:8000/api/v1`.

## Configuração e credenciais

| Variável | Onde é usada | Finalidade |
| --- | --- | --- |
| `DATABASE_URL` | Backend | URL do banco; localmente usa SQLite em `backend/rocketlab.db`. |
| `BACKEND_CORS_ORIGINS` | Backend | Lista de origens permitidas pelo CORS. |
| `JWT_SECRET_KEY` | Backend e configuração raiz do Compose | Assinatura dos tokens de sessão; use um segredo aleatório e exclusivo. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Duração da sessão JWT. |
| `INITIAL_ADMIN_EMAIL` | Backend e configuração raiz do Compose | E-mail da primeira conta administrativa. |
| `INITIAL_ADMIN_NAME` | Backend e configuração raiz do Compose | Nome da conta administrativa inicial. |
| `INITIAL_ADMIN_PASSWORD` | Backend e configuração raiz do Compose | Senha inicial; mantenha-a fora do repositório. |
| `TMDB_API_TOKEN` | `backend/.env` | Token de leitura usado somente nas chamadas do backend ao TMDB. |
| `VITE_API_BASE_URL` | `frontend/.env` | Endereço-base da API usado pelo Vite no desenvolvimento. |

Os arquivos `.env` contêm segredos e não devem ser commitados. Os arquivos
`.env.example` são modelos sem credenciais reais.

## Testes e verificações

### Backend

```powershell
Set-Location backend
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\ruff check .
```

Os testes do backend cobrem inicialização e configuração, cadastro e login,
permissões administrativas, catálogo e filtros, validação de avaliações,
listas, amizades, perfis, comunidades, analytics, mapa de gostos, integração
com TMDB, segurança de usuários e importação dos CSVs.

### Frontend

```powershell
Set-Location frontend
npm run lint
npm run test
npm run build
```

Vitest e Testing Library cobrem a interação dos componentes com estados de
sucesso, carregamento, erro e formulários, incluindo catálogo, avaliação,
autenticação, listas, perfis, amizades, comunidades, analytics e mapa de gostos.

Na revisão de 26 de setembro de 2026, passaram 77 testes do backend e 54 do
frontend; Ruff, lint e build do frontend também passaram. Migrações, seed em
banco limpo e smoke test com Docker Compose foram verificados no mesmo
checkpoint. O lint mantém um aviso já existente em `MovieDetail.tsx` sobre
atualização de estado dentro de efeito. Os números são um retrato dessa
execução: podem mudar quando novos testes forem adicionados.

## Documentação complementar

- [Convenção e contratos da API](docs/api-v1.md): rotas, parâmetros, autenticação,
  respostas, erros e regras de acesso.
- [Interface e mídia](docs/frontend.md): estados e fluxos visuais, responsividade,
  trailer da home e cobertura dos testes do frontend.
- [TODO e critérios de entrega](TODO.md): etapas, escopo concluído e itens
  opcionais do projeto.

## Limitações conhecidas

- SQLite e um único processo são apropriados à demonstração local; implantação
  concorrente de maior escala exigiria banco servidor, estratégia de arquivos e
  infraestrutura de execução adequada.
- Conversas de comunidades usam polling a cada cinco segundos enquanto estão
  abertas e visíveis. Não há WebSocket nem paginação do histórico completo.
- A métrica “mais vistas” conta aberturas da conversa e reaberturas, não pessoas
  únicas; ela pode ser manipulada e começa a acumular após a migração de views.
- A busca textual do catálogo local é pelo título e não é fuzzy. A pesquisa do
  TMDB é uma integração administrativa separada.
- Os gráficos refletem a atividade gravada no banco. Dados iniciais do catálogo
  não criam usuários, listas ou atividade social histórica artificial.
- O mapa faz similaridade de conteúdo sobre o catálogo local e uma shortlist de
  candidatos; não treina um modelo nem conhece filmes que não estejam na base.
- Imagens, fontes e vídeos externos dependem da disponibilidade do serviço de
  origem, da conexão e das políticas do navegador.
