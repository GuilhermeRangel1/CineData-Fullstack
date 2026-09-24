import { useState } from 'react'
import { Hero } from './components/Hero'
import { Icon } from './components/Icon'
import { MovieDetail } from './components/MovieDetail'
import { MovieShelf } from './components/MovieShelf'
import { Catalog } from './pages/Catalog'
import './App.css'

function App() {
  const [selected, setSelected] = useState<string | null>(null)
  const [genre, setGenre] = useState('')
  const [catalogVersion, setCatalogVersion] = useState(0)
  function explore(value: string) {
    setGenre(value)
    setCatalogVersion((version) => version + 1)
    document
      .getElementById('catalogo')
      ?.scrollIntoView({
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
        <span className="header-caption">PARA QUEM VIVE CINEMA</span>
      </header>
      <main>
        <Hero onExplore={() => explore('Animation')} />
        <div className="content-wrap">
          <div className="collection-intro" id="colecoes">
            <p className="eyebrow">HISTÓRIAS PARA TODOS OS OLHARES</p>
            <span>Explore o catálogo, um universo de cada vez.</span>
          </div>
          <MovieShelf
            title="A imaginação ganha vida."
            subtitle="Animações para ir além do mundo lá fora."
            genre="Animation"
            onOpen={setSelected}
            onExplore={explore}
          />
          <MovieShelf
            title="Fora da sua zona de conforto."
            subtitle="Grandes jornadas. Novos mundos. A próxima aventura."
            genre="Adventure"
            onOpen={setSelected}
            onExplore={explore}
          />
          <Catalog key={catalogVersion} genre={genre} onGenre={setGenre} onOpen={setSelected} />
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
      {selected && <MovieDetail id={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}

export default App
