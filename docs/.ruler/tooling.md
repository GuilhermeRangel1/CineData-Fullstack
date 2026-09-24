# Tooling e convenções de implementação

## Estrutura esperada

```text
.
├── backend/       # FastAPI, SQLAlchemy, Alembic e testes Python
├── frontend/      # Vite, React, TypeScript e testes da interface
├── data/raw/      # CSVs originais, versionados sem alterações
└── docs/.ruler/   # fonte central das instruções para agentes
```

Não mova os módulos existentes do backend sem necessidade técnica demonstrável.

## Fluxo de trabalho por tarefa

- Antes de editar, leia o item correspondente no `TODO.md`, os contratos
  envolvidos e a documentação diretamente relacionada ao requisito.
- Trabalhe em uma unidade coerente por vez. Não marque um item como concluído
  enquanto sua validação ainda estiver pendente.
- É permitido criar novos arquivos quando isso melhorar a separação de
  responsabilidades ou for necessário para atender ao requisito. O arquivo
  novo deve respeitar a estrutura do projeto, não duplicar uma responsabilidade
  existente e não contrariar o conteúdo-base deste Ruler.
- Preserve os CSVs originais, contratos públicos, decisões arquiteturais e
  limites de escopo existentes. Se uma mudança precisar contrariar uma dessas
  decisões, registre a justificativa e consulte o usuário antes de prosseguir.
- Antes de concluir qualquer alteração, revise o diff e execute as validações
  aplicáveis à área modificada. Uma alteração só está pronta quando os gates
  relevantes passam sem erros.
- Não execute operações Git que alterem o histórico sem pedido explícito do
  usuário. Por padrão, mantenha as alterações locais e informe o estado,
  impactos, validações e próximo passo.

## Validação obrigatória

Toda mudança deve ter uma validação proporcional ao risco. Para código novo ou
alterado, isso inclui testes automatizados do comportamento e dos casos de
erro relevantes, sempre que possível. Para alterações de banco, use um SQLite
temporário, aplique as migrações a partir de um banco vazio e valide rollback e
integridade referencial. Para contratos ou documentação de API, confirme os
status HTTP e o formato público das respostas.

Gates mínimos disponíveis no projeto:

```powershell
# Backend, executados a partir de backend/
python -m ruff format --check .
python -m ruff check .
python -m pytest

# Frontend, executados a partir de frontend/
npm run lint
npm run build
```

Quando um comando ainda não existir no projeto, não o invente como se tivesse
passado: registre a limitação e use a verificação equivalente disponível.
Após os gates, confirme com `git diff --check` que não há erro de whitespace ou
alteração acidental fora do escopo.

## Arquitetura da aplicação

- Routers cuidam de parsing HTTP, status e dependências; não concentram regras
  de negócio ou consultas complexas.
- Serviços coordenam validação de domínio, conversões de nota, transações e
  regras que envolvam mais de uma entidade.
- Acesso a dados deve permanecer testável e não deve vazar detalhes SQLAlchemy
  para componentes React ou contratos de API.
- Use uma representação de erro consistente para toda a API e nunca retorne
  exceções, SQL ou caminhos locais ao cliente.
- Mantenha interfaces e tipos de contrato como fonte de verdade entre frontend
  e backend; não replique estruturas sem necessidade.

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
- Dê ordem explícita a toda coleção exposta pela API.
- Faça logs estruturados de falhas e operações de carga, sem registrar segredos,
  comentários completos ou dados além do necessário para diagnóstico.
- Restrinja CORS às origens configuradas para cada ambiente; não use coringa em
  produção.

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
- Não carregue CSVs inteiros em memória quando puder processá-los em lotes.
- Mantenha métricas de carga verificáveis: linhas lidas, inseridas, atualizadas,
  ignoradas e rejeitadas.

## Testes

- Backend: teste validação, CRUD, busca, paginação, avaliações, média, conversão
  de escalas, integridade referencial e idempotência da carga.
- Frontend: teste os fluxos principais e os estados de carregamento, vazio e erro.
- Use banco temporário isolado nos testes; nunca dependa de `rocketlab.db` local.
- Para correções de defeitos, escreva um teste que falhe antes da correção sempre
  que isso for viável.
- Toda alteração de migração deve ser testada a partir de um banco vazio.
- Todo endpoint que altera dados deve ter testes de sucesso, validação, ausência
  de recurso e rollback quando houver falha relevante.
- O frontend deve validar contratos em compile-time e testar os estados de
  carregamento, vazio, erro e sucesso dos fluxos principais.

## Disciplina de mudanças

- Faça alterações pequenas e coerentes com o requisito em andamento.
- Não edite o README antecipadamente. Atualize-o quando os comandos e fluxos
  descritos puderem ser executados e verificados.
- Preserve mudanças do usuário que não façam parte da tarefa atual.
- Não crie funcionalidades opcionais enquanto houver requisito obrigatório
  incompleto.
- Revise impacto em contratos, migrações, testes e documentação antes de aceitar
  uma alteração de domínio.
- Não execute `git add`, `git commit`, `git push`, criação de branch, rebase,
  reset, abertura de pull request ou alteração de remoto sem pedido explícito
  do usuário. Mantenha as mudanças locais por padrão e dê assistência sobre o
  estado do desenvolvimento, impactos, verificações e próximos passos sem
  transformar a conversa em um relatório de operações Git.
