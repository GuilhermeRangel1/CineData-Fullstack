# Rocket Lab 2026.2 - CineData Analytics

Projeto da atividade DEV do Rocket Lab 2026.2: um sistema administrativo de
avaliação de filmes, inspirado em plataformas como Letterboxd.

## Objetivo

Permitir que o administrador gerencie um catálogo de filmes e suas avaliações.
O projeto utiliza Vite, React e TypeScript no frontend; FastAPI no backend; e
SQLite como banco de dados.

Ao final, a aplicação deverá permitir:

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

Há uma base de backend com modelos, migrações e health check. O frontend possui
um catálogo demonstrativo com busca local e dados simulados. Os contratos de
dados já foram definidos, mas a API de negócio, a carga dos CSVs e a integração
com o frontend ainda estão em desenvolvimento.

## Como executar

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
npm run build
```

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
