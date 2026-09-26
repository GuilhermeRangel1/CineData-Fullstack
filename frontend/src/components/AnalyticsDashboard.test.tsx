import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { AnalyticsDashboard } from './AnalyticsDashboard'
import { json } from '../test/movie'

it('exibe indicadores administrativos e atualiza o período consultado', async () => {
  const fetcher = vi.fn(() => json({
    periodo_dias: 30,
    metricas: [
      { chave: 'filmes', rotulo: 'Filmes no catálogo', valor: 18, detalhe: 'Histórias disponíveis' },
      { chave: 'usuarios', rotulo: 'Pessoas cadastradas', valor: 4, detalhe: 'Contas participantes' },
    ],
    evolucao: [
      { data: '2026-09-25', usuarios: 1, avaliacoes: 2, listas: 0, publicacoes: 1 },
      { data: '2026-09-26', usuarios: 0, avaliacoes: 1, listas: 1, publicacoes: 0 },
    ],
    generos: [{ nome: 'Drama', quantidade: 7, nota_media: 8.2 }],
    filmes_mais_avaliados: [
      { id: 'movie-1', titulo: 'A Chegada', url_poster: null, quantidade_avaliacoes: 3, nota_media: 8.5 },
    ],
    comunidades_em_alta: [
      { id: 'community-1', nome: 'Ficção científica', imagem_url: null, membros: 4, publicacoes: 2, visualizacoes: 9 },
    ],
  }))
  vi.stubGlobal('fetch', fetcher)
  const openMovie = vi.fn()

  render(<AnalyticsDashboard onOpenMovie={openMovie} />)

  expect(await screen.findByText('Filmes no catálogo')).toBeInTheDocument()
  expect(screen.getByText('Ficção científica')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: '7 dias' }))
  await waitFor(() => expect(fetcher).toHaveBeenLastCalledWith(
    expect.stringContaining('periodo_dias=7'),
    expect.any(Object),
  ))
  await userEvent.click(screen.getByRole('button', { name: /A Chegada/ }))
  expect(openMovie).toHaveBeenCalledWith('movie-1')
})
