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
  const communities = profile?.comunidades ?? []
  const recentReviews = profile?.avaliacoes.slice(0, 5) ?? []
  return (
    <Dialog title={`Perfil de ${person.nome}`} className="public-profile-dialog" onClose={onClose}>
      <div className="public-profile">
        <header className="public-profile-hero"><PersonAvatar person={profile ?? person} /><div className="public-profile-identity"><p className="eyebrow">PERFIL CINEDATA</p><h2>{profile?.nome ?? person.nome}</h2><span>Filmes, listas e espaços que fazem parte deste perfil.</span></div></header>
        {error ? <p className="form-error" role="alert">{error}</p> : !profile ? <p role="status">Carregando perfil…</p> : <>
          <div className="public-profile-stats"><span><strong>{profile.quantidade_amigos}</strong><small>{profile.quantidade_amigos === 1 ? 'amigo' : 'amigos'}</small></span><span><strong>{profile.listas_publicas.length}</strong><small>{profile.listas_publicas.length === 1 ? 'lista pública' : 'listas públicas'}</small></span><span><strong>{communities.length}</strong><small>{communities.length === 1 ? 'comunidade' : 'comunidades'}</small></span></div>
          <div className="public-profile-body">
            <section><div className="public-profile-section-title"><p className="eyebrow">ONDE PARTICIPA</p><h3>Comunidades</h3></div>{communities.length === 0 ? <p>Nenhuma comunidade pública por aqui.</p> : <div className="public-profile-communities">{communities.map((community) => <article key={community.id}><span aria-hidden="true">{community.nome.slice(0, 1).toUpperCase()}</span><div><strong>{community.nome}</strong><p>{community.descricao}</p></div></article>)}</div>}</section>
            <section><div className="public-profile-section-title"><p className="eyebrow">ATIVIDADE RECENTE</p><h3>Últimas avaliações</h3></div>{recentReviews.length === 0 ? <p>Nenhuma avaliação pública.</p> : <div className="public-profile-reviews">{recentReviews.map((review) => <button key={review.id} onClick={() => onOpenMovie(review.filme.id)} aria-label={`Ver ${review.filme.titulo}, nota ${review.nota} de 10`}><ProfilePoster title={review.filme.titulo} url={review.filme.url_poster} /><span><small>{review.filme.ano_lancamento ?? 'ANO NÃO INFORMADO'}</small><strong>{review.filme.titulo}</strong><em>{review.comentario || 'Sem comentário.'}</em></span><b>{review.nota}<small>/10</small></b></button>)}</div>}</section>
            <section><div className="public-profile-section-title"><p className="eyebrow">CURADORIA PESSOAL</p><h3>Listas públicas</h3></div>{profile.listas_publicas.length === 0 ? <p>Nenhuma lista pública.</p> : <div className="public-profile-lists">{profile.listas_publicas.map((list) => <article key={list.id}><header><h4>{list.nome}</h4><span>{list.quantidade_filmes} {list.quantidade_filmes === 1 ? 'filme' : 'filmes'}</span></header>{list.filmes.length === 0 ? <p>Lista ainda vazia.</p> : <div>{list.filmes.slice(0, 6).map((movie) => <button key={movie.id} onClick={() => onOpenMovie(movie.id)} aria-label={`Ver ${movie.titulo}`}><ProfilePoster title={movie.titulo} url={movie.url_poster} /><span>{movie.titulo}</span></button>)}</div>}</article>)}</div>}</section>
          </div>
        </>}
      </div>
    </Dialog>
  )
}

function ProfilePoster({ title, url }: { title: string; url: string | null }) {
  return url ? <img src={url} alt="" loading="lazy" /> : <span className="public-profile-poster-fallback" aria-hidden="true">{title.slice(0, 1).toUpperCase()}</span>
}
