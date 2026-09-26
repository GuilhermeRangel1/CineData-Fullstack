import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { CommunityHub } from './CommunityHub'
import { json, movie } from '../test/movie'
import type { PublicacaoComunidade, UsuarioLeitura } from '../types/api'

const user: UsuarioLeitura = {
  id: 'ana',
  email: 'ana@example.com',
  nome: 'Ana',
  role: 'user',
  created_at: '2026-09-25T12:00:00Z',
  avatar_url: null,
}

it('permite entrar, mencionar filme, publicar, comentar e reagir', async () => {
  let joined = false
  let sendAttempts = 0
  let posts: PublicacaoComunidade[] = []
  let resolveReaction: ((response: Response) => void) | null = null
  const fetcher = vi.fn((url: string, init?: RequestInit) => {
    const parsed = new URL(url)
    const path = parsed.pathname
    const method = init?.method ?? 'GET'
    const body = init?.body ? JSON.parse(String(init.body)) : {}

    if (path.endsWith('/comunidades') && method === 'GET') {
      return json([
        {
          id: 'c1',
          nome: 'Animação',
          descricao: 'Conversas sobre cinema animado.',
          quantidade_membros: joined ? 1 : 0,
          criada_em: '2026-09-25T12:00:00Z',
        },
      ])
    }
    if (path.endsWith('/comunidades/c1/membros')) return json(joined ? [user] : [])
    if (path.endsWith('/visualizacoes')) return json({ id: 'c1', nome: 'Animação', descricao: 'Conversas sobre cinema animado.', quantidade_membros: 1, visualizacoes: 1 })
    if (path.endsWith('/comunidades/c1/publicacoes') && method === 'GET') return json(posts)
    if (path.endsWith('/comunidades/c1/participacao') && method === 'POST') {
      joined = true
      return Promise.resolve(new Response(null, { status: 204 }))
    }
    if (path.endsWith('/filmes') && parsed.searchParams.has('busca')) {
      return json({ itens: [movie], meta: { pagina: 1, tamanho_pagina: 5, total_itens: 1, total_paginas: 1 } })
    }
    if (path.endsWith('/comunidades/c1/publicacoes') && method === 'POST') {
      sendAttempts += 1
      if (sendAttempts === 1) return json({ codigo: 'INDISPONIVEL', mensagem: 'Falha temporária no envio.' }, 503)
      const created: PublicacaoComunidade = {
        id: 'p1',
        comunidade_id: 'c1',
        conteudo: body.conteudo,
        autor: { id: user.id, nome: user.nome, avatar_url: null },
        filme: body.movie_id ? movie : null,
        comentarios: [],
        reacoes: [],
        criada_em: '2026-09-25T12:10:00Z',
      }
      posts = [created]
      return json(created, 201)
    }
    if (path.endsWith('/comentarios') && method === 'POST') {
      const comment = {
        id: 'comment-1',
        conteudo: body.conteudo,
        autor: { id: user.id, nome: user.nome, avatar_url: null },
        criado_em: '2026-09-25T12:11:00Z',
      }
      posts = [{ ...posts[0], comentarios: [comment] }]
      return json(comment, 201)
    }
    if (path.endsWith('/reacoes') && method === 'POST') {
      const reactions = [{ tipo: body.tipo, quantidade: 1 }]
      posts = [{ ...posts[0], reacoes: reactions }]
      return new Promise<Response>((resolve) => { resolveReaction = resolve })
    }
    throw new Error(`Requisição não esperada: ${method} ${path}`)
  })
  vi.stubGlobal('fetch', fetcher)
  const intervalSpy = vi.spyOn(window, 'setInterval')

  render(
    <CommunityHub
      usuario={user}
      onLoginRequested={vi.fn()}
      onOpenMovie={vi.fn()}
    />,
  )

  expect(await screen.findAllByText('Conversas sobre cinema animado.')).toHaveLength(1)
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Entrar em Animação' }))
  await waitFor(() => expect(intervalSpy).toHaveBeenCalledWith(expect.any(Function), 5_000))
  await screen.findByLabelText('Mensagem')

  await userEvent.type(screen.getByLabelText('Mensagem'), 'Uma animação inesquecível.')
  await userEvent.click(screen.getByRole('button', { name: '+ Mencionar filme' }))
  await userEvent.type(screen.getByLabelText('Buscar filme do catálogo'), 'Castelo')
  await userEvent.click(await screen.findByRole('button', { name: /Uma história/ }))
  expect(screen.getByText('FILME SELECIONADO')).toBeInTheDocument()
  expect(screen.getByText('2004')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: /Enviar mensagem/ }))

  expect(await screen.findByRole('alert')).toHaveTextContent('Falha temporária no envio.')
  expect(screen.getByLabelText('Mensagem')).toHaveValue('Uma animação inesquecível.')
  expect(screen.getByRole('button', { name: 'Remover filme' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: /Enviar mensagem/ }))

  expect(await screen.findByText('Uma animação inesquecível.')).toBeInTheDocument()
  expect(screen.getByText('FILME MENCIONADO')).toBeInTheDocument()
  await userEvent.click(screen.getByText('Responder', { selector: 'summary' }))
  await userEvent.type(screen.getByLabelText('Responder à mensagem de Ana'), 'Também adorei.')
  await userEvent.click(screen.getByRole('button', { name: 'Responder' }))
  expect(await screen.findByText('Também adorei.')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Amei' }))
  expect(screen.getByRole('button', { name: /Enviar mensagem/ })).toHaveTextContent('Enviar mensagem')
  expect(screen.queryByText('Enviando…')).not.toBeInTheDocument()
  await act(async () => { resolveReaction?.(await json([{ tipo: 'amei', quantidade: 1 }])) })
  await waitFor(() => expect(screen.getByRole('button', { name: 'Amei · 1' })).toBeInTheDocument())
})

