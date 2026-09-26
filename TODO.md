# CineData - plano de execução

Este checklist prioriza os requisitos obrigatórios da atividade. Só inicie a
próxima etapa quando o critério de saída da etapa atual estiver atendido.

## 1. Base de desenvolvimento e contratos

- [x] Confirmar a estrutura final: `backend/`, `frontend/` e `data/raw/`.
- [x] Criar o frontend com Vite, React e TypeScript em `frontend/`.
- [x] Criar `.env.example` com configurações não sensíveis e alinhar o README
      aos comandos realmente executáveis no Windows e no CI.
- [x] Definir contratos Pydantic e TypeScript para filme, gênero, pessoa,
      avaliação, paginação e respostas de erro.
- [x] Definir a convenção de API sob `/api/v1`, incluindo filtros, paginação,
      ordenação estável e códigos HTTP.
- [x] Criar uma camada de serviços para regras de negócio e manter routers, ORM
      e componentes React em responsabilidades separadas.

**Critério de saída:** backend e frontend iniciam localmente; health check,
lint e typecheck iniciais funcionam; os contratos não expõem entidades ORM.

## 2. Banco, migrações e carga inicial

- [x] Conferir a compatibilidade entre modelos SQLAlchemy, migração inicial e
      os 10 CSVs versionados.
- [x] Criar uma rotina ou comando de carga documentado, que leia os CSVs sem
      modificá-los e respeite a ordem de chaves estrangeiras.
- [x] Implementar carga em lotes, validação de cabeçalhos e referências, resumo
      de registros processados e falha clara para dados inválidos.
- [x] Garantir idempotência: duas execuções da carga resultam no mesmo estado
      final, sem duplicação.
- [x] Usar transações com rollback em falhas e manter o Alembic como única
      autoridade para criação/evolução de tabelas.
- [x] Preparar banco SQLite temporário e isolado para testes de integração.

**Critério de saída:** um clone limpo executa migrações e importa todos os
CSVs; a segunda carga não altera contagens ou cria duplicados.

## 3. Backend: catálogo e gestão de filmes

- [x] Implementar criação de filme com título, diretor, ano, gênero e sinopse,
      preservando os relacionamentos do modelo existente.
- [x] Implementar catálogo paginado, com ordem determinística e metadados de
      página suficientes para a interface.
- [x] Implementar busca textual por título, combinável com a paginação.
- [x] Implementar consulta de detalhes com gêneros, pessoas, desempenho,
      avaliações e média.
- [x] Implementar atualização parcial e remoção individual, retornando 404 para
      recurso inexistente.
- [x] Prevenir consultas N+1 e validar limites de paginação, textos e datas.
- [x] Padronizar respostas de erro, logs úteis sem dados sensíveis e rollback
      em qualquer falha de escrita.

**Critério de saída:** CRUD, busca, paginação e detalhes possuem testes de API
para sucesso, validação, recurso inexistente e falha transacional relevante.

## 4. Backend: avaliações e média

- [x] Implementar a criação e listagem do histórico de avaliações por filme.
- [x] Receber, validar e apresentar notas na escala de 0 a 10.
- [x] Manter a escala de 0 a 10 de forma consistente entre API, banco e CSVs,
      sem alterar os arquivos brutos.
- [x] Calcular ou atualizar a média de avaliações com consistência após cada
      inserção, sem divergência entre detalhes e catálogo.
- [x] Validar nota, autor e resenha, e manter a integridade referencial ao
      excluir filmes.

**Critério de saída:** testes cobrem limites de nota na escala de 0 a 10,
histórico, média e comportamento após exclusão de filme.

## 5. Frontend: fluxos obrigatórios

- [x] Criar catálogo e consulta de detalhes em janela acessível, integrados à API.
- [x] Criar a interface de gestão de filmes.
- [x] Implementar busca, paginação e estados de carregamento, vazio e erro no
      catálogo.
- [x] Implementar formulário de criação e edição com validação clara antes de
      enviar à API.
- [x] Implementar exclusão com confirmação e feedback de sucesso ou falha.
- [x] Exibir detalhes completos, média de 0 a 10 e histórico de avaliações.
- [x] Implementar formulário para nova avaliação, com seletor de 0 a 10 e
      resenha.
- [x] Garantir navegação por teclado, rótulos de formulário, contraste e uso
      adequado em telas móveis e desktop.

**Critério de saída:** todos os requisitos obrigatórios podem ser realizados
pela interface usando a API real, inclusive em estados sem dados e com erro.

**Checkpoint visual:** identidade CineData Analytics, destaque editorial de
O Castelo Animado com trailer oficial incorporado e imagem alternativa,
fileiras por gênero, catálogo paginado e detalhes. Os fluxos de cadastro,
edição, exclusão e avaliação estão implementados, com validação, confirmação,
feedback e atualização das consultas. Vitest cobre o fluxo completo e falhas;
cadastro, edição e avaliação também foram exercitados no navegador com API real
e banco isolado. A revisão final de entrega permanece na etapa 6.

## 6. Qualidade, robustez e entrega

- [x] Disponibilizar execução reproduzível com Docker Compose, incluindo frontend,
      backend, migrações, seed idempotente, health checks e persistência SQLite.
- [x] Aumentar a cobertura dos fluxos críticos no backend e no frontend,
      priorizando regras de negócio, falhas e regressões.
- [x] Executar lint, typecheck, testes, build do frontend e migrações em uma
      sequência reproduzível.
