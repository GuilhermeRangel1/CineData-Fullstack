import { useEffect, useState } from 'react'
import { obterPerfilPublico } from '../api/client'
import type { PerfilPublico, PessoaComunidade } from '../types/api'
import { Dialog } from './Dialog'

export function PersonAvatar({ person }: { person: PessoaComunidade }) {
  return person.avatar_url ? <img className="community-avatar" src={person.avatar_url} alt="" /> : <span className="community-avatar community-avatar-fallback" aria-hidden="true">{person.nome.slice(0, 1).toUpperCase()}</span>
}

export function PublicProfile({ person, onClose, onOpenMovie }: {
  person: PessoaComunidade
  onClose: () => void
  onOpenMovie: (id: string) => void
}) {
  const [profile, setProfile] = useState<PerfilPublico | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    void obterPerfilPublico(person.id, controller.signal)
      .then(setProfile)
      .catch((failure: Error) => { if (!controller.signal.aborted) setError(failure.message) })
    return () => controller.abort()
  }, [person.id])
  return (
    <Dialog title={`Perfil de ${person.nome}`} className="public-profile-dialog" onClose={onClose}>
      <div className="public-profile">
        <header><PersonAvatar person={profile ?? person} /><div><p className="eyebrow">PERFIL PÚBLICO</p><h2>{profile?.nome ?? person.nome}</h2></div></header>
        {error ? <p className="form-error" role="alert">{error}</p> : !profile ? <p role="status">Carregando perfil…</p> : <>
          <p className="public-profile-friends">{profile.quantidade_amigos} {profile.quantidade_amigos === 1 ? 'amigo' : 'amigos'}</p>
          <section><h3>Avaliações</h3>{profile.avaliacoes.length === 0 ? <p>Nenhuma avaliação pública.</p> : profile.avaliacoes.map((review) => <article key={review.id}><button className="text-button" onClick={() => onOpenMovie(review.filme.id)}>{review.filme.titulo}</button><strong>{review.nota}/10</strong><p>{review.comentario}</p></article>)}</section>
          <section><h3>Listas públicas</h3>{profile.listas_publicas.length === 0 ? <p>Nenhuma lista pública.</p> : profile.listas_publicas.map((list) => <details key={list.id}><summary>{list.nome} · {list.quantidade_filmes} filmes</summary><ul>{list.filmes.map((movie) => <li key={movie.id}><button className="text-button" onClick={() => onOpenMovie(movie.id)}>{movie.titulo}</button></li>)}</ul></details>)}</section>
        </>}
      </div>
    </Dialog>
  )
}
