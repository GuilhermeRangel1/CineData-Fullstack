import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MovieDetail } from './MovieDetail'
import { MovieCard } from './MovieCard'
import type { FilmeDetalhe } from '../types/api'

const admin = {
  id: 'admin',
  email: 'admin@example.com',
  nome: 'Admin',
  role: 'admin' as const,
  created_at: '2026-09-25T12:00:00Z',
}

const user = { ...admin, id: 'user', email: 'ana@example.com', nome: 'Ana', role: 'user' as const }

const movie: FilmeDetalhe = {
  id: '1',
  titulo: 'A Chegada',
  ano_lancamento: 2016,
  url_poster: 'https://example.com/poster.jpg',
  url_backdrop: null,
  url_trailer: null,
  generos: [{ id: 'g', nome: 'Drama' }],
  nota_media: 8.5,
  quantidade_avaliacoes: 1,
  data_lancamento: '2016-11-10',
  duracao_minutos: 116,
  status_filme: null,
  sinopse: 'Uma linguista investiga um contato inesperado.',
  pessoas: [{ id: 'p', nome: 'Denis Villeneuve', papel: 'Diretor' }],
  produtoras: [],
  desempenho: null,
  avaliacoes: [
    { id: 'r', nome: 'Ana', nota: 8.5, comentario: 'Excelente.', criada_em: '2026-09-24T12:00:00' },
  ],
}
describe('Detalhes de um filme real', () => {
  it('mantém confirmação aberta após falha de exclusão e só fecha depois do 204', async () => {
    let deleteAttempts = 0
    const fetcher = vi.fn((url: string, init?: RequestInit) => {
      const path = new URL(url).pathname
      if (path.endsWith('/minha-conta/listas')) return Promise.resolve(new Response(JSON.stringify([])))
      if (init?.method === 'DELETE') {
        deleteAttempts += 1
        return deleteAttempts === 1
          ? Promise.resolve(new Response(JSON.stringify({ mensagem: 'Não foi possível excluir.' }), { status: 500 }))
          : Promise.resolve(new Response(null, { status: 204 }))
      }
      return Promise.resolve(new Response(JSON.stringify(movie)))
    })
    vi.stubGlobal('fetch', fetcher)
    const close = vi.fn(),
      deleted = vi.fn()
    render(<MovieDetail id="1" onClose={close} onDeleted={deleted} usuario={admin} />)
    await userEvent.click(await screen.findByRole('button', { name: 'Excluir filme' }))
    await userEvent.click(screen.getByRole('button', { name: 'Excluir definitivamente' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível excluir.')
    expect(close).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Excluir definitivamente' }))
    expect(deleted).toHaveBeenCalledOnce()
    expect(close).toHaveBeenCalledOnce()
  })

  it('distingue avaliação publicada de uma falha posterior ao atualizar detalhes', async () => {
    let movieReads = 0
    const fetcher = vi.fn((url: string, init?: RequestInit) => {
      const path = new URL(url).pathname
      if (path.endsWith('/minha-conta/listas')) return Promise.resolve(new Response(JSON.stringify([])))
      if (init?.method === 'POST' && path.endsWith('/avaliacoes')) {
        return Promise.resolve(new Response(JSON.stringify(movie.avaliacoes[0]), { status: 201 }))
      }
      if (path.endsWith('/filmes/1')) {
        movieReads += 1
        return movieReads === 2 ? Promise.reject(new TypeError('offline')) : Promise.resolve(new Response(JSON.stringify(movie)))
      }
      throw new Error(`Requisição inesperada: ${path}`)
    })
    vi.stubGlobal('fetch', fetcher)
    const changed = vi.fn()
    render(<MovieDetail id="1" onClose={vi.fn()} onChanged={changed} usuario={user} />)
    await screen.findByLabelText('Sua nota (0 a 10)')
    await userEvent.type(screen.getByLabelText('Sua nota (0 a 10)'), '8.5')
    fireEvent.change(screen.getByLabelText('Sua resenha'), { target: { value: 'Excelente.' } })
    await userEvent.click(screen.getByRole('button', { name: 'Publicar avaliação' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível conectar')
    expect(screen.getByRole('status')).toHaveTextContent('Avaliação publicada')
    await userEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    await screen.findByLabelText('Sua nota (0 a 10)')
    expect(changed).toHaveBeenCalledOnce()
    expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(1)
  })
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

  it('deixa a pessoa salvar o filme em uma lista escolhida', async () => {
    const list = { id: 'favoritos', nome: 'Favoritos', visibilidade: 'privada', quantidade_filmes: 0, capa_url: null, criada_em: '2026-09-26T00:00:00Z' }
    const fetcher = vi.fn((url: string, init?: RequestInit) => {
      const path = new URL(url).pathname
      if (path.endsWith('/minha-conta/listas') && !init?.method) return Promise.resolve(new Response(JSON.stringify([list])))
      if (init?.method === 'POST' && path.endsWith('/minha-conta/listas/favoritos/filmes/1')) {
        return Promise.resolve(new Response(JSON.stringify({ ...list, quantidade_filmes: 1, filmes: [movie] })))
      }
      if (path.endsWith('/filmes/1')) return Promise.resolve(new Response(JSON.stringify(movie)))
      throw new Error(`Requisição inesperada: ${path}`)
    })
    vi.stubGlobal('fetch', fetcher)

    render(<MovieDetail id="1" onClose={vi.fn()} usuario={user} />)
    await userEvent.selectOptions(await screen.findByLabelText('Escolha uma lista'), 'favoritos')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar na lista' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Adicionado a Favoritos.')
    expect(fetcher.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true)
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

  it('usa o pôster como imagem de detalhes quando o backdrop está ausente', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response(JSON.stringify(movie)))))
    const { container } = render(<MovieDetail id="1" onClose={vi.fn()} />)
    await screen.findByText(movie.sinopse!)
    const image = container.querySelector('.detail-cover img')!
    expect(image).toHaveAttribute('src', movie.url_poster)
    fireEvent.error(image)
    expect(container.querySelector('.detail-cover img')).not.toBeInTheDocument()
  })

  it('exibe o trailer do YouTube abaixo dos detalhes quando ele existe', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({ ...movie, url_trailer: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' })))),
    )
    render(<MovieDetail id="1" onClose={vi.fn()} />)
    expect(await screen.findByTitle('Trailer de A Chegada')).toHaveAttribute('src', expect.stringContaining('youtube-nocookie.com'))
    expect(screen.getByRole('heading', { name: 'Trailer oficial' })).toBeInTheDocument()
  })
})
