import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MovieDetail } from './MovieDetail'
import { MovieCard } from './MovieCard'
import type { FilmeDetalhe } from '../types/api'

const movie: FilmeDetalhe = {
  id: '1',
  titulo: 'A Chegada',
  ano_lancamento: 2016,
  url_poster: 'https://example.com/poster.jpg',
  generos: [{ id: 'g', nome: 'Drama' }],
  nota_media: 8.5,
  quantidade_avaliacoes: 1,
  data_lancamento: '2016-11-10',
  duracao_minutos: 116,
  status_filme: null,
  sinopse: 'Uma linguista investiga um contato inesperado.',
  url_backdrop: null,
  pessoas: [{ id: 'p', nome: 'Denis Villeneuve', papel: 'Diretor' }],
  produtoras: [],
  desempenho: null,
  avaliacoes: [
    { id: 'r', nome: 'Ana', nota: 8.5, comentario: 'Excelente.', criada_em: '2026-09-24T12:00:00' },
  ],
}
describe('Detalhes de um filme real', () => {
  it('exibe sinopse, pessoas, média e histórico e permite fechar', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response(JSON.stringify(movie)))),
    )
    const close = vi.fn()
    render(<MovieDetail id="1" onClose={close} />)
    expect(await screen.findByText(movie.sinopse!)).toBeInTheDocument()
    expect(screen.getByText('Denis Villeneuve')).toBeInTheDocument()
    expect(screen.getByText('Excelente.')).toBeInTheDocument()
    expect(screen.getByText('8.5 / 10')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Fechar' }))
    expect(close).toHaveBeenCalled()
  })

  it('mostra um erro seguro para filme inexistente', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve(
          new Response(
            JSON.stringify({ codigo: 'FILME_NAO_ENCONTRADO', mensagem: 'Filme não encontrado.' }),
            { status: 404 },
          ),
        ),
      ),
    )
    render(<MovieDetail id="missing" onClose={vi.fn()} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Filme não encontrado.')
  })

  it('substitui pôster quebrado pelo título sem perder o acesso aos detalhes', async () => {
    const open = vi.fn()
    const { container } = render(<MovieCard movie={movie} onOpen={open} />)
    fireEvent.error(container.querySelector('img')!)
    expect(screen.getByText('Pôster indisponível')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Ver detalhes de A Chegada' }))
    expect(open).toHaveBeenCalledWith('1')
  })
})
