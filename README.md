# Rocket Lab 2026.2 - CineData Analytics

Projeto da atividade DEV do Rocket Lab 2026.2: um sistema administrativo de
avaliação de filmes, inspirado em plataformas como Letterboxd.

## Objetivo

Permitir que o administrador gerencie um catálogo de filmes e suas avaliações.
O projeto utiliza Vite, React e TypeScript no frontend; FastAPI no backend; e
SQLite como banco de dados.

A aplicação permite:

- cadastrar, editar e remover filmes;
- navegar por um catálogo paginado e pesquisar por título;
- consultar detalhes do filme, avaliações e média das notas;
- adicionar uma nota de 0 a 10 e uma resenha para cada filme.

## Estrutura

```text
backend/       API FastAPI, modelos SQLAlchemy, migrações e testes
frontend/      Aplicação Vite, React e TypeScript
data/raw/      CSVs fornecidos para a carga inicial
TODO.md        Plano de execução do projeto
```

## Estado atual

A API oferece CRUD de filmes, busca, paginação, detalhes e avaliações, com
migrações e seed dos CSVs. O frontend já consulta essa API: catálogo, fileiras
por gênero, pesquisa e detalhes com histórico e média de 0 a 10. Também permite
cadastrar, editar, excluir filmes com confirmação e publicar avaliações.
Também oferece cadastro e login locais por e-mail e senha, com sessão JWT.
O catálogo é público; somente contas autenticadas podem avaliar e somente
administradores podem alterar o catálogo.

A identidade CineData Analytics tem destaque editorial de O Castelo Animado
com trailer oficial incorporado. As etapas obrigatórias e a revisão de
qualidade/entrega estão concluídas.
Veja as fontes de mídia e os comportamentos do player em
[Interface e mídia](docs/frontend.md).

## Como executar

### Docker Compose

Com Docker Desktop em execução, suba a aplicação completa com:

```powershell
docker compose up --build
```

O frontend ficará em `http://localhost:8080`, a API em `http://localhost:8000`
e o health check em `http://localhost:8000/health`. Na primeira inicialização,
o container do backend aplica as migrações e executa o seed dos CSVs. O banco
fica no volume nomeado `cinedata-db`; a carga pode ser repetida sem duplicar
registros. Para encerrar os containers, use `Ctrl+C` ou `docker compose down`.
O volume não é removido por `down`, então os dados persistem entre reinícios.

### Frontend

```powershell
Set-Location frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Acesse `http://localhost:5173`.

### Backend

```powershell
Set-Location backend
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\python -m app.db.seed --database-url "sqlite+aiosqlite:///./rocketlab.db"
.\.venv\Scripts\uvicorn app.main:app --reload
```

Acesse `http://localhost:8000/health` para verificar a API e
`http://localhost:8000/docs` para a documentação automática.

### Contas locais e administrador inicial

O cadastro público em `POST /api/v1/auth/cadastro` cria exclusivamente contas
com o papel `user`. O login em `POST /api/v1/auth/login` devolve um JWT Bearer;
antes de usá-lo, configure uma chave de assinatura no `backend/.env`:

```env
JWT_SECRET_KEY=uma-chave-aleatoria-longa-e-exclusiva-para-este-ambiente
```

Para criar o primeiro administrador, defina também no mesmo arquivo:

```env
INITIAL_ADMIN_EMAIL=admin@exemplo.com
INITIAL_ADMIN_NAME=Administrador
INITIAL_ADMIN_PASSWORD=defina-uma-senha-forte
```

Após aplicar as migrações, execute uma única vez:

```powershell
.\.venv\Scripts\python -m app.users.bootstrap_admin
```

O comando é idempotente: se já houver um administrador com o e-mail informado,
ele não é duplicado. Não há senha ou administrador padrão no código. Para usar
o Docker Compose, informe as mesmas variáveis no ambiente do PowerShell antes
de executar `docker compose up --build`.

O frontend mantém a sessão localmente e envia o JWT no cabeçalho Bearer. O
catálogo e seus detalhes continuam públicos; publicar uma avaliação exige login,
e criar, editar ou remover filmes exige uma conta `admin`.

## Verificações

```powershell
# Backend
Set-Location backend
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\ruff check .

# Frontend
Set-Location frontend
npm run lint
npm run test
npm run build
```

Os comandos acima foram validados em 25 de setembro de 2026: 38 testes do
backend, 30 testes do frontend, lint dos dois projetos e o build de produção
do frontend passaram. As migrations também foram aplicadas em um banco SQLite
temporário antes da carga dos CSVs.

## Arquitetura, segurança e desempenho

O backend separa routers HTTP, serviços de domínio e modelos SQLAlchemy. O
Alembic é a única autoridade para evoluir o schema: a migration inicial cria o
catálogo, a migration `0002_add_catalog_filter_index` adiciona um índice para o
filtro por gênero, a `0003_add_local_users` cria as contas locais e a
`0004_link_reviews_to_users` vincula novas avaliações a elas, sem alterar as
avaliações importadas. Senhas são persistidas somente como hash Argon2; a sessão
é um JWT assinado por uma chave externa ao repositório. O frontend centraliza
chamadas HTTP, envia o Bearer da sessão e invalida o cache de leitura após
alterações no catálogo.

O CORS aceita apenas as origens locais configuradas em
`BACKEND_CORS_ORIGINS`: por padrão `http://localhost:5173`; no Docker Compose,
também `http://localhost:8080`. A API devolve envelopes de erro públicos e não
expõe detalhes internos de validação, persistência ou falhas inesperadas.

O catálogo foi revisado usando os dados completos fornecidos (95.645 filmes).
O filtro por gênero resolve primeiro a chave do gênero e usa o índice da tabela
de associação; assim evita varreduras e remoção redundante de duplicatas. Os
detalhes carregam relações com `selectinload`, prevenindo consultas N+1.

## Limitações conhecidas

- As conversas de comunidades são atualizadas por polling a cada cinco segundos
  enquanto a janela está aberta e a aba está visível; não há entrega instantânea
  por WebSocket. O histórico ainda é carregado integralmente.
- "Mais vistas" ordena comunidades por aberturas da conversa, contando também
  reaberturas. A contagem começa com a migration `0011_add_community_views` e não
  representa visitantes únicos nem possui proteção contra manipulação do ranking.
- O SQLite é adequado para a execução local e demonstração da atividade; uma
  implantação concorrente de maior escala exigiria um banco servidor.
- A busca atual é textual por título. Busca tolerante a erros de digitação ou
  por relevância exigiria um mecanismo de busca dedicado.

## Dados iniciais

Os 10 CSVs fornecidos estão em `data/raw/` e devem permanecer sem edição
manual. Depois de aplicar as migrações, execute o comando abaixo a partir de
`backend/` para carregá-los:

```powershell
.\.venv\Scripts\python -m app.db.seed --database-url "sqlite+aiosqlite:///./rocketlab.db"
```

A carga valida os cabeçalhos, os tipos e todas as referências entre os CSVs,
processa registros em lotes de 1.000 e mostra um resumo por arquivo. Ela usa
uma única transação: qualquer erro desfaz a carga inteira. É seguro repetir o
comando, pois as chaves fornecidas nos CSVs são usadas para atualizar ou manter
os registros existentes sem criar duplicidades. Para ajustar o tamanho dos
lotes, adicione `--batch-size 500` (ou outro inteiro positivo).