it('oferece login ao visitante que tenta participar', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      const path = new URL(url).pathname
      if (path.endsWith('/comunidades')) {
        return json([{ id: 'c1', nome: 'Drama', descricao: 'Debates.', quantidade_membros: 0, criada_em: '2026-09-25T12:00:00Z' }])
      }
      if (path.endsWith('/membros') || path.endsWith('/publicacoes')) return json([])
      if (path.endsWith('/visualizacoes')) return json({ id: 'c1', nome: 'Drama', descricao: 'Debates.', quantidade_membros: 0, visualizacoes: 1 })
      throw new Error(`Requisição não esperada: ${path}`)
    }),
  )
  const login = vi.fn()
  render(<CommunityHub usuario={null} onLoginRequested={login} onOpenMovie={vi.fn()} />)

  await userEvent.click(await screen.findByRole('button', { name: 'Entrar em Drama' }))
  await userEvent.click(await screen.findByRole('button', { name: 'Entrar com sua conta' }))
  expect(login).toHaveBeenCalledOnce()
})

it('mostra as quatro mais vistas e revela mais comunidades sem abrir a conversa', async () => {
  vi.stubGlobal('fetch', vi.fn(() => json(Array.from({ length: 7 }, (_, i) => ({ id: `c${i}`, nome: `Comunidade ${i}`, descricao: 'Cinema', visualizacoes: i, quantidade_membros: 0, criada_em: '2026-09-25T12:00:00Z' })))))
  render(<CommunityHub usuario={null} onLoginRequested={vi.fn()} onOpenMovie={vi.fn()} />)
  await screen.findByRole('heading', { name: 'Mais vistas' })
  expect(screen.getAllByRole('button', { name: /Entrar em/ }).map((button) => button.getAttribute('aria-label'))).toEqual(['Entrar em Comunidade 6', 'Entrar em Comunidade 5', 'Entrar em Comunidade 4', 'Entrar em Comunidade 3'])
  await userEvent.click(screen.getByRole('button', { name: /Ver mais/ }))
  expect(screen.getAllByRole('button', { name: /Entrar em/ })).toHaveLength(7)
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
  expect(screen.queryByRole('button', { name: /Ver mais/ })).not.toBeInTheDocument()
})

it('recebe novas mensagens, abre o perfil público e interrompe a consulta ao fechar', async () => {
  let messages: PublicacaoComunidade[] = []
  const fetcher = vi.fn((url: string) => {
    const path = new URL(url).pathname
    if (path.endsWith('/comunidades')) return json([{ id: 'c1', nome: 'Drama', descricao: 'Debates.', quantidade_membros: 1, visualizacoes: 0 }])
    if (path.endsWith('/visualizacoes')) return json({ id: 'c1', nome: 'Drama', descricao: 'Debates.', quantidade_membros: 1, visualizacoes: 1 })
    if (path.endsWith('/membros')) return json([user])
    if (path.endsWith('/publicacoes')) return json(messages)
    if (path.endsWith('/perfis/ana')) return json({ ...user, quantidade_amigos: 3, avaliacoes: [], listas_publicas: [], comunidades: [] })
    throw new Error(path)
  })
  vi.stubGlobal('fetch', fetcher)
  const interval = vi.spyOn(window, 'setInterval')
  const clear = vi.spyOn(window, 'clearInterval')
  render(<CommunityHub usuario={null} onLoginRequested={vi.fn()} onOpenMovie={vi.fn()} />)
  await userEvent.click(await screen.findByRole('button', { name: 'Entrar em Drama' }))
  await screen.findByText('A conversa começa com um oi.')
  messages = [{ id: 'p2', comunidade_id: 'c1', conteudo: 'Mensagem de outra pessoa', autor: { id: user.id, nome: user.nome, avatar_url: '/avatar.png' }, filme: null, comentarios: [], reacoes: [], criada_em: '2026-09-25T12:10:00Z' }]
  await act(async () => { const callback = interval.mock.calls.find((call) => call[1] === 5000)?.[0] as () => void; callback() })
  expect(await screen.findByText('Mensagem de outra pessoa')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Ver perfil de Ana' }))
  const profile = screen.getByRole('dialog', { name: 'Perfil de Ana' })
  expect((await within(profile).findByText('amigos')).parentElement).toHaveTextContent('3')
  await userEvent.click(within(profile).getByRole('button', { name: 'Fechar' }))
  expect(screen.getByText('Mensagem de outra pessoa')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Fechar' }))
  expect(clear).toHaveBeenCalled()
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})
