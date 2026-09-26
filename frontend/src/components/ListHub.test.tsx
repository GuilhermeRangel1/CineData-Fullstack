import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { ListHub } from './ListHub'
import { json } from '../test/movie'
import type { FilmeResumo, ListaDetalhe, UsuarioLeitura } from '../types/api'

const user: UsuarioLeitura = {
  id: 'user-1', email: 'ana@example.com', nome: 'Ana', role: 'user', created_at: '2026-09-26T00:00:00Z',
}
const movie: FilmeResumo = {
  id: 'movie-1', titulo: 'Filme encontrado', ano_lancamento: 2024, url_poster: 'https://example.com/poster.jpg', url_backdrop: null,
  generos: [], nota_media: null, quantidade_avaliacoes: 0,
}
const list = { id: 'list-1', nome: 'Favoritos', visibilidade: 'privada' as const, quantidade_filmes: 0, capa_url: 'https://example.com/poster.jpg', criada_em: '2026-09-26T00:00:00Z' }

it('permite adicionar e remover filmes de uma lista pessoal', async () => {
  let detail: ListaDetalhe = { ...list, filmes: [] }
  const fetcher = vi.fn((url: string, init?: RequestInit) => {
    const path = new URL(url).pathname
    if (path.endsWith('/minha-conta/listas') && !init?.method) return json([list])
    if (path.endsWith('/minha-conta/assistir-depois') || path.endsWith('/minha-conta/filmes-avaliados')) return json([])
    if (path.endsWith('/minha-conta/listas/list-1') && !init?.method) return json(detail)
    if (path.endsWith('/filmes')) return json({ itens: [movie], meta: { pagina: 1, tamanho_pagina: 6, total_itens: 1, total_paginas: 1 } })
    if (init?.method === 'POST') {
      detail = { ...list, quantidade_filmes: 1, filmes: [movie] }
      return json(detail)
    }
    if (init?.method === 'DELETE') return Promise.resolve(new Response(null, { status: 204 }))
    throw new Error(`Requisição inesperada: ${path}`)
  })
  vi.stubGlobal('fetch', fetcher)

  const { container } = render(<ListHub usuario={user} onLoginRequested={vi.fn()} onOpenMovie={vi.fn()} />)
  await userEvent.click(await screen.findByRole('button', { name: 'Abrir lista Favoritos' }))
  await userEvent.type(screen.getByLabelText('Adicionar um filme'), 'filme')
  await userEvent.click(await screen.findByRole('button', { name: /Adicionar/ }))
  expect((await screen.findAllByText('Filme encontrado')).length).toBeGreaterThan(0)
  expect(container.querySelector('.list-movie-card img')).toHaveAttribute('src', movie.url_poster)

  await userEvent.click(screen.getByRole('button', { name: 'Remover da lista' }))
  await waitFor(() => expect(fetcher.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(true))
})

it('convida visitantes a entrar antes de mostrar dados privados', async () => {
  const login = vi.fn()
  render(<ListHub usuario={null} onLoginRequested={login} onOpenMovie={vi.fn()} />)
  await userEvent.click(screen.getByRole('button', { name: 'Entrar para organizar filmes' }))
  expect(screen.getByText('Suas listas começam aqui.')).toBeInTheDocument()
  expect(login).toHaveBeenCalledOnce()
})
