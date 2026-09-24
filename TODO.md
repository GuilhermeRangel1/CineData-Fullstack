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
- [ ] Implementar catálogo paginado, com ordem determinística e metadados de
      página suficientes para a interface.
- [ ] Implementar busca textual por título, combinável com a paginação.
- [ ] Implementar consulta de detalhes com gêneros, pessoas, desempenho,
      avaliações e média.
- [ ] Implementar atualização parcial e remoção individual, retornando 404 para
      recurso inexistente.
- [ ] Prevenir consultas N+1 e validar limites de paginação, textos e datas.
- [ ] Padronizar respostas de erro, logs úteis sem dados sensíveis e rollback
      em qualquer falha de escrita.

**Critério de saída:** CRUD, busca, paginação e detalhes possuem testes de API
para sucesso, validação, recurso inexistente e falha transacional relevante.

## 4. Backend: avaliações e média

- [ ] Implementar a criação e listagem do histórico de avaliações por filme.
- [ ] Receber, validar e apresentar notas na escala de 0 a 10.
- [ ] Manter a escala de 0 a 10 de forma consistente entre API, banco e CSVs,
      sem alterar os arquivos brutos.
- [ ] Calcular ou atualizar a média de avaliações com consistência após cada
      inserção, sem divergência entre detalhes e catálogo.
- [ ] Validar nota, autor e resenha, e manter a integridade referencial ao
      excluir filmes.

**Critério de saída:** testes cobrem limites de nota na escala de 0 a 10,
histórico, média e comportamento após exclusão de filme.

## 5. Frontend: fluxos obrigatórios

- [ ] Criar páginas para catálogo, detalhes do filme e gestão de filmes.
- [ ] Implementar busca, paginação e estados de carregamento, vazio e erro no
      catálogo.
- [ ] Implementar formulário de criação e edição com validação clara antes de
      enviar à API.
- [ ] Implementar exclusão com confirmação e feedback de sucesso ou falha.
- [ ] Exibir detalhes completos, média de 0 a 10 e histórico de avaliações.
- [ ] Implementar formulário para nova avaliação, com seletor de 0 a 10 e
      resenha.
- [ ] Garantir navegação por teclado, rótulos de formulário, contraste e uso
      adequado em telas móveis e desktop.

**Critério de saída:** todos os requisitos obrigatórios podem ser realizados
pela interface usando a API real, inclusive em estados sem dados e com erro.

## 6. Qualidade, robustez e entrega

- [ ] Aumentar a cobertura dos fluxos críticos no backend e no frontend,
      priorizando regras de negócio, falhas e regressões.
- [ ] Executar lint, typecheck, testes, build do frontend e migrações em uma
      sequência reproduzível.
- [ ] Revisar CORS para aceitar somente as origens locais necessárias e nunca
      retornar detalhes internos em mensagens de erro.
- [ ] Revisar desempenho das rotas de catálogo e detalhes com o volume dos CSVs.
- [ ] Documentar arquitetura, comandos de instalação, carga de dados, execução,
      testes e limitações no README apenas após validá-los.
- [ ] Revisar o diff final, confirmar que `.env`, bancos locais, dependências e
      builds não estão versionados, e separar commits por assunto.

**Critério de saída:** os comandos documentados funcionam em clone limpo e a
aplicação atende todos os requisitos obrigatórios de ponta a ponta.

## Após o MVP, apenas se solicitado

- [ ] Autenticação e autorização.
- [ ] Filtros avançados, favoritos, recomendações e integrações externas.
- [ ] Storybook, cache, métricas externas, CI/CD e deploy.
