# Backend: dados e persistência

Este guia reúne os detalhes do modelo relacional, das migrações e da carga inicial do catálogo. Para executar o projeto, use os passos do [README principal](../README.md); para consultar as rotas HTTP, veja [API v1](api-v1.md).

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
| `community_reactions` | Um par publicação/conta | Uma reação por pessoa e publicação; tipos permitidos: `curtir` (🔥), `amei` (❤️), `interessante` (🍿) e `nao_curti` (👎). |

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
| `0016_clean_movie_runtime` | Converte durações nulas ou inválidas em desconhecidas e impede que novos valores menores que 1 minuto sejam gravados. |
| `0017_validate_movie_performance` | Trata notas sem votos como desconhecidas, corrige métricas inconsistentes existentes e protege métricas financeiras e externas com validações no banco. |
| `0018_add_dislike_reaction` | Permite a reação `nao_curti` nas publicações de comunidades. |

As migrations ficam em [`backend/migrations/versions/`](backend/migrations/versions/).
O modelo declarativo correspondente está em `backend/app/movies/models.py`,
`backend/app/users/models.py` e `backend/app/communities/models.py`. As
migrações são mantidas separadas dos modelos para que bancos existentes possam
evoluir sem recriar o schema ou perder os dados carregados.

O arquivo de modelo dimensional descreve o catálogo carregado pela aplicação;
este repositório não afirma executar o pipeline Bronze/Silver/Gold do projeto de
Engenharia de Dados. O seed importa os CSVs preparados diretamente para o
schema relacional SQLite do CineData.

## Banco, migrações e seed

As migrações sequenciais e suas alterações estão detalhadas em “Histórico de
evolução do schema”, acima. O comando `python -m app.db.seed`:

1. verifica se as migrações foram aplicadas e se os arquivos e cabeçalhos são os
   esperados;
2. valida tipos, valores de domínio e referências entre CSVs;
3. grava os dados em lotes de até 10 mil linhas dentro de uma única transação;
4. apresenta progresso nos arquivos grandes e, ao final, as quantidades
   processadas por arquivo; em caso de erro, desfaz a
   transação inteira.

No SQLite, a carga usa WAL, sincronização `NORMAL` e cache de 64 MiB para
reduzir o custo da importação inicial sem dividir a transação. Depois que o
catálogo é carregado, as próximas inicializações do Compose pulam o seed quando
já existem filmes no banco.

A seed contém cerca de 95 mil filmes e não consulta a internet durante a
inicialização. O importador converte duração zero ou negativa em valor
desconhecido; a migração `0016` aplica o mesmo tratamento aos bancos existentes.
Notas TMDB/IMDb associadas a zero votos também são tratadas como desconhecidas; a
migração `0017` corrige os bancos existentes e impede notas fora da escala,
contagens negativas e popularidade ou valores financeiros negativos.
O catálogo começa pelos títulos mais relevantes, usando a nota do TMDB ponderada
pelo número de votos e pela popularidade já importada. Assim, títulos conhecidos
ganham destaque sem aumentar o volume da seed nem o tempo da primeira carga.

Na revisão de 27/09/2026, a seed tinha 95.645 IDs de filme únicos e sinopse,
data e ano preenchidos em todos os registros. Cerca de 8.241 filmes não têm pôster
e 38.308 não têm backdrop; essas ausências estão concentradas na cauda menos
popular do catálogo. A seed permanece independente de consultas externas e os
arquivos de imagem são carregados em tamanhos adequados à interface (`w500` para
pôsteres e `w1280` para backdrops).

O catálogo e a integração administrativa usam dados do TMDB. O rodapé da aplicação
exibe a atribuição exigida pelo serviço; consulte os [termos da API do TMDB](https://www.themoviedb.org/api-terms-of-use).

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

