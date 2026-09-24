import { useCallback, useRef } from 'react'
import { listarFilmes } from '../api/client'
import { useResource } from '../hooks/useResource'
import { Icon } from './Icon'
import { MovieCard } from './MovieCard'

export function MovieShelf({
  title,
  subtitle,
  genre,
  onOpen,
  onExplore,
}: {
  title: string
  subtitle: string
  genre: string
  onOpen: (id: string) => void
  onExplore: (genre: string) => void
}) {
  const loader = useCallback(
    (signal: AbortSignal) =>
      listarFilmes(
        new URLSearchParams({
          genero: genre,
          tamanho_pagina: '12',
          ordenar_por: 'ano_lancamento',
          direcao: 'desc',
        }),
        signal,
      ),
    [genre],
  )
  const { data, loading, error, retry } = useResource(loader)
  const rail = useRef<HTMLDivElement>(null)
  function scroll(direction: number) {
    rail.current?.scrollBy({
      left: direction * rail.current.clientWidth * 0.85,
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 'instant'
        : 'smooth',
    })
  }
  return (
    <section className="shelf" aria-label={title} aria-busy={loading}>
      <div className="section-heading">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        <div className="shelf-actions">
          <button className="text-button" onClick={() => onExplore(genre)}>
            Explorar <Icon name="arrow" />
          </button>
          <button
            className="icon-button shelf-prev"
            aria-label={`Filmes anteriores: ${title}`}
            onClick={() => scroll(-1)}
          >
            <Icon name="left" />
          </button>
          <button
            className="icon-button"
            aria-label={`Próximos filmes: ${title}`}
            onClick={() => scroll(1)}
          >
            <Icon name="arrow" />
          </button>
        </div>
      </div>
      {error ? (
        <div className="inline-state" role="alert">
          <p>{error}</p>
          <button className="text-button" onClick={retry}>
            Tentar novamente
          </button>
        </div>
      ) : loading ? (
        <div className="movie-rail" aria-label="Carregando filmes">
          {Array.from({ length: 6 }, (_, i) => (
            <div className="poster skeleton" key={i} />
          ))}
        </div>
      ) : data?.itens.length ? (
        <div className="movie-rail" ref={rail}>
          {data.itens.map((movie) => (
            <MovieCard key={movie.id} movie={movie} onOpen={onOpen} />
          ))}
        </div>
      ) : (
        <p className="muted">Ainda não há filmes nesta seleção.</p>
      )}
    </section>
  )
}