- [x] Revisar CORS para aceitar somente as origens locais necessárias e nunca
      retornar detalhes internos em mensagens de erro.
- [x] Revisar desempenho das rotas de catálogo e detalhes com o volume dos CSVs.
- [x] Documentar arquitetura, comandos de instalação, carga de dados, execução,
      testes e limitações no README apenas após validá-los.
- [x] Revisar o diff final, confirmar que `.env`, bancos locais, dependências e
      builds não estão versionados, e separar commits por assunto.

**Critério de saída:** os comandos documentados funcionam em clone limpo e a
aplicação atende todos os requisitos obrigatórios de ponta a ponta.

## Próximas extensões planejadas

### 7. Contas locais e autorização

- [x] Criar tabela de usuários sem alterar os dados existentes do catálogo.
- [x] Armazenar senha somente como hash seguro, nunca em texto puro.
- [x] Criar endpoints de cadastro e login local por e-mail e senha.
- [x] Emitir JWT próprio da aplicação após o login.
- [x] Criar os perfis `user` e `admin`.
- [x] Manter catálogo e detalhes públicos sem autenticação.
- [x] Criar telas de cadastro, login e encerramento de sessão no frontend.
- [x] Exigir autenticação para criar avaliações.
- [x] Restringir gestão de filmes ao administrador.
- [x] Vincular novas avaliações ao usuário e preservar avaliações importadas.

**Critério de saída:** cadastro e login emitem uma sessão local segura; catálogo
permanece público; avaliações exigem usuário autenticado; e a gestão de filmes
aceita somente administradores, com testes cobrindo autenticação e autorização.

### 8. Avaliações, listas e perfis

- [x] Exibir a média geral e a quantidade de avaliações por filme.
- [x] Criar a lista virtual obrigatória de filmes avaliados por cada usuário.
- [x] Permitir listas personalizadas com nome e filmes do catálogo.
- [x] Implementar a lista "assistir depois".
- [x] Definir visibilidade das listas públicas e privadas.
- [x] Criar perfis públicos com avaliações, listas públicas e quantidade de
      amigos.
- [x] Adicionar trailer opcional ao detalhe do filme quando houver uma fonte
      válida, sem alterar os CSVs originais.

**Critério de saída:** usuário autenticado cria e gerencia listas, usa
"assistir depois", atualiza seu perfil com avatar e consulta perfis públicos;
detalhes exibem trailer do YouTube quando configurado; migrações, testes,
lint e build passam sem alterar os CSVs originais.

### 9. Comunidades

- [x] Restringir gestão de comunidades ao administrador.
- [x] Permitir que o administrador crie, edite e exclua comunidades.
- [x] Permitir que usuários entrem e saiam de comunidades.
- [x] Criar publicações e comentários relacionados a filmes do catálogo.
- [x] Permitir mencionar um filme usando `movie_id` e exibir seus dados no post.
- [x] Adicionar reações simples às publicações.
- [x] Usar requisições HTTP/polling inicialmente; avaliar WebSockets apenas se
      a experiência exigir atualização em tempo real.
- [x] Exibir quatro comunidades mais vistas e revelar mais quatro com "Ver mais",
      registrando aberturas da conversa para ordenar a descoberta.
- [x] Abrir chat em janela flutuante a partir do card, com mensagens cronológicas,
      avatar, nome clicável para o perfil público, menções de filmes e reações.
- [x] Atualizar mensagens a cada cinco segundos sem tirar o usuário da leitura
      de mensagens antigas; preservar o texto quando o envio falhar.

**Critério de saída:** administrador gerencia comunidades; usuários entram,
saem e interagem com publicações, comentários, menções de filmes e reações;
descoberta destaca as mais vistas e o chat permite consultar o perfil público
dos autores; permissões, visibilidade dos dados relacionados e fluxos principais
possuem testes de API e interface.

### 10. Amizades

- [x] Criar solicitações de amizade com estados pendente, aceita e bloqueada.
- [x] Permitir consultar amigos e quantidade de amigos no perfil.
- [x] Respeitar a visibilidade definida para listas e avaliações.

**Critério de saída:** usuário autenticado envia, aceita, bloqueia e remove
amizades; perfil público informa a quantidade correta de amigos; e listas ou
avaliações privadas não aparecem nas consultas públicas, com testes cobrindo
transições de solicitação, autorização e visibilidade.

### 11. Recursos opcionais

- [ ] Implementar filtros avançados além de título, gênero, ordenação e
      paginação.
- [ ] Implementar recomendações baseadas em avaliações e listas.
- [ ] Criar um "Mapa de gostos": grafo interativo com filmes avaliados pelo
      usuário, recomendações próximas e conexões explicadas por afinidades
      como gênero, direção ou elenco.
- [ ] Integrar fonte externa para dados ou trailers de filmes.
- [ ] Criar Storybook para componentes visuais.
- [x] Manter cache de consultas de leitura no frontend.
- [ ] Adicionar métricas externas e observabilidade.
- [ ] Criar pipeline de CI/CD.
- [x] Disponibilizar execução local via Docker Compose.
- [ ] Avaliar quizzes, conquistas, níveis, notícias e eventos somente depois
      de validar o núcleo social.

**Critério de saída:** cada item opcional marcado como concluído possui fluxo
utilizável, documentação e validação proporcional ao seu impacto, sem regredir
os requisitos obrigatórios ou expor dados sensíveis.
