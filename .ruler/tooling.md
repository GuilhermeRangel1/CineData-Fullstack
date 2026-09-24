# Tooling e convenções de implementação

## Estrutura esperada

```text
.
├── backend/       # FastAPI, SQLAlchemy, Alembic e testes Python
├── frontend/      # Vite, React, TypeScript e testes da interface
├── data/raw/      # CSVs originais, versionados sem alterações
└── .ruler/        # fonte central das instruções para agentes
```

Não mova os módulos existentes do backend sem necessidade técnica demonstrável.

## Backend

- Use as dependências e configurações declaradas em `backend/pyproject.toml`.
- Mantenha endpoints de negócio sob `/api/v1` e preserve `GET /health`.
- Use schemas Pydantic distintos dos modelos ORM para entrada e saída da API.
- Use `AsyncSession` e consultas SQLAlchemy 2; evite SQL textual sem necessidade.
- Faça `commit` e `rollback` em limites transacionais claros.
- Paginação deve ter parâmetros validados, ordem determinística e metadados
  suficientes para a interface navegar entre páginas.
- Busca textual deve ser segura, case-insensitive quando suportado e combinável
  com a paginação.
- Retorne códigos HTTP coerentes: 201 para criação, 204 para exclusão bem-sucedida,
  404 para recurso ausente e 422 para entrada inválida.
- Evite consultas N+1 ao carregar gêneros, pessoas, desempenho e avaliações.

Comandos de verificação do backend devem partir de `backend/`:

```bash
python -m pytest
python -m ruff check .
alembic upgrade head
```

## Frontend

- Crie o frontend em `frontend/` com Vite, React e TypeScript.
- Use componentes funcionais e TypeScript estrito; não introduza `any` sem uma
  justificativa localizada.
- Centralize o cliente HTTP e os tipos de contrato da API.
- Separe páginas, componentes reutilizáveis e acesso a dados.
- Implemente, no mínimo, catálogo, pesquisa, paginação, detalhes, formulário de
  filme, edição, exclusão e criação de avaliação.
- Confirme ações destrutivas e preserve mensagens de erro úteis ao usuário.
- Mantenha a interface utilizável em telas móveis e desktop.
- Adicione dependências somente quando reduzirem complexidade real. Não adicione
  bibliotecas apenas para substituir recursos simples da plataforma.

Comandos mínimos esperados do frontend, executados em `frontend/`:

```bash
npm run lint
npm run test
npm run build
```

Se o template não fornecer `test`, adicione uma configuração de testes antes de
declarar a interface concluída.

## Banco e carga dos CSVs

- O Alembic é a única autoridade para criar ou alterar tabelas.
- A carga deve usar os CSVs de `data/raw/dimensions/` e `data/raw/facts/`.
- Carregue dimensões antes de tabelas de associação, fatos e avaliações.
- Valide cabeçalhos e referências antes de gravar; falhe com mensagem clara em
  vez de ignorar linhas silenciosamente.
- Faça a carga em lotes para não manter todo o conjunto em memória.
- Produza um resumo com quantidades inseridas, atualizadas, ignoradas e inválidas.
- A execução repetida deve produzir o mesmo estado final.

## Testes

- Backend: teste validação, CRUD, busca, paginação, avaliações, média, conversão
  de escalas, integridade referencial e idempotência da carga.
- Frontend: teste os fluxos principais e os estados de carregamento, vazio e erro.
- Use banco temporário isolado nos testes; nunca dependa de `rocketlab.db` local.
- Para correções de defeitos, escreva um teste que falhe antes da correção sempre
  que isso for viável.

## Disciplina de mudanças

- Faça alterações pequenas e coerentes com o requisito em andamento.
- Não edite o README antecipadamente. Atualize-o quando os comandos e fluxos
  descritos puderem ser executados e verificados.
- Preserve mudanças do usuário que não façam parte da tarefa atual.
- Não crie funcionalidades opcionais enquanto houver requisito obrigatório
  incompleto.

