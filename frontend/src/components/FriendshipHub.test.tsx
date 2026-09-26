import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { FriendshipHub } from './FriendshipHub'
import { json, movie } from '../test/movie'
import type { UsuarioLeitura } from '../types/api'

const user: UsuarioLeitura = {
  id: 'ana',
  email: 'ana@example.com',
  nome: 'Ana',
  role: 'user',
  created_at: '2026-09-25T12:00:00Z',
  avatar_url: null,
}

it('pesquisa pessoas e administra pedidos e amizades sem recarregar a página', async () => {
  let friends: { id: string; nome: string; avatar_url: string | null }[] = []
  let requests = [{
    id: 'r-caio',
    status: 'pendente',
    direcao: 'recebida',
    pessoa: { id: 'caio', nome: 'Caio', avatar_url: null },
    criada_em: '2026-09-25T12:00:00Z',
  }]
  const fetcher = vi.fn((url: string, init?: RequestInit) => {
    const parsed = new URL(url)
    const path = parsed.pathname
    const method = init?.method ?? 'GET'
    if (path.endsWith('/amigos/solicitacoes') && method === 'GET') return json(requests)
    if (path.endsWith('/amigos') && method === 'GET') return json(friends)
    if (path.endsWith('/amigos/pesquisa')) return json(parsed.searchParams.get('busca') === 'Ca' ? [{ id: 'caio', nome: 'Caio', avatar_url: null }] : [{ id: 'bia', nome: 'Bia', avatar_url: null }])
    if (path.endsWith('/perfis/caio')) return json({
      id: 'caio',
      nome: 'Caio',
      avatar_url: null,
      quantidade_amigos: 4,
      comunidades: [{ id: 'c1', nome: 'Cinema brasileiro', descricao: 'Produções nacionais.' }],
      avaliacoes: Array.from({ length: 6 }, (_, index) => ({ id: `a${index}`, nome: 'Caio', nota: 9 - index, comentario: `Comentário ${index}`, criada_em: '2026-09-25T12:00:00Z', visibilidade: 'publica', filme: movie })),
      listas_publicas: [{ id: 'l1', nome: 'Favoritos', quantidade_filmes: 1, filmes: [movie] }],
    })
    if (path.endsWith('/amigos/solicitacoes/bia') && method === 'POST') {
      const created = { id: 'r-bia', status: 'pendente', direcao: 'enviada', pessoa: { id: 'bia', nome: 'Bia', avatar_url: null }, criada_em: '2026-09-25T12:10:00Z' }
      requests = [created, ...requests]
      return json(created, 201)
    }
    if (path.endsWith('/amigos/solicitacoes/caio') && method === 'POST') {
      const created = { id: 'r-caio-novo', status: 'pendente', direcao: 'enviada', pessoa: { id: 'caio', nome: 'Caio', avatar_url: null }, criada_em: '2026-09-25T12:20:00Z' }
      requests = [created, ...requests]
      return json(created, 201)
    }
    if (path.endsWith('/amigos/solicitacoes/r-caio') && method === 'PATCH') {
      const accepted = { ...requests.find((item) => item.id === 'r-caio')!, status: 'aceita' }
      requests = requests.map((item) => item.id === accepted.id ? accepted : item)
      friends = [accepted.pessoa]
      return json(accepted)
    }
    if (path.endsWith('/amigos/caio') && method === 'DELETE') {
      friends = []
      requests = requests.filter((item) => item.pessoa.id !== 'caio')
      return Promise.resolve(new Response(null, { status: 204 }))
    }
    throw new Error(`Requisição não esperada: ${method} ${path}`)
  })
  vi.stubGlobal('fetch', fetcher)
  render(<FriendshipHub usuario={user} onLoginRequested={vi.fn()} onOpenMovie={vi.fn()} />)

  await screen.findByRole('heading', { name: 'Pedidos recebidos' })
  expect(screen.getByLabelText('1 pedido pendente')).toHaveTextContent('1')
  const received = screen.getByRole('heading', { name: 'Pedidos recebidos' }).closest('section')!
  await userEvent.click(within(received).getByRole('button', { name: 'Ver perfil de Caio' }))
  const profile = await screen.findByRole('dialog', { name: 'Perfil de Caio' })
  expect(within(profile).getByText('Cinema brasileiro')).toBeInTheDocument()
  expect(within(profile).getByText('Favoritos')).toBeInTheDocument()
  expect(within(profile).getAllByRole('button', { name: /nota .* de 10/ })).toHaveLength(5)
  await userEvent.click(within(profile).getByRole('button', { name: 'Fechar' }))
  await userEvent.type(screen.getByLabelText('Encontrar pessoas'), 'Bi')
  await screen.findByRole('button', { name: 'Enviar pedido para Bia' })
  await userEvent.click(screen.getByRole('button', { name: 'Enviar pedido para Bia' }))
  expect(await screen.findByText('Pedido enviado')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Pedidos enviados' }).closest('section')).toHaveTextContent('1')

  await userEvent.click(within(received).getByRole('button', { name: 'Aceitar' }))
  const friendsSection = screen.getByRole('heading', { name: 'Amigos', level: 2 }).closest('section')!
  expect(await within(friendsSection).findByText('Caio')).toBeInTheDocument()
  await userEvent.click(within(friendsSection).getByRole('button', { name: 'Remover' }))
  await waitFor(() => expect(within(friendsSection).queryByText('Caio')).not.toBeInTheDocument())
  await userEvent.clear(screen.getByLabelText('Encontrar pessoas'))
  await userEvent.type(screen.getByLabelText('Encontrar pessoas'), 'Ca')
  const sendAgain = await screen.findByRole('button', { name: 'Enviar pedido para Caio' })
  expect(screen.queryByText('Responda ao pedido abaixo')).not.toBeInTheDocument()
  await userEvent.click(sendAgain)
  await waitFor(() => expect(fetcher).toHaveBeenCalledWith(expect.stringContaining('/amigos/solicitacoes/caio'), expect.objectContaining({ method: 'POST' })))
})

it('convida o visitante a entrar antes de abrir a rede', async () => {
  const login = vi.fn()
  render(<FriendshipHub usuario={null} onLoginRequested={login} onOpenMovie={vi.fn()} />)

  await userEvent.click(screen.getByRole('button', { name: 'Entrar para encontrar amigos' }))
  expect(login).toHaveBeenCalledOnce()
})

it('limita cada bloco a cinco itens e permite revelar a coleção completa', async () => {
  const friends = Array.from({ length: 7 }, (_, index) => ({ id: `f${index}`, nome: `Amigo ${index + 1}`, avatar_url: null }))
  const received = Array.from({ length: 6 }, (_, index) => ({ id: `r${index}`, status: 'pendente', direcao: 'recebida', pessoa: { id: `r-user${index}`, nome: `Recebido ${index + 1}`, avatar_url: null }, criada_em: '2026-09-25T12:00:00Z' }))
  const sent = Array.from({ length: 6 }, (_, index) => ({ id: `s${index}`, status: 'pendente', direcao: 'enviada', pessoa: { id: `s-user${index}`, nome: `Enviado ${index + 1}`, avatar_url: null }, criada_em: '2026-09-25T12:00:00Z' }))
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    const parsed = new URL(url)
    const path = parsed.pathname
    if (path.endsWith('/amigos/solicitacoes')) return json([...received, ...sent])
    if (path.endsWith('/amigos')) return json(friends)
    if (path.endsWith('/amigos/pesquisa')) return json(Array.from({ length: 7 }, (_, index) => ({ id: `p${index}`, nome: `Pessoa ${index + 1}`, avatar_url: null })))
    throw new Error(`Requisição não esperada: ${path}`)
  }))
  render(<FriendshipHub usuario={user} onLoginRequested={vi.fn()} onOpenMovie={vi.fn()} />)

  const receivedSection = (await screen.findByRole('heading', { name: 'Pedidos recebidos' })).closest('section')!
  expect(within(receivedSection).getAllByRole('button', { name: /Ver perfil de Recebido/ })).toHaveLength(5)
  expect(within(receivedSection).queryByText('Recebido 6')).not.toBeInTheDocument()
  await userEvent.click(within(receivedSection).getByRole('button', { name: 'Ver todos os pedidos recebidos (6)' }))
  expect(within(receivedSection).getByText('Recebido 6')).toBeInTheDocument()

  const sentSection = screen.getByRole('heading', { name: 'Pedidos enviados' }).closest('section')!
  expect(within(sentSection).getAllByRole('button', { name: /Ver perfil de Enviado/ })).toHaveLength(5)
  expect(within(sentSection).getByRole('button', { name: 'Ver todos os pedidos enviados (6)' })).toBeInTheDocument()

  const friendsSection = screen.getByRole('heading', { name: 'Amigos', level: 2 }).closest('section')!
  expect(within(friendsSection).getAllByRole('button', { name: /Ver perfil de Amigo/ })).toHaveLength(5)
  expect(within(friendsSection).getByRole('button', { name: 'Ver todos os amigos (7)' })).toBeInTheDocument()

  await userEvent.type(screen.getByLabelText('Encontrar pessoas'), 'Pe')
  await screen.findByRole('button', { name: 'Ver perfil de Pessoa 1' })
  const searchSection = screen.getByRole('heading', { name: 'Quem vai para a próxima sessão?' }).closest('section')!
  expect(within(searchSection).getAllByRole('button', { name: /Ver perfil de Pessoa/ })).toHaveLength(5)
  expect(within(searchSection).getByRole('button', { name: 'Ver todos os resultados da busca (7)' })).toBeInTheDocument()
})
