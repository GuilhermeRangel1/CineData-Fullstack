import { useCallback, useEffect, useState } from 'react'
import { listarFilmes } from '../api/client'
import { Icon } from '../components/Icon'
import { MovieCard } from '../components/MovieCard'
import { useResource } from '../hooks/useResource'

const genres = [
  ['', 'Todos os filmes'],
  ['Animation', 'Animação'],
  ['Adventure', 'Aventura'],
  ['Drama', 'Drama'],
  ['Comedy', 'Comédia'],
  ['Thriller', 'Suspense'],
] as const

export function Catalog({
  genre,
  onGenre,
  onOpen,
  revision = 0,
}: {
  genre: string
  onGenre: (value: string) => void
  onOpen: (id: string) => void
  revision?: number
}) {
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [order, setOrder] = useState('recent')
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setQuery(search.trim())
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])
  const loader = useCallback(
    (signal: AbortSignal) => {
      const params = new URLSearchParams({
        pagina: String(page),
        tamanho_pagina: '12',
        ordenar_por: order === 'recent' ? 'ano_lancamento' : 'titulo',
        direcao: order === 'recent' ? 'desc' : 'asc',
        priorizar_capa: 'true',
      })
      if (query) params.set('busca', query)
      if (genre) params.set('genero', genre)
      return listarFilmes(params, signal)
    },
    [page, query, genre, order],
  )
  const { data, loading, error, retry } = useResource(loader, revision)
  if (data && page > Math.max(1, data.meta.total_paginas))
    setPage(Math.max(1, data.meta.total_paginas))
  function changePage(value: number) {
    setPage(value)
    document.getElementById('catalogo')?.scrollIntoView({ block: 'start' })
  }
  return (
    <section className="catalog-section" id="catalogo" aria-labelledby="catalog-title">
      <div className="catalog-heading">
        <div>
          <p className="eyebrow">ENCONTRE SUA PRÓXIMA HISTÓRIA</p>
          <h2 id="catalog-title">O cinema não acaba aqui.</h2>
        </div>
        <label className="search">
          <Icon name="search" />
          <span className="sr-only">Buscar por título</span>
          <input
            type="search"
            placeholder="Qual filme você procura?"
            value={search}
            maxLength={100}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
      </div>
      <div className="catalog-toolbar">
        <div className="genre-filters" aria-label="Filtrar por gênero">
          {genres.map(([value, label]) => (
            <button
              key={value}
              aria-pressed={genre === value}
              onClick={() => {
                setPage(1)
                onGenre(value)
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <label className="sort-control">
          <span className="sr-only">Ordenar filmes</span>
          <select
            value={order}
            onChange={(event) => {
              setOrder(event.target.value)
              setPage(1)
            }}
          >
            <option value="recent">Mais recentes</option>
            <option value="title">Título: A–Z</option>
          </select>
        </label>
      </div>
      <div aria-busy={loading}>
        <p className="result-count" role="status">
          {loading
            ? 'Buscando histórias…'
            : error
              ? 'Catálogo indisponível'
              : `${(data?.meta.total_itens ?? 0).toLocaleString('pt-BR')} ${data?.meta.total_itens === 1 ? 'filme' : 'filmes'}${query ? ` para “${query}”` : ' para descobrir'}`}
        </p>
        {error ? (
          <div className="empty-state" role="alert">
            <Icon name="film" />
            <h3>Uma pausa na sessão.</h3>
            <p>{error}</p>
            <button className="button button-light" onClick={retry}>
              Tentar novamente
            </button>
          </div>
        ) : loading ? (
          <div className="movie-grid">
            {Array.from({ length: 6 }, (_, i) => (
              <div className="poster skeleton" key={i} />
            ))}
          </div>
        ) : !data?.itens.length ? (
          <div className="empty-state">
            <Icon name="search" />
            <h3>Nenhuma história por aqui. Ainda.</h3>
            <p>
              {query || genre
                ? 'Experimente outro título ou remova os filtros.'
                : 'Os filmes cadastrados aparecerão neste catálogo.'}
            </p>
            {(query || genre) && (
              <button
                className="button button-light"
                onClick={() => {
                  setSearch('')
                  setQuery('')
                  setPage(1)
                  onGenre('')
                }}
              >
                Limpar filtros
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="movie-grid">
              {data.itens.map((movie) => (
                <MovieCard key={movie.id} movie={movie} onOpen={onOpen} />
              ))}
            </div>
            <nav className="pagination" aria-label="Paginação do catálogo">
              <button
                className="button button-outline"
                disabled={page === 1}
                onClick={() => changePage(page - 1)}
              >
                <Icon name="left" /> Anterior
              </button>
              <span>
                Página <strong>{page}</strong> de {data.meta.total_paginas.toLocaleString('pt-BR')}
              </span>
              <button
                className="button button-outline"
                disabled={page >= data.meta.total_paginas}
                onClick={() => changePage(page + 1)}
              >
                Próxima <Icon name="arrow" />
              </button>
            </nav>
          </>
        )}
      </div>
    </section>
  )
}
