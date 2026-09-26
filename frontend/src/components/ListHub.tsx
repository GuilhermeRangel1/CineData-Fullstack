import { useEffect, useState, type FormEvent } from 'react'
import {
  adicionarFilmeALista,
  criarLista,
  listarFilmes,
  listarFilmesAvaliados,
  listarListas,
  obterLista,
  atualizarLista,
  removerFilmeDaLista,
  removerLista,
} from '../api/client'
import type { FilmeResumo, ListaDetalhe, ListaLeitura, UsuarioLeitura, VisibilidadeLista } from '../types/api'
import { MovieCard } from './MovieCard'
import { Dialog } from './Dialog'
import { Icon } from './Icon'

type Editor = 'create' | ListaLeitura | null

export function ListHub({ usuario, onLoginRequested, onOpenMovie }: {
  usuario: UsuarioLeitura | null
  onLoginRequested: () => void
  onOpenMovie: (id: string) => void
}) {
  const userId = usuario?.id
  const [lists, setLists] = useState<ListaLeitura[]>([])
  const [rated, setRated] = useState<FilmeResumo[]>([])
  const [selected, setSelected] = useState<ListaDetalhe | null>(null)
  const [editor, setEditor] = useState<Editor>(null)
  const [deleting, setDeleting] = useState<ListaLeitura | null>(null)
  const [name, setName] = useState('')
  const [visibility, setVisibility] = useState<VisibilidadeLista>('privada')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<FilmeResumo[]>([])
  const [loading, setLoading] = useState(Boolean(userId))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!userId) return
    const controller = new AbortController()
    void Promise.all([
      listarListas(controller.signal),
      listarFilmesAvaliados(controller.signal),
    ])
      .then(([personalLists, reviewed]) => {
        setLists(personalLists)
        setRated(reviewed)
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
    const selectedId = selected?.id
    if (!selectedId || query.trim().length < 2) return
    const controller = new AbortController()
    const timeout = window.setTimeout(() => {
      const parameters = new URLSearchParams({ busca: query.trim(), tamanho_pagina: '6' })
      void listarFilmes(parameters, controller.signal)
        .then((page) => setResults(page.itens))
        .catch((failure: Error) => {
          if (!controller.signal.aborted) setError(failure.message)
        })
    }, 250)
    return () => {
      controller.abort()
      window.clearTimeout(timeout)
    }
  }, [query, selected?.id])

  function openEditor(value: Editor) {
    setError('')
    setName(value && value !== 'create' ? value.nome : '')
    setVisibility(value && value !== 'create' ? value.visibilidade : 'privada')
    setEditor(value)
  }

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

  function replaceList(list: ListaLeitura) {
    setLists((items) => [...items.filter((item) => item.id !== list.id), list].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR')))
  }

  async function openList(list: ListaLeitura) {
    await manage(async () => {
      const detail = await obterLista(list.id)
      setSelected(detail)
      setQuery('')
      setResults([])
    })
  }

  async function saveList(event: FormEvent) {
    event.preventDefault()
    if (!editor || !name.trim()) return
    await manage(async () => {
      const saved = editor === 'create'
        ? await criarLista({ nome: name.trim(), visibilidade: visibility })
        : await atualizarLista(editor.id, { nome: name.trim(), visibilidade: visibility })
      replaceList(saved)
      if (selected?.id === saved.id) setSelected((current) => current ? { ...current, ...saved } : current)
      setEditor(null)
    })
  }

  if (!usuario) {
    return <main className="list-page list-page--guest" id="minhas-listas">
      <section className="list-guest-panel">
        <p className="eyebrow"><span className="red-line" />SUA EXPERIÊNCIA, DO SEU JEITO</p>
        <h1>Suas listas começam aqui.</h1>
        <p>Monte seleções próprias, guarde seus favoritos e acompanhe tudo o que você já avaliou.</p>
        <button className="button button-light" onClick={onLoginRequested}>Entrar para organizar filmes</button>
      </section>
    </main>
  }

  return <main className="list-page" id="minhas-listas">
    <header className="list-header">
      <div>
        <p className="eyebrow"><span className="red-line" />SUA EXPERIÊNCIA, DO SEU JEITO</p>
        <h1>Minhas listas</h1>
        <p>Organize o que quer ver, o que já marcou você e suas próximas sessões.</p>
      </div>
      <button className="button button-light" onClick={() => openEditor('create')}>+ Criar lista</button>
    </header>
    <div className="list-content">
      {error && !editor && !deleting && <p className="form-error" role="alert">{error}</p>}
      {loading ? <p role="status">Carregando suas listas…</p> : <>
        <section aria-labelledby="personal-lists-title">
          <div className="list-section-heading"><div><p className="eyebrow">SELEÇÕES PESSOAIS</p><h2 id="personal-lists-title">Criadas por você</h2></div><span>{lists.length} {lists.length === 1 ? 'lista' : 'listas'}</span></div>
          {lists.length === 0 ? <div className="list-empty"><h3>Qual filme vai entrar na primeira?</h3><p>Crie uma lista para montar sua próxima sessão ou registrar um recorte especial.</p><button className="button button-outline" onClick={() => openEditor('create')}>Criar primeira lista</button></div> :
            <div className="personal-list-grid">{lists.map((list) => <article className={`personal-list-card ${selected?.id === list.id ? 'is-open' : ''}`} key={list.id}>
              <button className="personal-list-open" onClick={() => void openList(list)} disabled={busy} aria-label={`Abrir lista ${list.nome}`}>
                <ListCover list={list} />
                <span><small>{list.visibilidade === 'publica' ? 'PÚBLICA' : 'PRIVADA'}</small><strong>{list.nome}</strong><em>{list.quantidade_filmes} {list.quantidade_filmes === 1 ? 'filme' : 'filmes'}</em></span>
              </button>
              <div className="personal-list-actions"><button className="text-button" onClick={() => openEditor(list)}>Editar</button><button className="text-button danger-text" onClick={() => { setError(''); setDeleting(list) }}>Excluir</button></div>
            </article>)}</div>}
        </section>

        {selected && <section className="list-detail" aria-labelledby="selected-list-title">
          <div className="list-section-heading"><div><p className="eyebrow">EDITANDO LISTA</p><h2 id="selected-list-title">{selected.nome}</h2></div><button className="text-button" onClick={() => setSelected(null)}>Fechar lista</button></div>
          <div className="list-add-movie"><label htmlFor="list-movie-search">Adicionar um filme<input id="list-movie-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Busque por título" autoComplete="off" /></label>
            {query.trim().length >= 2 && <div className="list-search-results">{results.length === 0 ? <p>Nenhum filme encontrado.</p> : results.map((movie) => <button key={movie.id} disabled={busy || selected.filmes.some((item) => item.id === movie.id)} onClick={() => void manage(async () => { const updated = await adicionarFilmeALista(selected.id, movie.id); setSelected(updated); replaceList(updated); setQuery(''); setResults([]) })}><span>{movie.titulo}<small>{movie.ano_lancamento ?? 'Ano não informado'}</small></span><b>{selected.filmes.some((item) => item.id === movie.id) ? 'Já está na lista' : '+ Adicionar'}</b></button>)}</div>}
          </div>
          {selected.filmes.length === 0 ? <p className="muted">Esta lista ainda está vazia. Busque um filme acima para começar.</p> : <div className="list-movie-grid">{selected.filmes.map((movie) => <article className="list-movie-card" key={movie.id}><MovieCard movie={movie} onOpen={onOpenMovie} /><button className="text-button danger-text" disabled={busy} onClick={() => void manage(async () => { await removerFilmeDaLista(selected.id, movie.id); const updated = { ...selected, filmes: selected.filmes.filter((item) => item.id !== movie.id), quantidade_filmes: selected.quantidade_filmes - 1 }; setSelected(updated); replaceList(updated) })}>Remover da lista</button></article>)}</div>}
        </section>}

        <section className="virtual-lists" aria-labelledby="virtual-lists-title">
          <div className="list-section-heading"><div><p className="eyebrow">ACOMPANHE SUA JORNADA</p><h2 id="virtual-lists-title">Listas automáticas</h2></div></div>
          <div className="virtual-list-grid">
            <MovieCollection title="Filmes avaliados" description="Seu histórico de filmes que receberam uma avaliação." movies={rated} onOpenMovie={onOpenMovie} />
          </div>
        </section>
      </>}
    </div>
    {editor && <Dialog title={editor === 'create' ? 'Criar lista' : 'Editar lista'} className="editor-dialog" busy={busy} onClose={() => setEditor(null)}><form className="list-editor" onSubmit={saveList}><p className="eyebrow">SUA SELEÇÃO</p><h2>{editor === 'create' ? 'Uma nova lista' : 'Ajustar lista'}</h2><label>Nome da lista<input data-initial-focus value={name} onChange={(event) => setName(event.target.value)} maxLength={120} required /></label><label>Visibilidade<select value={visibility} onChange={(event) => setVisibility(event.target.value as VisibilidadeLista)}><option value="privada">Privada — só você vê</option><option value="publica">Pública — aparece no seu perfil</option></select></label>{error && <p className="form-error" role="alert">{error}</p>}<div className="form-actions"><button type="button" className="button button-outline" onClick={() => setEditor(null)} disabled={busy}>Cancelar</button><button className="button button-light" disabled={busy}>{editor === 'create' ? 'Criar lista' : 'Salvar alterações'}</button></div></form></Dialog>}
    {deleting && <Dialog title="Excluir lista" className="editor-dialog" busy={busy} onClose={() => setDeleting(null)}><div className="list-editor"><p className="eyebrow">AÇÃO IRREVERSÍVEL</p><h2>Excluir {deleting.nome}?</h2><p>Os filmes continuarão no catálogo; só esta seleção será removida.</p>{error && <p className="form-error" role="alert">{error}</p>}<div className="form-actions"><button className="button button-outline" data-initial-focus onClick={() => setDeleting(null)} disabled={busy}>Cancelar</button><button className="button button-danger" disabled={busy} onClick={() => void manage(async () => { await removerLista(deleting.id); setLists((items) => items.filter((item) => item.id !== deleting.id)); if (selected?.id === deleting.id) setSelected(null); setDeleting(null) })}>Excluir lista</button></div></div></Dialog>}
  </main>
}

function ListCover({ list }: { list: ListaLeitura }) {
  const [failed, setFailed] = useState(false)
  if (list.capa_url && !failed) {
    return <img className="personal-list-cover" src={list.capa_url} alt="" loading="lazy" onError={() => setFailed(true)} />
  }
  return <span className="personal-list-icon" aria-hidden="true"><Icon name="film" /></span>
}

function MovieCollection({ title, description, movies, onOpenMovie }: {
  title: string
  description: string
  movies: FilmeResumo[]
  onOpenMovie: (id: string) => void
}) {
  return <section className="virtual-list-card"><header><h3>{title}</h3><p>{description}</p></header>{movies.length === 0 ? <p className="muted">Nenhum filme por aqui ainda.</p> : <div className="virtual-movie-grid">{movies.map((movie) => <MovieCard key={movie.id} movie={movie} onOpen={onOpenMovie} />)}</div>}</section>
}
