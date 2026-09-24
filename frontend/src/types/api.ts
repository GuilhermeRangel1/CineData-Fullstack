export type PapelPessoa = 'Ator' | 'Diretor' | 'Roteirista'
export type OrdenacaoFilme = 'titulo' | 'ano_lancamento'
export type DirecaoOrdenacao = 'asc' | 'desc'

export interface ErroApi {
  codigo: string
  mensagem: string
}

export interface MetadadosPagina {
  pagina: number
  tamanho_pagina: number
  total_itens: number
  total_paginas: number
}

export interface Pagina<T> {
  itens: T[]
  meta: MetadadosPagina
}

export interface GeneroResumo {
  id: string
  nome: string
}

export interface ProdutoraResumo {
  id: string
  nome: string
}

export interface PessoaResumo {
  id: string
  nome: string
  papel: PapelPessoa
}

export interface AvaliacaoCriacao {
  nome: string
  nota: number
  comentario: string
}

export interface AvaliacaoLeitura extends AvaliacaoCriacao {
  id: string
  criada_em: string
}

export interface DesempenhoFilme {
  orcamento_usd: number | null
  receita_usd: number | null
  lucro_usd: number | null
  orcamento_brl: number | null
  receita_brl: number | null
  lucro_brl: number | null
  popularidade: number | null
  nota_tmdb: number | null
  quantidade_tmdb: number | null
  nota_imdb: number | null
  quantidade_imdb: number | null
}

export interface FilmeCriacao {
  titulo: string
  diretor: string
  ano_lancamento?: number
  generos: string[]
  sinopse?: string
  data_lancamento?: string
  duracao_minutos?: number
  status_filme?: string
  url_poster?: string
  url_backdrop?: string
  atores?: string[]
  roteiristas?: string[]
  produtoras?: string[]
}

export type FilmeAtualizacao = Partial<
  Pick<FilmeCriacao, 'titulo' | 'diretor' | 'generos' | 'atores' | 'roteiristas' | 'produtoras'>
> & {
  [
    K in
      | 'ano_lancamento'
      | 'sinopse'
      | 'data_lancamento'
      | 'duracao_minutos'
      | 'status_filme'
      | 'url_poster'
      | 'url_backdrop'
  ]?: FilmeCriacao[K] | null
}

export interface FilmeResumo {
  id: string
  titulo: string
  ano_lancamento: number | null
  url_poster: string | null
  url_backdrop: string | null
  generos: GeneroResumo[]
  nota_media: number | null
  quantidade_avaliacoes: number
}

export interface FilmeDetalhe extends FilmeResumo {
  data_lancamento: string | null
  duracao_minutos: number | null
  status_filme: string | null
  sinopse: string | null
  url_backdrop: string | null
  pessoas: PessoaResumo[]
  produtoras: ProdutoraResumo[]
  desempenho: DesempenhoFilme | null
  avaliacoes: AvaliacaoLeitura[]
}

export interface ConsultaCatalogo {
  busca?: string
  genero?: string
  pagina?: number
  tamanho_pagina?: number
  ordenar_por?: OrdenacaoFilme
  direcao?: DirecaoOrdenacao
  priorizar_capa?: boolean
}
