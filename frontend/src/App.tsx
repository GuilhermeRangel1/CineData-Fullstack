import { useMemo, useState } from 'react'
import './App.css'
import { mockMovies } from './data/mockMovies'

function App() {
  const [search, setSearch] = useState('')
  const [activeSection, setActiveSection] = useState('Catálogo')
  const movies = useMemo(
    () => mockMovies.filter((movie) => movie.titulo.toLocaleLowerCase('pt-BR').includes(search.toLocaleLowerCase('pt-BR'))),
    [search],
  )

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#catalogo" aria-label="CineData, página inicial"><span className="brand-mark" aria-hidden="true">C</span><span>CineData</span></a>
        <nav aria-label="Navegação principal">
          {['Catálogo', 'Meus filmes'].map((section) => (
            <button className={activeSection === section ? 'nav-link active' : 'nav-link'} key={section} onClick={() => setActiveSection(section)} type="button">{section}</button>
          ))}
        </nav>
        <button className="add-movie" type="button">+ Adicionar filme</button>
      </header>
      <main>
        <section className="intro" aria-labelledby="page-title">
          <p className="eyebrow">Catálogo de cinema</p>
          <h1 id="page-title">Encontre seu próximo filme.</h1>
          <p className="subtitle">Explore, avalie e guarde os filmes que marcaram você.</p>
          <label className="search" htmlFor="movie-search"><span aria-hidden="true">⌕</span><input id="movie-search" onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por título" type="search" value={search} /></label>
        </section>
        <section className="catalog" id="catalogo" aria-labelledby="catalog-title">
          <div className="section-heading"><div><h2 id="catalog-title">Em destaque</h2><p>{movies.length} filmes encontrados</p></div><button className="filter" type="button">Filtrar <span aria-hidden="true">⌄</span></button></div>
          {movies.length > 0 ? (
            <div className="movie-grid">
              {movies.map((movie, index) => (
                <article className="movie-card" key={movie.id}>
                  <div className={`movie-poster poster-${index + 1}`} aria-hidden="true"><span>{movie.titulo.slice(0, 1)}</span></div>
                  <div className="movie-info"><div className="movie-title-row"><h3>{movie.titulo}</h3><span>{movie.ano_lancamento}</span></div><p className="genres">{movie.generos.map((genre) => genre.nome).join(' · ')}</p><p className="rating" aria-label={`Nota média de ${movie.nota_media}, em uma escala de 0 a 10`}><span aria-hidden="true">★</span> {movie.nota_media?.toFixed(1)} <small>/ 10 · {movie.quantidade_avaliacoes}</small></p></div>
                </article>
              ))}
            </div>
          ) : <div className="empty-state"><p>Nenhum filme encontrado para “{search}”.</p><button onClick={() => setSearch('')} type="button">Limpar busca</button></div>}
        </section>
      </main>
    </div>
  )
}

export default App
