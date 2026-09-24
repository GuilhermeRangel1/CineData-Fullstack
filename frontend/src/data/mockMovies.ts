import type { FilmeResumo } from '../types/api'

export const mockMovies: FilmeResumo[] = [
  { id: '1', titulo: 'A Chegada', ano_lancamento: 2016, url_poster: null, url_backdrop: null, generos: [{ id: 'ficcao', nome: 'Ficção científica' }], nota_media: 9, quantidade_avaliacoes: 248 },
  { id: '2', titulo: 'Parasita', ano_lancamento: 2019, url_poster: null, url_backdrop: null, generos: [{ id: 'drama', nome: 'Drama' }, { id: 'suspense', nome: 'Suspense' }], nota_media: 9.6, quantidade_avaliacoes: 391 },
  { id: '3', titulo: 'Tudo em Todo Lugar ao Mesmo Tempo', ano_lancamento: 2022, url_poster: null, url_backdrop: null, generos: [{ id: 'aventura', nome: 'Aventura' }, { id: 'drama', nome: 'Drama' }], nota_media: 8.8, quantidade_avaliacoes: 176 },
  { id: '4', titulo: 'O Farol', ano_lancamento: 2019, url_poster: null, url_backdrop: null, generos: [{ id: 'terror', nome: 'Terror' }, { id: 'drama', nome: 'Drama' }], nota_media: 8.2, quantidade_avaliacoes: 92 },
]
