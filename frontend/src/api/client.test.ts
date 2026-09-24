import { describe, expect, it, vi } from 'vitest'
import { atualizarFilme, listarFilmes, obterFilme } from './client'
import { movie } from '../test/movie'
import type { Pagina } from '../types/api'

const catalogo: Pagina<typeof movie> = {
  itens: [movie],
  meta: { pagina: 1, tamanho_pagina: 12, total_itens: 1, total_paginas: 1 },
}

describe('Cache do cliente da API', () => {
  it('reutiliza respostas recentes de catálogo e detalhes', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(catalogo)))
      .mockResolvedValueOnce(new Response(JSON.stringify(movie)))
    vi.stubGlobal('fetch', fetcher)

    const params = new URLSearchParams({ busca: 'cache-catalogo' })
    await listarFilmes(params)
    await listarFilmes(params)
    await obterFilme('cache-detalhe')
    await obterFilme('cache-detalhe')

    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(fetcher.mock.calls[0][1]).toMatchObject({ cache: 'no-store' })
  })

  it('limpa o cache depois de uma escrita para não exibir dados antigos', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(catalogo)))
      .mockResolvedValueOnce(new Response(JSON.stringify(movie)))
      .mockResolvedValueOnce(new Response(JSON.stringify(catalogo)))
    vi.stubGlobal('fetch', fetcher)

    const params = new URLSearchParams({ busca: 'cache-invalidacao' })
    await listarFilmes(params)
    await atualizarFilme('cache-invalidacao', { titulo: 'Título atualizado' })
    await listarFilmes(params)

    expect(fetcher).toHaveBeenCalledTimes(3)
    expect(fetcher.mock.calls[1][1]).toMatchObject({ method: 'PATCH' })
  })
})
