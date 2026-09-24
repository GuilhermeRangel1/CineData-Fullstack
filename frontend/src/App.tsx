import { useState } from 'react'
import { Hero } from './components/Hero'
import { Icon } from './components/Icon'
import { MovieDetail } from './components/MovieDetail'
import { MovieShelf } from './components/MovieShelf'
import { Catalog } from './pages/Catalog'
import { Dialog } from './components/Dialog'
import { MovieForm } from './components/MovieForm'
import './App.css'

function App() {
  const [selected, setSelected] = useState<string | null>(null)
  const [genre, setGenre] = useState('')
  const [catalogVersion, setCatalogVersion] = useState(0)
  const [revision, setRevision] = useState(0)
  const [creating, setCreating] = useState(false)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const refresh = () => setRevision((value) => value + 1)
  function explore(value: string) {
    setGenre(value)
    setCatalogVersion((version) => version + 1)
    document.getElementById('catalogo')?.scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 'instant'
        : 'smooth',
    })
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#catalogo">
        Pular para o catálogo
      </a>
      <header className="topbar">
        <a className="brand" href="#inicio" aria-label="CineData Analytics, início">
          <span className="brand-symbol">
            <Icon name="film" />
          </span>
          <span className="brand-name">
            CINEDATA<small>ANALYTICS</small>
          </span>
        </a>
        <nav className="main-nav" aria-label="Navegação principal">
          <a href="#inicio">Início</a>
          <a href="#colecoes">Coleções</a>
          <a href="#catalogo">Catálogo</a>
        </nav>
        <a href="#catalogo" className="header-search">
          <Icon name="search" />
          <span>Encontrar um filme</span>
        </a>
        <button
          className="button button-outline add-movie"
          data-dialog-focus-return
          onClick={() => {
            setNotice('')
            setCreating(true)
          }}
        >
          + Adicionar filme
        </button>
      </header>
      <main>
        <Hero onExplore={() => explore('Animation')} paused={creating || selected !== null} />
        <div className="content-wrap">
          <div className="collection-intro" id="colecoes">
            <p className="eyebrow">HISTÓRIAS PARA TODOS OS OLHARES</p>
            <span>Explore o catálogo, um universo de cada vez.</span>
          </div>
          <MovieShelf
            title="A imaginação ganha vida."
            subtitle="Animações para ir além do mundo lá fora."
            genre="Animation"
            revision={revision}
            onOpen={setSelected}
            onExplore={explore}
          />
          <MovieShelf
            title="Fora da sua zona de conforto."
            subtitle="Grandes jornadas. Novos mundos. A próxima aventura."
            genre="Adventure"
            revision={revision}
            onOpen={setSelected}
            onExplore={explore}
          />
          <Catalog
            key={catalogVersion}
            revision={revision}
            genre={genre}
            onGenre={setGenre}
            onOpen={setSelected}
          />
        </div>
      </main>
      <footer className="footer">
        <a className="footer-brand" href="#inicio">
          CINEDATA <span>ANALYTICS</span>
        </a>
        <p>Histórias que ficam. Olhares que se encontram.</p>
        <details>
          <summary>Créditos do destaque</summary>
          <p>
            O Castelo Animado © 2004 Diana Wynne Jones / Hayao Miyazaki / Studio Ghibli, NDDMT.{' '}
            <a href="https://www.ghibli.jp/works/howl/" target="_blank" rel="noreferrer">
              Imagem: Studio Ghibli
            </a>
            .{' '}
            <a href="https://www.youtube.com/watch?v=2x5SejvTMeA" target="_blank" rel="noreferrer">
              Trailer: GKIDS
            </a>
            . Projeto acadêmico, sem afiliação aos estúdios.
          </p>
        </details>
      </footer>
      {notice && (
        <div className="app-notice" role="status">
          <span>{notice}</span>
          <button
            className="icon-button"
            aria-label="Dispensar mensagem"
            onClick={() => setNotice('')}
          >
            <Icon name="close" />
          </button>
        </div>
      )}
      {creating && (
        <Dialog
          title="Adicionar filme"
          className="editor-dialog"
          busy={busy}
          onClose={() => setCreating(false)}
        >
          <MovieForm
            onBusyChange={setBusy}
            onCancel={() => setCreating(false)}
            onSaved={(movie) => {
              setCreating(false)
              setNotice('Filme cadastrado com sucesso.')
              refresh()
              setSelected(movie.id)
            }}
          />
        </Dialog>
      )}
      {selected && (
        <MovieDetail
          key={selected}
          id={selected}
          onClose={() => setSelected(null)}
          onChanged={refresh}
          onDeleted={() => {
            refresh()
            setNotice('Filme e avaliações excluídos.')
            document.querySelector<HTMLElement>('.add-movie')?.focus()
          }}
        />
      )}
    </div>
  )
}

export default App
