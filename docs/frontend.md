# Interface e mídia — etapa 5

O frontend usa React, TypeScript e CSS, com componentes separados para destaque,
fileiras, cards, catálogo e detalhes. O cliente HTTP fica em
`frontend/src/api/client.ts`, usando `VITE_API_BASE_URL`
(padrão: `http://localhost:8000/api/v1`).

## Fluxos disponíveis

- Catálogo real com busca por título, filtro por gênero, ordenação e paginação.
- Fileiras de animação e aventura, também consultadas na API.
- Detalhes em `dialog` nativo: sinopse, pessoas, produtoras, desempenho, média
  e histórico. Escape fecha a janela e devolve o foco.
- Estados de carregamento, vazio, erro e nova tentativa. Buscas antigas são
  canceladas para evitar que uma resposta atrasada substitua a atual.
- Pôsteres ausentes ou quebrados recebem uma apresentação com o título.
- O catálogo prioriza filmes com pôster ou backdrop, sem omitir registros sem
  imagem. Quando um pôster não existe, o card usa o backdrop como alternativa;
  nos detalhes, o pôster também substitui um backdrop ausente.
- Respostas de catálogo e detalhes são mantidas por até um minuto no cache em
  memória do cliente. Qualquer cadastro, edição, exclusão ou avaliação limpa
  esse cache antes de as consultas serem atualizadas, evitando dados obsoletos.
- Cadastro, login e encerramento de sessão locais pelo cabeçalho. A sessão JWT
  é mantida no navegador e enviada nas escritas da API.
- O botão **Adicionar filme**, a edição e a exclusão ficam visíveis apenas para
  administradores. O formulário oferece título, diretor, ano, gêneros, sinopse,
  data completa e links opcionais de imagens.
- Edição via PATCH envia apenas campos alterados. Elenco, produtoras e demais
  relações não editadas são preservados. Se houver vários diretores, a interface
  avisa que alterar esse campo substitui a direção pelo único nome informado.
- Exclusão exige confirmação e informa que avaliações também serão removidas.
- Avaliação com a identidade da conta, nota de 0 a 10 (seletor em intervalos de
  0,5) e resenha. Sem sessão, a interface convida a pessoa a entrar. Catálogo,
  coleções, histórico e média são consultados novamente após escritas.
- Campos inválidos recebem mensagens; falhas de escrita preservam o formulário.
  Durante o envio, controles e fechamento da janela ficam bloqueados para
  evitar requisições duplicadas. Uma falha de atualização posterior não é
  apresentada como falha de gravação de uma avaliação já confirmada pela API.

Os dados brutos preservam títulos e gêneros do arquivo original, inclusive
idiomas, datas futuras, notas e imagens indisponíveis. As categorias em português
na interface mapeiam os gêneros em inglês, sem modificar os registros.

O formulário e suas conversões/validações estão separados em `MovieForm` e
`lib/movieForm.ts`. `useMutation` coordena bloqueio de envio e erros; `useResource`
invalida consultas após alterações, preservando filtros e ordenação do catálogo.
Ao remover o último item de uma página, a navegação retorna à última página válida.
Dados são persistidos pela API, não em armazenamento local do navegador.

## Destaque editorial

O Castelo Animado não foi encontrado no seed local. Ele aparece como seleção
editorial, sem nota inventada ou ligação a um registro inexistente. O botão
Explorar animações abre o filtro correspondente no catálogo real.

- Trailer: [GKIDS, trailer oficial](https://www.youtube.com/watch?v=2x5SejvTMeA).
- Imagem: [galeria oficial do Studio Ghibli](https://www.ghibli.jp/works/howl/),
  quadro `howl003.jpg`.
- Créditos: © 2004 Diana Wynne Jones / Hayao Miyazaki / Studio Ghibli, NDDMT.
- Fontes: Manrope e Barlow Condensed, servidas pelo Google Fonts, com
  alternativas locais em CSS.

O trailer usa a API oficial de iframe do YouTube e o domínio
`youtube-nocookie.com`; nenhum vídeo foi baixado ou versionado. O destaque tenta
reproduzir sem som, permite pausa e controle de áudio e pausa ao sair da área
visível ou ao abrir uma janela de detalhes, cadastro ou trailer. Com preferência por movimento
reduzido, começa estático; a pessoa pode iniciar a reprodução explicitamente.

A imagem permanece até o evento de reprodução. Bloqueio de autoplay, falha do
player ou tempo excedido mantêm a alternativa estática. Na janela do trailer há
um link para assistir diretamente na fonte oficial. Reprodução, imagens e
fontes dependem dos serviços externos e da conexão; bloqueadores ou restrições
do navegador podem impedir o vídeo.

## Verificações

Execute em `frontend/`: `npm run lint`, `npm run test` e `npm run build`.
Os 30 testes com Vitest e Testing Library cobrem catálogo, filtros, paginação,
buscas fora de ordem, erros e nova tentativa, detalhes, pôster indisponível e
os estados e controles do player com a API externa simulada. Também cobrem
cadastro, PATCH mínimo, campos opcionais apagados com null, validação antes do
envio, prevenção de envio duplicado, preservação de texto em falhas, notas 0 e 10,
confirmação/cancelamento/falha de exclusão e atualização das três listas após
alterações. O fluxo integrado completo usa respostas HTTP simuladas no Vitest.

A interface foi inspecionada no navegador em desktop e áreas de 390 e 320 pixels,
incluindo formulários, confirmação, foco inicial e retorno por Escape. Cadastro,
edição e envio de avaliação foram executados com a API real sobre banco isolado
criado pelo Alembic; média e histórico foram conferidos. A limpeza desse registro
pela API retornou 204, e sua ausência gerou a mensagem de 404 esperada na interface.
A execução do botão de exclusão é coberta no teste integrado do frontend;
a confirmação visual foi inspecionada sem remover registros da base importada.
O trailer oficial, no fundo e na janela própria, já havia sido verificado no
checkpoint visual. A revisão final de entrega permanece na etapa 6.
