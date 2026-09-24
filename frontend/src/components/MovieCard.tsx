import { useState } from 'react'
import type { FilmeResumo } from '../types/api'
import { Icon } from './Icon'

export function MovieCard({ movie, onOpen }: { movie: FilmeResumo; onOpen: (id: string) => void }) {
  const [failed, setFailed] = useState(false)
  const imageUrl = movie.url_poster ?? movie.url_backdrop
  return (
    <article className="movie-card">
      <button
        className="movie-card-link"
        onClick={() => onOpen(movie.id)}
        aria-label={`Ver detalhes de ${movie.titulo}`}
      >
        <div className="poster">
          {imageUrl && !failed ? (
            <img
              src={imageUrl}
              alt=""
              loading="lazy"
              decoding="async"
              referrerPolicy="no-referrer"
              onError={() => setFailed(true)}
            />
          ) : (
            <div className="poster-fallback">
              <Icon name="film" />
              <span>{movie.titulo}</span>
              <small>Pôster indisponível</small>
            </div>
          )}
          <span className="poster-action">
            Ver detalhes <Icon name="arrow" />
          </span>
          {movie.nota_media !== null && (
            <span className="score" aria-label={`Média ${movie.nota_media.toFixed(1)} de 10`}>
              {movie.nota_media.toFixed(1)}
              <small>/10</small>
            </span>
          )}
        </div>
        <div className="movie-caption">
          <h3>{movie.titulo}</h3>
          <p>
            {movie.ano_lancamento ?? 'Ano não informado'}
            <span>·</span>
            {movie.nota_media === null
              ? 'Sem avaliações'
              : `${movie.quantidade_avaliacoes} ${movie.quantidade_avaliacoes === 1 ? 'avaliação' : 'avaliações'}`}
          </p>
        </div>
      </button>
    </article>
  )
}
