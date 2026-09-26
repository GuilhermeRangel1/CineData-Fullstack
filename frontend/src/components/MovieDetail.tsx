import { useCallback, useEffect, useRef, useState } from 'react'
import { adicionarFilmeALista, listarListas, obterFilme, removerFilme } from '../api/client'
import { useResource } from '../hooks/useResource'
import { useMutation } from '../hooks/useMutation'
import { Dialog } from './Dialog'
import { MovieForm } from './MovieForm'
import { ReviewForm } from './ReviewForm'
import { youtubeEmbedUrl } from '../lib/youtube'
import type { ListaLeitura, UsuarioLeitura } from '../types/api'

const number = (value: number | null | undefined) =>
  value == null ? 'Não informado' : value.toLocaleString('pt-BR')

export function MovieDetail({
  id,
  onClose,
  onChanged,
  onDeleted,
  usuario = null,
  onLoginRequested = () => undefined,
  onOpenLists = () => undefined,
}: {
  id: string
  onClose: () => void
  onChanged?: () => void
  onDeleted?: () => void
  usuario?: UsuarioLeitura | null
  onLoginRequested?: () => void
  onOpenLists?: () => void
}) {
  const [mode, setMode] = useState<'view' | 'edit' | 'delete'>('view')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [failedCoverUrl, setFailedCoverUrl] = useState('')
  const [personalLists, setPersonalLists] = useState<ListaLeitura[] | null>(() => usuario ? null : [])
  const [selectedListId, setSelectedListId] = useState('')
  const [savedListName, setSavedListName] = useState('')
  const focusAfterChange = useRef(false)
  const feedback = useRef<HTMLParagraphElement>(null)
  const editButton = useRef<HTMLButtonElement>(null)
  const deletion = useMutation()
  const listMutation = useMutation()
  const loader = useCallback((signal: AbortSignal) => obterFilme(id, signal), [id])
  const { data: movie, loading, error, retry } = useResource(loader)
  useEffect(() => {
    if (mode === 'view' && !loading && focusAfterChange.current) {
      ;(feedback.current ?? editButton.current)?.focus()
      focusAfterChange.current = false
    }
  }, [mode, loading, error])
  useEffect(() => {
    if (!usuario) return
    const controller = new AbortController()
    void listarListas(controller.signal)
      .then((lists) => setPersonalLists(Array.isArray(lists) ? lists : []))
      .catch(() => {
        if (!controller.signal.aborted) setPersonalLists([])
      })
    return () => controller.abort()
  }, [usuario])
  const people = (role: string) =>
    movie?.pessoas
      .filter((person) => person.papel === role)
      .map((person) => person.nome)
      .join(', ') || 'Não informado'
  const coverUrl = movie?.url_backdrop ?? movie?.url_poster
  const trailerUrl = movie?.url_trailer ? youtubeEmbedUrl(movie.url_trailer) : null
  const selectedList = personalLists?.find((list) => list.id === selectedListId)
  function saveToSelectedList() {
    if (!selectedList) return
    void listMutation.run(
      () => adicionarFilmeALista(selectedList.id, id),
      () => setSavedListName(selectedList.nome),
    )
  }
  return (
    <Dialog
      title={
        mode === 'edit'
          ? 'Editar filme'
          : mode === 'delete'
            ? 'Excluir filme'
            : (movie?.titulo ?? 'Detalhes do filme')
      }
      onClose={onClose}
      className="detail-dialog"
      busy={busy || deletion.pending}
    >
      {notice && (
        <p ref={feedback} tabIndex={-1} className="success-message detail-notice" role="status">
          {notice}
        </p>
      )}
      {mode === 'edit' && movie ? (
        <MovieForm
          movie={movie}
          onBusyChange={setBusy}
          onCancel={() => {
            focusAfterChange.current = true
            setMode('view')
          }}
          onSaved={() => {
            focusAfterChange.current = true
            setMode('view')
            setNotice('Alterações salvas.')
            retry()
            onChanged?.()
          }}
        />
      ) : mode === 'delete' && movie ? (
        <div className="editor-body delete-confirmation">
          <p className="eyebrow">GESTÃO DO CATÁLOGO</p>
          <h2>Excluir este filme?</h2>
          <p>
            Você vai excluir <strong>{movie.titulo}</strong> e suas avaliações. Esta ação não pode
            ser desfeita.
          </p>
          {deletion.error && (
            <p role="alert" className="form-error">
              {deletion.error}
            </p>
          )}
          <div className="form-actions">
            <button
              className="button button-outline"
              autoFocus
              disabled={deletion.pending}
              onClick={() => {
                focusAfterChange.current = true
                setMode('view')
              }}
            >
              Manter filme
            </button>
            <button
              className="button button-danger"
              disabled={deletion.pending}
              onClick={() =>
                void deletion.run(
                  () => removerFilme(id),
                  () => {
                    onDeleted?.()
                    onClose()
                  },
                )
              }
            >
              {deletion.pending ? 'Excluindo…' : 'Excluir definitivamente'}
            </button>
          </div>
        </div>
      ) : loading ? (
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
              {coverUrl && failedCoverUrl !== coverUrl && (
                <img
                  src={coverUrl.replace('/t/p/w1280/', '/t/p/w780/')}
                  alt=""
                  decoding="async"
                  referrerPolicy="no-referrer"
                  onError={() => {
                    setFailedCoverUrl(coverUrl)
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
              {usuario?.role === 'admin' && (
                <div className="management-actions">
                  <span>GESTÃO DO FILME</span>
                  <button
                    ref={editButton}
                    className="button button-outline"
                    disabled={busy}
                    onClick={() => {
                      setNotice('')
                      setMode('edit')
                    }}
                  >
                    Editar filme
                  </button>
                  <button
                    className="text-button danger-text"
                    disabled={busy}
                    onClick={() => {
                      setNotice('')
                      setMode('delete')
                    }}
                  >
                    Excluir filme
                  </button>
                </div>
              )}
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
              <section className="save-to-list" aria-labelledby="save-to-list-title">
                <div>
                  <p className="eyebrow">SUA CURADORIA</p>
                  <h3 id="save-to-list-title">Salvar em uma lista</h3>
                </div>
                {!usuario ? (
                  <button className="button button-outline" onClick={onLoginRequested}>Entrar para salvar</button>
                ) : personalLists === null ? (
                  <p className="muted">Carregando suas listas…</p>
                ) : personalLists.length === 0 ? (
                  <p className="muted">Você ainda não criou uma lista. <button className="text-button" onClick={onOpenLists}>Criar uma lista</button></p>
                ) : (
                  <div className="list-picker">
                    <label htmlFor="movie-list-picker">Escolha uma lista
                      <select id="movie-list-picker" value={selectedListId} onChange={(event) => setSelectedListId(event.target.value)} disabled={listMutation.pending}>
                        <option value="">Selecione uma lista</option>
                        {personalLists.map((list) => <option key={list.id} value={list.id}>{list.nome} · {list.quantidade_filmes} {list.quantidade_filmes === 1 ? 'filme' : 'filmes'}</option>)}
                      </select>
                    </label>
                    <button className="button button-outline" disabled={!selectedList || listMutation.pending} onClick={saveToSelectedList}>{listMutation.pending ? 'Salvando…' : 'Salvar na lista'}</button>
                  </div>
                )}
                {savedListName && <p className="success-message" role="status">Adicionado a {savedListName}.</p>}
                {listMutation.error && <p className="form-error" role="alert">{listMutation.error}</p>}
              </section>
              <h3>Sinopse</h3>
              <p className="synopsis">{movie.sinopse || 'Ainda não há sinopse para este filme.'}</p>
              {trailerUrl && (
                <section className="movie-trailer" aria-label="Trailer">
                  <h3>Trailer</h3>
                  <iframe
                    title={`Trailer de ${movie.titulo}`}
                    src={trailerUrl}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </section>
              )}
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
                {usuario ? (
                  <ReviewForm
                    movieId={id}
                    onBusyChange={setBusy}
                    onSaved={() => {
                      focusAfterChange.current = true
                      setNotice('Avaliação publicada. Sua nota já faz parte da média.')
                      retry()
                      onChanged?.()
                    }}
                  />
                ) : (
                  <div className="review-login-prompt">
                    <p className="muted">Entre na sua conta para publicar uma avaliação.</p>
                    <button className="button button-outline" onClick={onLoginRequested}>
                      Entrar para avaliar
                    </button>
                  </div>
                )}
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
