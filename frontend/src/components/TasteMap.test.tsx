import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { TasteMap } from './TasteMap'
import { json } from '../test/movie'

it('exibe a malha, explica uma sugestão e abre o filme selecionado', async () => {
  const fetcher = vi.fn(() => json({
    total_avaliados: 1,
    limite_nos: 24,
    vizinhos_por_filme: 3,
    nos: [
      { id: 'avaliado', titulo: 'Filme avaliado', ano_lancamento: 2020, url_poster: null, genero_principal: 'Drama', generos: ['Drama'], nota_usuario: 9, tipo: 'avaliado', afinidade: null },
      { id: 'sugestao', titulo: 'Filme sugerido', ano_lancamento: 2022, url_poster: null, genero_principal: 'Drama', generos: ['Drama'], nota_usuario: null, tipo: 'recomendado', afinidade: 0.81 },
    ],
    arestas: [{ origem: 'avaliado', destino: 'sugestao', peso: 0.81, explicacao: 'Conexão por gênero Drama' }],
  }))
  vi.stubGlobal('fetch', fetcher)
  const openMovie = vi.fn()
  const user = userEvent.setup()

  render(<TasteMap onOpenMovie={openMovie} />)

  expect(await screen.findByRole('button', { name: 'Abrir Filme sugerido' })).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Abrir Filme sugerido' }))
  expect(screen.getByText('Conexão por gênero Drama', { selector: 'small' })).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: /Ver filme/ }))
  expect(openMovie).toHaveBeenCalledWith('sugestao')

  await user.click(screen.getByRole('button', { name: /Atualizar mapa/ }))
  await waitFor(() => expect(fetcher).toHaveBeenLastCalledWith(
    expect.stringContaining('excluir=sugestao'),
    expect.any(Object),
  ))
})

it('troca as sugestões ao atualizar e pesquisa a rodada atual sem refazer a consulta', async () => {
  const base = { total_avaliados: 1, limite_nos: 24, vizinhos_por_filme: 3, arestas: [] }
  const rated = { id: 'rated', titulo: 'Meu filme', tipo: 'avaliado', nota_usuario: 9, generos: ['Drama'], genero_principal: 'Drama', url_poster: null }
  const candidate = { id: 'old', titulo: 'Sugestão anterior', tipo: 'recomendado', generos: ['Drama'], genero_principal: 'Drama', url_poster: null }
  const fetcher = vi.fn()
    .mockImplementationOnce(() => json({ ...base, nos: [rated, candidate] }))
    .mockImplementationOnce(() => json({ ...base, nos: [rated, { ...candidate, id: 'new', titulo: 'Nova sugestão' }] }))
  vi.stubGlobal('fetch', fetcher)
  const user = userEvent.setup()
  render(<TasteMap onOpenMovie={vi.fn()} />)
  await screen.findByRole('button', { name: 'Abrir Sugestão anterior' })
  await user.click(screen.getByRole('button', { name: /Atualizar mapa/ }))
  await screen.findByRole('button', { name: 'Abrir Nova sugestão' })
  expect(screen.queryByRole('button', { name: 'Abrir Sugestão anterior' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Abrir Meu filme' })).toBeInTheDocument()
  await user.type(screen.getByLabelText('Pesquisar dentro do mapa'), 'Nova')
  expect(fetcher).toHaveBeenCalledTimes(2)
})
