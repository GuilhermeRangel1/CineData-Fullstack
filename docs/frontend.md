# Interface e mídia — checkpoint da etapa 5

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

Os dados brutos preservam títulos e gêneros do arquivo original, inclusive
idiomas, datas futuras, notas e imagens indisponíveis. As categorias em português
na interface mapeiam os gêneros em inglês, sem modificar os registros.

Cadastro, edição, exclusão e envio de avaliações pela interface ainda serão
implementados. Este checkpoint não conclui toda a etapa 5.

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
visível ou ao abrir o trailer em janela própria. Com preferência por movimento
reduzido, começa estático; a pessoa pode iniciar a reprodução explicitamente.

A imagem permanece até o evento de reprodução. Bloqueio de autoplay, falha do
player ou tempo excedido mantêm a alternativa estática. Na janela do trailer há
um link para assistir diretamente na fonte oficial. Reprodução, imagens e
fontes dependem dos serviços externos e da conexão; bloqueadores ou restrições
do navegador podem impedir o vídeo.

## Verificações

Execute em `frontend/`: `npm run lint`, `npm run test` e `npm run build`.
Os testes com Vitest e Testing Library cobrem catálogo, filtros, paginação,
buscas fora de ordem, erros e nova tentativa, detalhes, pôster indisponível e
os estados e controles do player com a API externa simulada.

O checkpoint também foi inspecionado no navegador com a API real, em desktop
e em áreas de 390 e 320 pixels de largura. A reprodução do trailer oficial,
no fundo e na janela própria, e a abertura de detalhes foram verificadas.
