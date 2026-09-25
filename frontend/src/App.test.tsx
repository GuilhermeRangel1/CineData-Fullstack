import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import App from './App'
import { json, movie } from './test/movie'
import type { FilmeDetalhe } from './types/api'

vi.mock('./components/Hero', () => ({ Hero: () => <div>Destaque editorial</div> }))

it('completa cadastro, edição, avaliação e exclusão atualizando todas as listas sem recarregar a página', async () => {
  let current: FilmeDetalhe | null = null
  const fetcher = vi.fn((url: string, init?: RequestInit) => {
    const path = new URL(url).pathname
    const body = init?.body ? JSON.parse(String(init.body)) : {}
    if (init?.method === 'POST' && path.endsWith('/avaliacoes')) {
      const review = { ...body, id: 'r', criada_em: '2026-09-24T12:00:00Z' }
      current = {
        ...current!,
        avaliacoes: [review],
        nota_media: body.nota,
        quantidade_avaliacoes: 1,
      }
      return json(review, 201)
    }
    if (init?.method === 'POST') {
      current = {
        ...movie,
        ...body,
        generos: body.generos.map((nome: string, index: number) => ({ id: String(index), nome })),
      }
      return json(current, 201)
    }
    if (init?.method === 'PATCH') {
      current = { ...current!, ...body }
      return json(current)
    }
    if (init?.method === 'DELETE') {
      current = null
      return Promise.resolve(new Response(null, { status: 204 }))
    }
    if (path.endsWith('/filmes'))
      return json({
        itens: current ? [current] : [],
        meta: {
          pagina: 1,
          tamanho_pagina: 12,
          total_itens: current ? 1 : 0,
          total_paginas: current ? 1 : 0,
        },
      })
    return json(current)
  })
  vi.stubGlobal('fetch', fetcher)
  window.localStorage.setItem(
    'cinedata.session',
    JSON.stringify({
      token: 'token-de-teste',
      usuario: {
        id: 'admin',
        email: 'admin@example.com',
        nome: 'Admin',
        role: 'admin',
        created_at: '2026-09-25T12:00:00Z',
      },
    }),
  )
  render(<App />)
  await screen.findByText('Nenhuma história por aqui. Ainda.')
  await userEvent.click(screen.getByRole('button', { name: /Adicionar filme/ }))
  fireEvent.change(screen.getByLabelText('Título *'), { target: { value: 'Nova história' } })
  fireEvent.change(screen.getByLabelText('Diretor *'), { target: { value: 'Cineasta' } })
  fireEvent.change(screen.getByLabelText('Gêneros *'), { target: { value: 'Animation' } })
  await userEvent.click(screen.getByRole('button', { name: 'Cadastrar filme' }))
  let detail = await screen.findByRole('dialog', { name: 'Nova história' })
  await userEvent.click(within(detail).getByRole('button', { name: 'Editar filme' }))
  fireEvent.change(screen.getByLabelText('Título *'), { target: { value: 'História revisada' } })
  await userEvent.click(screen.getByRole('button', { name: 'Salvar alterações' }))
  detail = await screen.findByRole('dialog', { name: 'História revisada' })
  await waitFor(() =>
    expect(
      screen.getAllByRole('button', { name: 'Ver detalhes de História revisada' }),
    ).toHaveLength(3),
  )
  await userEvent.selectOptions(within(detail).getByLabelText('Sua nota (0 a 10)'), '10')
  fireEvent.change(within(detail).getByLabelText('Sua resenha'), {
    target: { value: 'Uma ótima sessão.' },
  })
  await userEvent.click(within(detail).getByRole('button', { name: 'Publicar avaliação' }))
  await screen.findByText('Uma ótima sessão.')
  await waitFor(() => expect(screen.getAllByLabelText('Média 10.0 de 10')).toHaveLength(3))
  await userEvent.click(screen.getByRole('button', { name: 'Excluir filme' }))
  await userEvent.click(screen.getByRole('button', { name: 'Manter filme' }))
  expect(fetcher.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false)
  await userEvent.click(screen.getByRole('button', { name: 'Excluir filme' }))
  await userEvent.click(screen.getByRole('button', { name: 'Excluir definitivamente' }))
  await screen.findByText('Filme e avaliações excluídos.')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(await screen.findByText('Nenhuma história por aqui. Ainda.')).toBeInTheDocument()
  expect(fetcher.mock.calls.filter(([, init]) => init?.method === 'DELETE')).toHaveLength(1)
})
