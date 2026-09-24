import { useCallback } from 'react'
import { obterFilme } from '../api/client'
import { useResource } from '../hooks/useResource'
import { Dialog } from './Dialog'

const number = (value: number | null | undefined) =>
  value == null ? 'Não informado' : value.toLocaleString('pt-BR')

export function MovieDetail({ id, onClose }: { id: string; onClose: () => void }) {
  const loader = useCallback((signal: AbortSignal) => obterFilme(id, signal), [id])
  const { data: movie, loading, error, retry } = useResource(loader)
  const people = (role: string) =>
    movie?.pessoas
      .filter((person) => person.papel === role)
      .map((person) => person.nome)
      .join(', ') || 'Não informado'
  return (
    <Dialog
      title={movie?.titulo ?? 'Detalhes do filme'}
      onClose={onClose}
      className="detail-dialog"
    >
      {loading ? (
        <p className="dialog-state" role="status">
          Preparando os detalhes…
        </p>
      ) : error ? (
        <div className="dialog-state" role="alert">
          <h2>Não foi possível abrir o filme.</h2>
          <p>{error}</p>
          <button className="button button-light" onClick={retry}>
            Tentar novamente
          </button>
        </div>
      ) : (
        movie && (
          <>
            <div className="detail-cover">
              {movie.url_backdrop && (
                <img
                  src={movie.url_backdrop}
                  alt=""
                  onError={(event) => {
                    event.currentTarget.style.visibility = 'hidden'
                  }}
                />
              )}
              <div className="detail-cover-shade" />
              <div className="detail-title">
                <p className="eyebrow">DENTRO DA HISTÓRIA</p>
                <h2>{movie.titulo}</h2>
                <p>
                  {movie.ano_lancamento ?? 'Ano não informado'} ·{' '}
                  {movie.duracao_minutos == null
                    ? 'Duração não informada'
                    : `${movie.duracao_minutos} min`}
                </p>
              </div>
            </div>
            <div className="detail-body">
              <div className="detail-summary">
                <div className="detail-genres">
                  {movie.generos.map((genre) => (
                    <span key={genre.id}>{genre.nome}</span>
                  ))}
                </div>
                <div className="detail-rating">
                  <strong>{movie.nota_media?.toFixed(1) ?? '—'}</strong>
                  <span>
                    / 10
                    <br />
                    {movie.quantidade_avaliacoes}{' '}
                    {movie.quantidade_avaliacoes === 1 ? 'avaliação' : 'avaliações'}
                  </span>
                </div>
              </div>
              <h3>Sinopse</h3>
              <p className="synopsis">{movie.sinopse || 'Ainda não há sinopse para este filme.'}</p>
              <dl className="credits">
                <div>
                  <dt>Direção</dt>
                  <dd>{people('Diretor')}</dd>
                </div>
                <div>
                  <dt>Elenco</dt>
                  <dd>{people('Ator')}</dd>
                </div>
                <div>
                  <dt>Roteiro</dt>
                  <dd>{people('Roteirista')}</dd>
                </div>
                <div>
                  <dt>Produção</dt>
                  <dd>
                    {movie.produtoras.map((company) => company.nome).join(', ') || 'Não informado'}
                  </dd>
                </div>
                <div>
                  <dt>Lançamento</dt>
                  <dd>
                    {movie.data_lancamento
                      ? new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(
                          new Date(movie.data_lancamento),
                        )
                      : 'Não informado'}
                  </dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{movie.status_filme || 'Não informado'}</dd>
                </div>
              </dl>
              {movie.desempenho && (
                <details className="performance">
                  <summary>Bilheteria e outros números</summary>
                  <dl className="credits">
                    {(['usd', 'brl'] as const).map((currency) => (
                      <div key={currency}>
                        <dt>Orçamento / receita / lucro ({currency.toUpperCase()})</dt>
                        <dd>
                          {number(movie.desempenho?.[`orcamento_${currency}`])} /{' '}
                          {number(movie.desempenho?.[`receita_${currency}`])} /{' '}
                          {number(movie.desempenho?.[`lucro_${currency}`])}
                        </dd>
                      </div>
                    ))}
                    <div>
                      <dt>TMDB</dt>
                      <dd>
                        {number(movie.desempenho.nota_tmdb)} / 10 ·{' '}
                        {number(movie.desempenho.quantidade_tmdb)} avaliações
                      </dd>
                    </div>
                    <div>
                      <dt>IMDb</dt>
                      <dd>
                        {number(movie.desempenho.nota_imdb)} / 10 ·{' '}
                        {number(movie.desempenho.quantidade_imdb)} avaliações
                      </dd>
                    </div>
                    <div>
                      <dt>Popularidade</dt>
                      <dd>{number(movie.desempenho.popularidade)}</dd>
                    </div>
                  </dl>
                </details>
              )}
              <section className="reviews">
                <p className="eyebrow">OUTROS OLHARES</p>
                <h3>O que acharam do filme</h3>
                {movie.avaliacoes.length ? (
                  <ul>
                    {movie.avaliacoes.map((review) => (
                      <li key={review.id}>
                        <div>
                          <strong>{review.nome}</strong>
                          <span>{review.nota.toFixed(1)} / 10</span>
                        </div>
                        <p>{review.comentario}</p>
                        <time dateTime={review.criada_em}>
                          {new Intl.DateTimeFormat('pt-BR').format(new Date(review.criada_em))}
                        </time>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Este filme ainda não tem resenhas.</p>
                )}
              </section>
            </div>
          </>
        )
      )}
    </Dialog>
  )
}
