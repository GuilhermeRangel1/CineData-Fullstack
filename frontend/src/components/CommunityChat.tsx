import { useEffect, useRef, useState, type FormEvent } from 'react'
import { comentarPublicacao, criarPublicacaoComunidade, entrarNaComunidade, listarFilmes, listarMembrosComunidade, listarPublicacoesComunidade, reagirPublicacao, removerComentarioComunidade, removerPublicacaoComunidade, removerReacaoPublicacao, sairDaComunidade } from '../api/client'
import type { ComunidadeLeitura, FilmeResumo, PessoaComunidade, PublicacaoComunidade, TipoReacao, UsuarioLeitura } from '../types/api'
import { Dialog } from './Dialog'
import { Icon } from './Icon'
import { PersonAvatar, PublicProfile } from './PublicProfile'

const REACTIONS: Record<TipoReacao, string> = { curtir: 'Fogo', amei: 'Amei', interessante: 'Pipoca', nao_curti: 'Não curti' }
const SYMBOLS: Record<TipoReacao, string> = { curtir: '🔥', amei: '❤️', interessante: '🍿', nao_curti: '👎' }
const POLLING_INTERVAL_MS = 5_000

type AlvoModeracao =
  | { tipo: 'publicacao'; id: string; autor: string }
  | { tipo: 'comentario'; id: string; autor: string }

