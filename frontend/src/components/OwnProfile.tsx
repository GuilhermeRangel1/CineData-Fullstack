import { useEffect, useState } from 'react'
import { obterPerfilProprio } from '../api/client'
import type { PerfilProprio, UsuarioLeitura } from '../types/api'
import { Dialog } from './Dialog'
import { ProfileForm } from './ProfileForm'
import { PersonAvatar, ProfilePoster } from './PublicProfile'

export function OwnProfile({ user, busy, onClose, onBusyChange, onSaved, onOpenMovie }: {
  user: UsuarioLeitura
  busy: boolean
  onClose: () => void
  onBusyChange: (busy: boolean) => void
  onSaved: (user: UsuarioLeitura) => void
  onOpenMovie: (id: string) => void
}) {
  const [profile, setProfile] = useState<PerfilProprio | null>(null)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    void obterPerfilProprio(controller.signal)
      .then(setProfile)
      .catch((failure: Error) => { if (!controller.signal.aborted) setError(failure.message) })
    return () => controller.abort()
  }, [])

  const communities = profile?.comunidades ?? []
  const reviews = profile?.avaliacoes.slice(0, 5) ?? []
  const lists = profile?.listas ?? []
  const person = profile ?? { nome: user.nome, avatar_url: user.avatar_url ?? null }

  return (
    <Dialog title="Seu perfil" className="public-profile-dialog" busy={busy} onClose={onClose}>
      <div className="public-profile own-profile">
        <header className="public-profile-hero">
          <PersonAvatar person={person} />
          <div className="public-profile-identity"><p className="eyebrow">SEU PERFIL CINEDATA</p><h2>{person.nome}</h2><span>O que você compartilha e guarda para si no CineData.</span></div>
          <button className="button button-outline own-profile-edit-trigger" onClick={() => setEditing((value) => !value)}>{editing ? 'Fechar edição' : 'Editar perfil'}</button>
        </header>
        {editing && <div className="own-profile-edit"><ProfileForm user={user} onBusyChange={onBusyChange} onCancel={() => setEditing(false)} onSaved={(updated) => { onSaved(updated); setProfile((current) => current ? { ...current, nome: updated.nome, avatar_url: updated.avatar_url ?? null } : current); setEditing(false) }} /></div>}
        {error ? <p className="form-error" role="alert">{error}</p> : !profile ? <p role="status">Carregando perfil…</p> : <>
          <div className="public-profile-stats"><span><strong>{profile.quantidade_amigos}</strong><small>{profile.quantidade_amigos === 1 ? 'amigo' : 'amigos'}</small></span><span><strong>{lists.length}</strong><small>{lists.length === 1 ? 'lista' : 'listas'}</small></span><span><strong>{communities.length}</strong><small>{communities.length === 1 ? 'comunidade' : 'comunidades'}</small></span></div>
          <div className="public-profile-body">
            <section><div className="public-profile-section-title"><h3>Comunidades</h3></div>{communities.length === 0 ? <p>Você ainda não participa de comunidades.</p> : <div className="public-profile-communities">{communities.map((community) => <article key={community.id}><span aria-hidden="true">{community.nome.slice(0, 1).toUpperCase()}</span><div><strong>{community.nome}</strong><p>{community.descricao}</p></div></article>)}</div>}</section>
            <section><div className="public-profile-section-title"><h3>Últimas avaliações</h3></div>{reviews.length === 0 ? <p>Você ainda não avaliou nenhum filme.</p> : <div className="public-profile-reviews">{reviews.map((review) => <button key={review.id} onClick={() => onOpenMovie(review.filme.id)} aria-label={`Ver ${review.filme.titulo}, nota ${review.nota} de 10`}><ProfilePoster title={review.filme.titulo} url={review.filme.url_poster} /><span><small>{review.filme.ano_lancamento ?? 'ANO NÃO INFORMADO'} {review.visibilidade === 'privada' ? '· PRIVADA' : ''}</small><strong>{review.filme.titulo}</strong><em>{review.comentario || 'Sem comentário.'}</em></span><b>{review.nota}<small>/10</small></b></button>)}</div>}</section>
            <section><div className="public-profile-section-title"><h3>Suas listas</h3></div>{lists.length === 0 ? <p>Você ainda não criou listas.</p> : <div className="public-profile-lists">{lists.map((list) => <article key={list.id}><header><h4>{list.nome}</h4><span>{list.quantidade_filmes} {list.quantidade_filmes === 1 ? 'filme' : 'filmes'} · {list.visibilidade}</span></header>{list.filmes.length === 0 ? <p>Lista ainda vazia.</p> : <div>{list.filmes.slice(0, 6).map((movie) => <button key={movie.id} onClick={() => onOpenMovie(movie.id)} aria-label={`Ver ${movie.titulo}`}><ProfilePoster title={movie.titulo} url={movie.url_poster} /><span>{movie.titulo}</span></button>)}</div>}</article>)}</div>}</section>
          </div>
        </>}
      </div>
    </Dialog>
  )
}
