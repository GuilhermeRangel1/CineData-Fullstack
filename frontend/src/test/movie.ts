import type { FilmeDetalhe } from '../types/api'

export const movie: FilmeDetalhe = {
  id: 'test-movie',
  titulo: 'Uma história',
  ano_lancamento: 2004,
  url_poster: null,
  url_backdrop: null,
  url_trailer: null,
  generos: [{ id: 'g', nome: 'Animation' }],
  nota_media: null,
  quantidade_avaliacoes: 0,
  data_lancamento: '2004-11-20',
  duracao_minutos: 119,
  status_filme: null,
  sinopse: 'Uma viagem inesperada.',
  pessoas: [
    { id: 'd1', nome: 'Diretor original', papel: 'Diretor' },
    { id: 'd2', nome: 'Outra diretora', papel: 'Diretor' },
  ],
  produtoras: [{ id: 'company', nome: 'Estúdio original' }],
  desempenho: null,
  avaliacoes: [],
}

export function json(value: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(value), { status }))
}