function dateLabel(value: string) {
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`))
}

export function CommunityChat({ community, usuario, onClose, onLoginRequested, onOpenMovie, onMembershipChange }: {
  community: ComunidadeLeitura
  usuario: UsuarioLeitura | null
  onClose: () => void
  onLoginRequested: () => void
  onOpenMovie: (id: string) => void
  onMembershipChange: (delta: number) => void
}) {
  const [members, setMembers] = useState<PessoaComunidade[]>([])
  const [posts, setPosts] = useState<PublicacaoComunidade[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [syncError, setSyncError] = useState(false)
  const [revision, setRevision] = useState(0)
  const [content, setContent] = useState('')
  const [mentionOpen, setMentionOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<FilmeResumo[]>([])
  const [movie, setMovie] = useState<FilmeResumo | null>(null)
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [comments, setComments] = useState<Record<string, string>>({})
  const [profile, setProfile] = useState<PessoaComunidade | null>(null)
  const [reactionPending, setReactionPending] = useState<string | null>(null)
  const [moderationTarget, setModerationTarget] = useState<AlvoModeracao | null>(null)
  const timeline = useRef<HTMLDivElement>(null)
  const nearBottom = useRef(true)
  const input = useRef<HTMLTextAreaElement>(null)
  const participating = Boolean(usuario && members.some((member) => member.id === usuario.id))
  const ordered = [...posts].reverse().sort((a, b) => a.criada_em.localeCompare(b.criada_em))

  useEffect(() => {
    if (busy) return
    const controller = new AbortController()
    let fetching = false
    async function refresh() {
      if (fetching || document.visibilityState === 'hidden') return
      fetching = true
      try {
        const [people, messages] = await Promise.all([listarMembrosComunidade(community.id, controller.signal), listarPublicacoesComunidade(community.id, controller.signal)])
        if (!controller.signal.aborted) { setMembers(people); setPosts(messages); setSyncError(false) }
      } catch {
        if (!controller.signal.aborted) setSyncError(true)
      } finally {
        fetching = false
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void refresh()
    const interval = window.setInterval(() => void refresh(), POLLING_INTERVAL_MS)
    const onVisible = () => { if (document.visibilityState === 'visible') void refresh() }
    document.addEventListener('visibilitychange', onVisible)
    return () => { controller.abort(); window.clearInterval(interval); document.removeEventListener('visibilitychange', onVisible) }
  }, [community.id, usuario?.id, busy, revision])

  useEffect(() => {
    if (nearBottom.current && timeline.current) timeline.current.scrollTop = timeline.current.scrollHeight
  }, [posts])

  useEffect(() => {
    if (!mentionOpen || movie || query.trim().length < 2) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      void listarFilmes(new URLSearchParams({ busca: query.trim(), tamanho_pagina: '6', ordenar_por: 'titulo' }), controller.signal)
        .then((data) => { if (!controller.signal.aborted) setResults(data.itens) })
        .catch((failure: Error) => { if (!controller.signal.aborted) setSearchError(failure.message) })
        .finally(() => { if (!controller.signal.aborted) setSearching(false) })
    }, 300)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [query, mentionOpen, movie])

  async function perform(task: () => Promise<void>) {
    setBusy(true)
    setError('')
    try { await task() }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Não foi possível concluir a ação.') }
    finally { setBusy(false) }
  }

  async function send(event: FormEvent) {
    event.preventDefault()
    if (!content.trim() || !participating || busy) return
    await perform(async () => {
      const created = await criarPublicacaoComunidade(community.id, { conteudo: content.trim(), ...(movie ? { movie_id: movie.id } : {}) })
      nearBottom.current = true
      setPosts((items) => [created, ...items.filter((item) => item.id !== created.id)])
      setContent(''); setMovie(null); setQuery(''); setResults([]); setMentionOpen(false)
      input.current?.focus()
    })
  }

  async function reply(event: FormEvent, postId: string) {
    event.preventDefault()
    if (!comments[postId]?.trim()) return
    await perform(async () => {
      const created = await comentarPublicacao(postId, comments[postId].trim())
      setPosts((items) => items.map((post) => post.id === postId ? { ...post, comentarios: [...post.comentarios, created] } : post))
      setComments((current) => ({ ...current, [postId]: '' }))
    })
  }

  async function react(postId: string, type: TipoReacao) {
    const pendingKey = `${postId}:${type}`
    setReactionPending(pendingKey)
    setError('')
    try {
      const reactions = await reagirPublicacao(postId, type)
      setPosts((items) => items.map((item) => item.id === postId ? { ...item, reacoes: reactions } : item))
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Não foi possível registrar a reação.')
    } finally {
      setReactionPending(null)
    }
  }

  async function removeReaction(postId: string) {
    setReactionPending(`${postId}:remove`)
    setError('')
    try {
      await removerReacaoPublicacao(postId)
      setRevision((value) => value + 1)
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Não foi possível remover a reação.')
    } finally {
      setReactionPending(null)
    }
  }

  async function confirmModeration() {
    const target = moderationTarget
    if (!target) return
    await perform(async () => {
      if (target.tipo === 'publicacao') {
        await removerPublicacaoComunidade(target.id)
        setPosts((items) => items.map((post) => post.id !== target.id ? post : {
          ...post,
          conteudo: '',
          removida_por_moderacao: true,
          filme: null,
          reacoes: [],
          comentarios: post.comentarios.map((comment) => ({
            ...comment,
            conteudo: '',
            removida_por_moderacao: true,
          })),
        }))
      } else {
        await removerComentarioComunidade(target.id)
        setPosts((items) => items.map((post) => ({
          ...post,
          comentarios: post.comentarios.map((comment) => comment.id !== target.id ? comment : {
            ...comment,
            conteudo: '',
            removida_por_moderacao: true,
          }),
        })))
      }
      setModerationTarget(null)
    })
  }

  function author(person: PessoaComunidade) {
    return <button className="chat-author" onClick={() => setProfile(person)} aria-label={`Ver perfil de ${person.nome}`}><PersonAvatar person={person} /><strong>{person.nome}</strong></button>
  }

  return (
    <Dialog title={`Conversa · ${community.nome}`} className="community-chat-dialog" busy={busy} onClose={onClose}>
      <div className="community-chat">
        <header className="chat-heading"><div className={`chat-community-icon ${community.imagem_url ? 'has-image' : ''}`} aria-hidden="true">{community.imagem_url ? <img src={community.imagem_url} alt="" /> : <Icon name="film" />}</div><div><p>COMUNIDADE</p><h2>{community.nome}</h2><span>{members.length} {members.length === 1 ? 'membro' : 'membros'}</span></div></header>
        <div className="chat-subheading"><p>{community.descricao}</p>{participating && <button className="text-button" disabled={busy} onClick={() => void perform(async () => { await sairDaComunidade(community.id); onMembershipChange(-1); onClose() })}>Sair da comunidade</button>}</div>
        {error && <p className="form-error chat-alert" role="alert">{error}</p>}
        {syncError && <p className="chat-alert" role="status">Não foi possível atualizar a conversa. <button className="text-button" onClick={() => setRevision((value) => value + 1)}>Tentar novamente</button></p>}
        <div className="chat-timeline" ref={timeline} role="log" aria-label="Mensagens da comunidade" aria-live="polite" aria-relevant="additions" onScroll={() => { const node = timeline.current; if (node) nearBottom.current = node.scrollHeight - node.scrollTop - node.clientHeight < 90 }}>
          {loading ? <p className="chat-empty" role="status">Carregando conversa…</p> : posts.length === 0 ? <div className="chat-empty"><span aria-hidden="true">↗</span><h3>A conversa começa com um oi.</h3><p>Compartilhe uma mensagem ou indique um filme.</p></div> : ordered.map((post) => (
            <article className={`chat-message ${post.autor.id === usuario?.id ? 'chat-message-own' : ''}`} key={post.id}>
              <header>{author(post.autor)}<time dateTime={post.criada_em}>{dateLabel(post.criada_em)}</time>{usuario?.role === 'admin' && !post.removida_por_moderacao && <button className="text-button danger-text community-moderate" aria-label={`Remover publicação de ${post.autor.nome}`} onClick={() => setModerationTarget({ tipo: 'publicacao', id: post.id, autor: post.autor.nome })}>Remover</button>}</header>
              <div className="chat-bubble">
                {post.removida_por_moderacao ? <p className="chat-moderation-notice" role="status">Mensagem removida pela moderação.</p> : <><p>{post.conteudo}</p>
                  {post.filme && <button className="community-movie-mention" onClick={() => onOpenMovie(post.filme!.id)}>{post.filme.url_poster && <img src={post.filme.url_poster} alt="" />}<span><small>FILME MENCIONADO</small><strong>{post.filme.titulo}</strong><em>{post.filme.ano_lancamento ?? ''}</em></span><b aria-hidden="true">↗</b></button>}
                </>}
              </div>
              {!post.removida_por_moderacao && <div className="community-reactions" aria-label={`Reações à mensagem de ${post.autor.nome}`}>
                {(Object.keys(REACTIONS) as TipoReacao[]).map((type) => { const count = post.reacoes.find((reaction) => reaction.tipo === type)?.quantidade ?? 0; const pendingKey = `${post.id}:${type}`; return <button key={type} title={REACTIONS[type]} aria-label={`${REACTIONS[type]}${count ? ` · ${count}` : ''}`} aria-busy={reactionPending === pendingKey} disabled={!participating || reactionPending !== null} onClick={() => void react(post.id, type)}><span aria-hidden="true">{SYMBOLS[type]}</span>{count > 0 && <span className="reaction-count">{count}</span>}</button> })}
                {participating && <button className="reaction-remove" disabled={reactionPending !== null} onClick={() => void removeReaction(post.id)}>Remover reação</button>}
              </div>}
              <details className="chat-replies"><summary>{post.comentarios.length ? `${post.comentarios.length} respostas` : 'Responder'}</summary>
                {post.comentarios.map((comment) => <div className="chat-reply" key={comment.id}><div className="chat-reply-heading">{author(comment.autor)}{usuario?.role === 'admin' && !comment.removida_por_moderacao && <button className="text-button danger-text community-moderate" aria-label={`Remover comentário de ${comment.autor.nome}`} onClick={() => setModerationTarget({ tipo: 'comentario', id: comment.id, autor: comment.autor.nome })}>Remover</button>}</div>{comment.removida_por_moderacao ? <p className="chat-moderation-notice" role="status">Comentário removido pela moderação.</p> : <p>{comment.conteudo}</p>}<time dateTime={comment.criado_em}>{dateLabel(comment.criado_em)}</time></div>)}
                {participating && !post.removida_por_moderacao && <form className="community-comment-form" onSubmit={(event) => void reply(event, post.id)}><label className="sr-only" htmlFor={`reply-${post.id}`}>Responder à mensagem de {post.autor.nome}</label><input id={`reply-${post.id}`} value={comments[post.id] ?? ''} onChange={(event) => setComments((current) => ({ ...current, [post.id]: event.target.value }))} placeholder="Escreva uma resposta" maxLength={2000} /><button className="button button-outline" disabled={busy || !comments[post.id]?.trim()}>Responder</button></form>}
              </details>
            </article>
          ))}
        </div>
        {participating ? <form className="chat-composer" onSubmit={send}>
          {mentionOpen && !movie && <div className="chat-film-search"><label htmlFor="chat-film">Buscar filme do catálogo</label><input id="chat-film" type="search" autoComplete="off" value={query} onChange={(event) => { setQuery(event.target.value); setResults([]); setSearchError(''); setSearching(event.target.value.trim().length >= 2) }} placeholder="Digite ao menos 2 letras" />
            {searching && <p role="status">Buscando…</p>}{searchError && <p className="form-error" role="alert">{searchError}</p>}
            {!searching && !searchError && query.trim().length >= 2 && !results.length && <p>Nenhum filme encontrado.</p>}
            {results.length > 0 && <ul>{results.map((item) => <li key={item.id}><button type="button" onClick={() => { setMovie(item); setMentionOpen(false); input.current?.focus() }}>{item.url_poster && <img src={item.url_poster} alt="" />}<span>{item.titulo}<small>{item.ano_lancamento}</small></span><b>+</b></button></li>)}</ul>}
          </div>}
          {movie && <div className="chat-selected-film">
            {movie.url_poster ? <img src={movie.url_poster} alt="" /> : <span className="chat-selected-film-poster" aria-hidden="true">C</span>}
            <span><small>FILME SELECIONADO</small><strong>{movie.titulo}</strong><em>{movie.ano_lancamento ?? 'Ano não informado'}</em></span>
            <button type="button" className="text-button" onClick={() => setMovie(null)}>Remover filme</button>
          </div>}
          <label className="sr-only" htmlFor="chat-message">Mensagem</label><textarea id="chat-message" ref={input} readOnly={busy} rows={2} maxLength={4000} value={content} onChange={(event) => setContent(event.target.value)} placeholder={`Converse em ${community.nome}…`} required />
          <div className="chat-composer-actions"><button type="button" className="text-button" aria-expanded={mentionOpen} onClick={() => setMentionOpen((open) => !open)} disabled={Boolean(movie)}>{mentionOpen ? 'Fechar busca' : '+ Mencionar filme'}</button><button className="button community-enter" disabled={busy || !content.trim()}>{busy ? 'Enviando…' : 'Enviar mensagem'} <span aria-hidden="true">↗</span></button></div>
        </form> : !loading && <div className="chat-login"><p>{usuario ? 'Participe para enviar mensagens e reagir.' : 'Entre na sua conta para conversar.'}</p><button className="button community-enter" disabled={busy} onClick={() => { if (!usuario) onLoginRequested(); else void perform(async () => { await entrarNaComunidade(community.id); onMembershipChange(1); setRevision((value) => value + 1) }) }}>{usuario ? 'Participar da conversa' : 'Entrar com sua conta'}</button></div>}
      </div>
      {moderationTarget && <Dialog title="Confirmar moderação" className="editor-dialog" busy={busy} onClose={() => setModerationTarget(null)}>
        <div className="community-editor community-moderation-confirmation">
          <h2>Remover {moderationTarget.tipo === 'publicacao' ? 'publicação' : 'comentário'}?</h2>
          <p>{moderationTarget.tipo === 'publicacao' ? 'O conteúdo, filme mencionado, comentários e reações serão removidos. A conversa ficará com um aviso de moderação.' : 'O texto será removido e substituído por um aviso; o restante da conversa será mantido.'}</p>
          <p className="community-moderation-author">Publicado por {moderationTarget.autor}</p>
          <div className="form-actions"><button className="button button-outline" data-initial-focus disabled={busy} onClick={() => setModerationTarget(null)}>Cancelar</button><button className="button button-danger" disabled={busy} onClick={() => void confirmModeration()}>{busy ? 'Removendo…' : 'Confirmar remoção'}</button></div>
        </div>
      </Dialog>}
      {profile && <PublicProfile key={profile.id} person={profile} viewer={usuario} onClose={() => setProfile(null)} onOpenMovie={onOpenMovie} />}
    </Dialog>
  )
}
