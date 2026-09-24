import { useState } from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { Catalog } from './Catalog'
import type { FilmeResumo, Pagina } from '../types/api'

const movie: FilmeResumo = {
  id: '1',
  titulo: 'Uma história',
  ano_lancamento: 2024,
  url_poster: null,
  generos: [],
  nota_media: 0,
  quantidade_avaliacoes: 1,
}
const result = (items = [movie], page = 1, total = 24): Pagina<FilmeResumo> => ({
  itens: items,
  meta: {
    pagina: page,
    tamanho_pagina: 12,
    total_itens: total,
    total_paginas: Math.ceil(total / 12),
  },
})
function response(value: unknown) {
  return Promise.resolve(new Response(JSON.stringify(value)))
}
function View({ onOpen = vi.fn() }: { onOpen?: (id: string) => void }) {
  const [genre, setGenre] = useState('')
  return <Catalog genre={genre} onGenre={setGenre} onOpen={onOpen} />
}

describe('Catálogo conectado', () => {
  it('volta à última página válida após excluir o último resultado sem perder os filtros', async () => {
    let deleted = false
    const fetcher = vi.fn((url: string) => {
      const page = Number(new URL(url).searchParams.get('pagina'))
      return response(result(deleted && page === 2 ? [] : [movie], page, deleted ? 12 : 13))
    })
    vi.stubGlobal('fetch', fetcher)
    const props = { genre: 'Animation', onGenre: vi.fn(), onOpen: vi.fn() }
    const { rerender } = render(<Catalog {...props} revision={0} />)
    await userEvent.click(await screen.findByRole('button', { name: /Próxima/ }))
    await waitFor(() =>
      expect(new URL(fetcher.mock.lastCall![0]).searchParams.get('pagina')).toBe('2'),
    )
    deleted = true
    rerender(<Catalog {...props} revision={1} />)
    await waitFor(() =>
      expect(screen.getByRole('navigation', { name: 'Paginação do catálogo' })).toHaveTextContent(
        'Página 1 de 1',
      ),
    )
    expect(new URL(fetcher.mock.lastCall![0]).searchParams.get('genero')).toBe('Animation')
  })
  it('mostra carregamento e depois filme, nota zero e detalhes', async () => {
    let finish!: (value: Response) => void
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise<Response>((resolve) => {
            finish = resolve
          }),
      ),
    )
    const onOpen = vi.fn()
    render(<View onOpen={onOpen} />)
    expect(screen.getByRole('status')).toHaveTextContent('Buscando')
    finish(new Response(JSON.stringify(result())))
    await userEvent.click(
      await screen.findByRole('button', { name: 'Ver detalhes de Uma história' }),
    )
    expect(onOpen).toHaveBeenCalledWith('1')
    expect(screen.getByLabelText('Média 0.0 de 10')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Anterior/ })).toBeDisabled()
  })

  it('combina paginação, gênero, busca e ordenação, reiniciando a página', async () => {
    const fetcher = vi.fn((url: string) =>
      response(result([movie], Number(new URL(url).searchParams.get('pagina')))),
    )
    vi.stubGlobal('fetch', fetcher)
    render(<View />)
    await userEvent.click(await screen.findByRole('button', { name: /Próxima/ }))
    await waitFor(() =>
      expect(new URL(fetcher.mock.lastCall![0]).searchParams.get('pagina')).toBe('2'),
    )
    await userEvent.click(screen.getByRole('button', { name: 'Animação' }))
    await waitFor(() => {
      const params = new URL(fetcher.mock.lastCall![0]).searchParams
      expect(params.get('pagina')).toBe('1')
      expect(params.get('genero')).toBe('Animation')
    })
    await userEvent.type(screen.getByRole('searchbox'), 'Castelo')
    await waitFor(() =>
      expect(new URL(fetcher.mock.lastCall![0]).searchParams.get('busca')).toBe('Castelo'),
    )
    await userEvent.selectOptions(screen.getByRole('combobox'), 'title')
    await waitFor(() =>
      expect(new URL(fetcher.mock.lastCall![0]).searchParams.get('ordenar_por')).toBe('titulo'),
    )
  })

  it('permite tentar novamente depois de uma falha de rede', async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new TypeError('offline'))
      .mockImplementation(() => response(result()))
    vi.stubGlobal('fetch', fetcher)
    render(<View />)
    await userEvent.click(await screen.findByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByRole('heading', { name: movie.titulo })).toBeInTheDocument()
  })

  it('mostra estado vazio e limpa filtros', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => response(result([], 1, 0))),
    )
    render(<View />)
    expect(await screen.findByText('Nenhuma história por aqui. Ainda.')).toBeInTheDocument()
    await userEvent.type(screen.getByRole('searchbox'), 'inexistente')
    await userEvent.click(await screen.findByRole('button', { name: 'Limpar filtros' }))
    expect(screen.getByRole('searchbox')).toHaveValue('')
  })

  it('descarta a resposta atrasada de uma busca antiga', async () => {
    let oldResponse!: (value: Response) => void
    vi.stubGlobal(
      'fetch',
      vi.fn((url: string) => {
        const query = new URL(url).searchParams.get('busca')
        if (query === 'antigo')
          return new Promise<Response>((resolve) => {
            oldResponse = resolve
          })
        return response(
          result([{ ...movie, titulo: query === 'novo' ? 'Novo resultado' : movie.titulo }]),
        )
      }),
    )
    render(<View />)
    await screen.findByRole('heading', { name: movie.titulo })
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'antigo' } })
    await waitFor(() => expect(oldResponse).toBeDefined())
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'novo' } })
    await screen.findByRole('heading', { name: 'Novo resultado' })
    oldResponse(new Response(JSON.stringify(result([{ ...movie, titulo: 'Antigo resultado' }]))))
    await waitFor(() => expect(screen.queryByText('Antigo resultado')).not.toBeInTheDocument())
    expect(screen.getByRole('heading', { name: 'Novo resultado' })).toBeInTheDocument()
  })
})
