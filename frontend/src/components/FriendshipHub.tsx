import { useEffect, useState } from 'react'
import {
  enviarSolicitacaoAmizade,
  listarAmigos,
  listarSolicitacoesAmizade,
  pesquisarPessoas,
  removerAmigo,
  responderSolicitacaoAmizade,
} from '../api/client'
import type { ContatoAmizade, SolicitacaoAmizade, UsuarioLeitura } from '../types/api'
import { PublicProfile } from './PublicProfile'

const VISIBLE_ITEMS_LIMIT = 5

export function FriendshipHub({ usuario, onLoginRequested, onOpenMovie }: {
  usuario: UsuarioLeitura | null
  onLoginRequested: () => void
  onOpenMovie: (id: string) => void
}) {
  const userId = usuario?.id
  const [friends, setFriends] = useState<ContatoAmizade[]>([])
  const [requests, setRequests] = useState<SolicitacaoAmizade[]>([])
  const [query, setQuery] = useState('')
  const [people, setPeople] = useState<ContatoAmizade[]>([])
  const [loading, setLoading] = useState(Boolean(userId))
  const [searching, setSearching] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [profile, setProfile] = useState<ContatoAmizade | null>(null)
  const [showAllSearch, setShowAllSearch] = useState(false)
  const [showAllReceived, setShowAllReceived] = useState(false)
  const [showAllSent, setShowAllSent] = useState(false)
  const [showAllFriends, setShowAllFriends] = useState(false)

  useEffect(() => {
    if (!userId) return
    const controller = new AbortController()
    void Promise.all([listarAmigos(controller.signal), listarSolicitacoesAmizade(controller.signal)])
      .then(([currentFriends, currentRequests]) => {
        setFriends(currentFriends)
        setRequests(currentRequests)
      })
      .catch((failure: Error) => {
        if (!controller.signal.aborted) setError(failure.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [userId])

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2) {
      return
    }
    const controller = new AbortController()
    const timeout = window.setTimeout(() => {
      setSearching(true)
      void pesquisarPessoas(term, controller.signal)
        .then(setPeople)
        .catch((failure: Error) => {
          if (!controller.signal.aborted) setError(failure.message)
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false)
        })
    }, 250)
    return () => {
      controller.abort()
      window.clearTimeout(timeout)
    }
  }, [query])

  async function manage(task: () => Promise<void>) {
    setBusy(true)
    setError('')
    try {
      await task()
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Não foi possível concluir a ação.')
    } finally {
      setBusy(false)
    }
  }

  function relationFor(personId: string) {
    if (friends.some((friend) => friend.id === personId)) return 'amigo' as const
    return requests.find((request) => request.pessoa.id === personId) ?? null
  }

  function addFriend(person: ContatoAmizade) {
    setFriends((items) => [...items.filter((item) => item.id !== person.id), person].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')))
  }

  const received = requests.filter((request) => request.direcao === 'recebida' && request.status === 'pendente')
  const sent = requests.filter((request) => request.direcao === 'enviada' && request.status === 'pendente')
  const visiblePeople = showAllSearch ? people : people.slice(0, VISIBLE_ITEMS_LIMIT)
  const visibleReceived = showAllReceived ? received : received.slice(0, VISIBLE_ITEMS_LIMIT)
  const visibleSent = showAllSent ? sent : sent.slice(0, VISIBLE_ITEMS_LIMIT)
  const visibleFriends = showAllFriends ? friends : friends.slice(0, VISIBLE_ITEMS_LIMIT)

  if (!usuario) {
    return <main className="friend-page friend-page--guest" id="amigos">
      <section className="friend-guest-panel">
        <p className="eyebrow"><span className="red-line" />CINEMA FICA MELHOR EM COMPANHIA</p>
        <h1>Encontre sua próxima conversa.</h1>
        <p>Adicione pessoas, acompanhe os filmes que elas recomendam e transforme cada sessão em uma troca.</p>
        <button className="button button-light" onClick={onLoginRequested}>Entrar para encontrar amigos</button>
      </section>
    </main>
  }

  return <main className="friend-page" id="amigos">
    <header className="friend-header">
      <div>
        <p className="eyebrow"><span className="red-line" />CINEMA FICA MELHOR EM COMPANHIA</p>
        <h1>Amigos</h1>
      </div>
    </header>
    <div className="friend-content">
      {error && <p className="form-error" role="alert">{error}</p>}
      {loading ? <p role="status">Carregando sua rede…</p> : <>
        <section className="friend-search" aria-labelledby="friend-search-title">
          <div className="friend-section-heading"><div><p className="eyebrow">EXPANDA SUA REDE</p><h2 id="friend-search-title">Quem vai para a próxima sessão?</h2></div><span>Busque pelo nome</span></div>
          <label htmlFor="friend-search-input">Encontrar pessoas<input id="friend-search-input" type="search" value={query} onChange={(event) => { setQuery(event.target.value); setShowAllSearch(false) }} placeholder="Digite pelo menos 2 letras" autoComplete="off" /></label>
          {query.trim().length >= 2 && <div className="friend-search-results" aria-live="polite">
            {searching ? <p>Procurando pessoas…</p> : people.length === 0 ? <p>Nenhuma pessoa encontrada.</p> : visiblePeople.map((person) => {
              const relation = relationFor(person.id)
              const label = relation === 'amigo'
                ? 'Já são amigos'
                : relation
                  ? relation.status === 'bloqueada' ? 'Contato bloqueado' : relation.direcao === 'enviada' ? 'Pedido enviado' : 'Responda ao pedido abaixo'
                  : 'Adicionar'
              return <article key={person.id} className="friend-person-result"><ProfileTrigger person={person} subtitle="Perfil CineData" onOpen={() => setProfile(person)} />{relation ? <span className="friend-relation">{label}</span> : <button className="button button-outline" disabled={busy} aria-label={`Enviar pedido para ${person.nome}`} onClick={() => void manage(async () => {
                const created = await enviarSolicitacaoAmizade(person.id)
                setRequests((items) => [created, ...items])
              })}>Adicionar</button>}</article>
            })}
            {!searching && <CollectionToggle total={people.length} expanded={showAllSearch} label="resultados da busca" onToggle={() => setShowAllSearch((value) => !value)} />}
          </div>}
        </section>

        <div className="friend-columns">
          <section className="friend-panel" aria-labelledby="received-requests-title">
            <div className="friend-section-heading"><div><p className="eyebrow">PARA VOCÊ</p><h2 id="received-requests-title">Pedidos recebidos</h2></div><span className={`friend-notification-badge ${received.length > 0 ? 'has-notifications' : ''}`} aria-label={`${received.length} ${received.length === 1 ? 'pedido pendente' : 'pedidos pendentes'}`}>{received.length}</span></div>
            {received.length === 0 ? <p className="friend-empty">Nenhum convite esperando por você.</p> : <><div className="friend-request-list">{visibleReceived.map((request) => <article className="friend-request" key={request.id}><ProfileTrigger person={request.pessoa} subtitle="Quer adicionar você à rede." onOpen={() => setProfile(request.pessoa)} /><div className="friend-request-actions"><button className="button button-light" disabled={busy} onClick={() => void manage(async () => {
              const updated = await responderSolicitacaoAmizade(request.id, 'aceitar')
              setRequests((items) => items.map((item) => item.id === updated.id ? updated : item))
              addFriend(updated.pessoa)
            })}>Aceitar</button><button className="text-button danger-text" disabled={busy} onClick={() => void manage(async () => {
              const updated = await responderSolicitacaoAmizade(request.id, 'bloquear')
              setRequests((items) => items.map((item) => item.id === updated.id ? updated : item))
            })}>Bloquear</button></div></article>)}</div><CollectionToggle total={received.length} expanded={showAllReceived} label="pedidos recebidos" onToggle={() => setShowAllReceived((value) => !value)} /></>}
          </section>

          <section className="friend-panel" aria-labelledby="sent-requests-title">
            <div className="friend-section-heading"><div><p className="eyebrow">EM ANDAMENTO</p><h2 id="sent-requests-title">Pedidos enviados</h2></div><span>{sent.length}</span></div>
            {sent.length === 0 ? <p className="friend-empty">Quando você enviar um convite, ele aparece aqui.</p> : <><div className="friend-request-list">{visibleSent.map((request) => <article className="friend-request" key={request.id}><ProfileTrigger person={request.pessoa} subtitle="Aguardando resposta." onOpen={() => setProfile(request.pessoa)} /><span className="friend-relation">Enviado</span></article>)}</div><CollectionToggle total={sent.length} expanded={showAllSent} label="pedidos enviados" onToggle={() => setShowAllSent((value) => !value)} /></>}
          </section>
        </div>

        <section className="friend-panel friend-panel--wide" aria-labelledby="friends-title">
          <div className="friend-section-heading"><div><p className="eyebrow">SUA REDE</p><h2 id="friends-title">Amigos</h2></div><span>{friends.length} {friends.length === 1 ? 'amigo' : 'amigos'}</span></div>
          {friends.length === 0 ? <p className="friend-empty">Sua rede ainda está começando. Procure alguém acima para enviar o primeiro convite.</p> : <><div className="friend-grid">{visibleFriends.map((friend) => <article className="friend-card" key={friend.id}><ProfileTrigger person={friend} subtitle="Conexão na sua rede" onOpen={() => setProfile(friend)} /><button className="text-button danger-text" disabled={busy} onClick={() => void manage(async () => {
            await removerAmigo(friend.id)
            setFriends((items) => items.filter((item) => item.id !== friend.id))
            setRequests((items) => items.filter((request) => request.pessoa.id !== friend.id))
          })}>Remover</button></article>)}</div><CollectionToggle total={friends.length} expanded={showAllFriends} label="amigos" onToggle={() => setShowAllFriends((value) => !value)} /></>}
        </section>
      </>}
    </div>
    {profile && <PublicProfile person={profile} onClose={() => setProfile(null)} onOpenMovie={(id) => { setProfile(null); onOpenMovie(id) }} />}
  </main>
}

function ProfileTrigger({ person, subtitle, onOpen }: {
  person: ContatoAmizade
  subtitle: string
  onOpen: () => void
}) {
  return <button className="friend-profile-trigger" onClick={onOpen} aria-label={`Ver perfil de ${person.nome}`}><Avatar person={person} /><span className="friend-profile-copy"><strong>{person.nome}</strong><small>{subtitle}</small></span></button>
}

function CollectionToggle({ total, expanded, label, onToggle }: {
  total: number
  expanded: boolean
  label: string
  onToggle: () => void
}) {
  if (total <= VISIBLE_ITEMS_LIMIT) return null
  return <button className="friend-show-all" onClick={onToggle}>{expanded ? 'Mostrar menos' : `Ver todos os ${label} (${total})`}<span aria-hidden="true">{expanded ? '↑' : '↓'}</span></button>
}

function Avatar({ person }: { person: ContatoAmizade }) {
  const [failed, setFailed] = useState(false)
  if (person.avatar_url && !failed) return <img className="friend-avatar" src={person.avatar_url} alt="" onError={() => setFailed(true)} />
  return <span className="friend-avatar friend-avatar--fallback" aria-hidden="true">{person.nome.slice(0, 1).toUpperCase()}</span>
}
