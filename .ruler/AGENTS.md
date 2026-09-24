# CineData - limites da atividade

## Objetivo

Entregar uma aplicação full-stack de administração de um catálogo de filmes,
inspirada em plataformas como Letterboxd. O administrador deve conseguir
consultar e gerenciar filmes e registrar avaliações.

## Fontes de verdade

Use esta ordem para resolver dúvidas de escopo:

1. solicitação explícita do usuário;
2. requisitos obrigatórios da atividade Rocket Lab 2026.2;
3. arquitetura e contratos já existentes no repositório;
4. estrutura e valores dos CSVs em `data/raw/`.

Não trate sugestões opcionais da atividade como requisitos obrigatórios. Quando
duas fontes entrarem em conflito, preserve os dados existentes e implemente uma
adaptação explícita na camada de aplicação. Registre a decisão em testes e na
documentação pertinente.

## Stack obrigatória

- Frontend: Vite, React e TypeScript.
- Backend: FastAPI em Python 3.11 ou superior.
- Persistência: SQLite, SQLAlchemy 2 assíncrono e Alembic.
- Não substitua essas tecnologias por frameworks ou bancos alternativos.

## Escopo obrigatório

A implementação deve permitir:

- cadastrar filmes com, no mínimo, título, diretor, ano de lançamento, gênero e sinopse;
- listar todos os filmes em catálogo paginado;
- pesquisar filmes por texto, ao menos pelo título;
- abrir os detalhes completos de um filme;
- atualizar e remover filmes individualmente;
- listar o histórico de avaliações de cada filme;
- adicionar uma avaliação com nota e resenha em texto;
- exibir a média geral das avaliações de cada filme;
- carregar os dados iniciais fornecidos nos CSVs de forma reproduzível.

O frontend deve oferecer os fluxos acima pela interface. Não considere a tarefa
concluída se uma funcionalidade existir apenas na API ou apenas na interface.

## Regra de avaliações

- A experiência do usuário usa uma escala de 1 a 5 estrelas, conforme a atividade.
- Os CSVs e o modelo inicial usam notas de 0 a 10; preserve os arquivos brutos e
  o armazenamento nessa escala para evitar perda ou reinterpretação dos dados.
- Converta estrelas para a escala persistida multiplicando por 2 e converta a
  escala persistida para estrelas dividindo por 2.
- Centralize a conversão na camada de aplicação; não espalhe cálculos pelo
  frontend, pelos routers e pelos repositórios.
- Valide os limites nas entradas e cubra conversão e média com testes.
- A média exibida ao usuário deve estar na escala de 1 a 5 estrelas.

## Limites de arquitetura e dados

- Preserve a organização atual do backend e evolua o schema somente por
  migrações Alembic. Não use `create_all` em execução normal.
- Trate `data/raw/` como fonte imutável. Não corrija, reformate nem sobrescreva
  os CSVs para facilitar a importação.
- A carga deve respeitar chaves estrangeiras, ser transacional e poder ser
  executada novamente sem duplicar registros.
- Mantenha regras de negócio fora dos componentes React e dos handlers HTTP
  quando houver uma camada de serviço apropriada.
- Não exponha rastros de exceção, caminhos locais ou detalhes internos do banco
  nas respostas da API.
- Não versionar segredos, arquivos `.env`, bancos SQLite locais, ambientes
  virtuais, `node_modules` ou artefatos de build.

## Padrão de engenharia

- Organize mudanças por responsabilidade: rotas tratam HTTP, serviços contêm
  regras de negócio e persistência fica isolada da apresentação.
- Defina contratos de entrada e saída separados dos modelos ORM. Valide limites,
  formatos, paginação e relações antes de iniciar escritas.
- Toda escrita que afetar mais de uma entidade deve ser atômica. Ao ocorrer
  erro, desfaça a transação e retorne uma resposta segura e coerente.
- Prefira comportamento determinístico: ordenação explícita, mensagens de erro
  previsíveis e cargas idempotentes.
- Registre eventos relevantes para diagnóstico, sem expor segredos, conteúdo de
  avaliações ou rastros internos ao cliente.
- Trate acessibilidade, responsividade, estado vazio, carregamento e falha como
  requisitos de cada fluxo de interface, não como acabamento posterior.
- Antes de concluir uma mudança, execute as verificações aplicáveis e revise o
  diff para garantir que não houve alteração fora de escopo.
- Nunca prepare, crie ou publique commits, nem altere histórico Git, crie
  branches, abra pull requests ou altere remotos sem um pedido explícito do
  usuário na conversa atual. Ao terminar uma etapa, explique o que foi feito,
  seus impactos, as verificações realizadas e as propostas de desenvolvimento;
  então aguarde a decisão do usuário sobre o próximo passo.

## Fora do escopo inicial

Não implemente antes dos requisitos obrigatórios estarem completos e testados:

- autenticação, autorização ou múltiplos perfis de usuário;
- recomendações, recursos generativos ou integrações com APIs externas;
- Storybook, cache distribuído, filas, microsserviços ou infraestrutura cloud;
- dashboards analíticos adicionais ou redesigns sem relação com os fluxos exigidos.

Esses itens só entram no escopo mediante solicitação explícita do usuário.

## Critérios de conclusão

Uma entrega só está pronta quando:

- os fluxos obrigatórios funcionam de ponta a ponta;
- migrações e carga inicial partem de um clone limpo;
- testes automatizados cobrem regras de negócio e operações críticas;
- lint, testes e builds aplicáveis passam;
- estados de carregamento, vazio, validação e erro são tratados na interface;
- o README contém comandos realmente verificados para instalar e executar a aplicação.
