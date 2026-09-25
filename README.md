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

Os comandos acima foram validados em 25 de setembro de 2026: 30 testes do
backend, 30 testes do frontend, lint dos dois projetos e o build de produção
do frontend passaram. As migrations também foram aplicadas em um banco SQLite
temporário antes da carga dos CSVs.

## Arquitetura, segurança e desempenho

O backend separa routers HTTP, serviços de domínio e modelos SQLAlchemy. O
Alembic é a única autoridade para evoluir o schema: a migration inicial cria o
catálogo e a migration `0002_add_catalog_filter_index` adiciona um índice para
o filtro por gênero. O frontend centraliza chamadas HTTP e invalida o cache de
leitura após alterações no catálogo.

O CORS aceita apenas as origens locais configuradas em
`BACKEND_CORS_ORIGINS`: por padrão `http://localhost:5173`; no Docker Compose,
também `http://localhost:8080`. A API devolve envelopes de erro públicos e não
expõe detalhes internos de validação, persistência ou falhas inesperadas.

O catálogo foi revisado usando os dados completos fornecidos (95.645 filmes).
O filtro por gênero resolve primeiro a chave do gênero e usa o índice da tabela
de associação; assim evita varreduras e remoção redundante de duplicatas. Os
detalhes carregam relações com `selectinload`, prevenindo consultas N+1.

## Limitações conhecidas

- A aplicação é administrativa e ainda não possui autenticação, contas de
  usuário ou autorização por perfil.
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
