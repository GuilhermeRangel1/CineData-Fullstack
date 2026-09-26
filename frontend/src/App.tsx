import { useState } from 'react'
import { Hero } from './components/Hero'
import { Icon } from './components/Icon'
import { MovieDetail } from './components/MovieDetail'
import { MovieShelf } from './components/MovieShelf'
import { Catalog } from './pages/Catalog'
import { Dialog } from './components/Dialog'
import { MovieForm } from './components/MovieForm'
import { AuthForm } from './components/AuthForm'
import { ProfileForm } from './components/ProfileForm'
import { CommunityHub } from './components/CommunityHub'
import { ListHub } from './components/ListHub'
import { FriendshipHub } from './components/FriendshipHub'
import { atualizarUsuarioSessao, carregarSessao, encerrarSessao, type Sessao } from './auth/session'
import './App.css'

function App() {
  const [page, setPage] = useState<'home' | 'lists' | 'friends' | 'communities'>('home')
  const [selected, setSelected] = useState<string | null>(null)
  const [genre, setGenre] = useState('')
  const [catalogVersion, setCatalogVersion] = useState(0)
  const [revision, setRevision] = useState(0)
  const [creating, setCreating] = useState(false)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [session, setSession] = useState<Sessao | null>(() => carregarSessao())
  const [authMode, setAuthMode] = useState<'login' | 'cadastro' | null>(null)
  const [profileOpen, setProfileOpen] = useState(false)
  const refresh = () => setRevision((value) => value + 1)
  function showHome() {
    setPage('home')
  }
  function showLists() {
    setPage('lists')
  }
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
      <a className="skip-link" href={page === 'home' ? '#catalogo' : page === 'lists' ? '#minhas-listas' : page === 'friends' ? '#amigos' : '#comunidades'}>
        Pular para o conteúdo
      </a>
      <header className={`topbar ${page !== 'home' ? 'topbar--solid' : ''}`}>
        <a className="brand" href="#inicio" aria-label="CineData, início" onClick={showHome}>
          <span className="brand-symbol">
            <Icon name="film" />
          </span>
          <span className="brand-name">CINEDATA</span>
        </a>
        <nav className="main-nav" aria-label="Navegação principal">
          <a href="#inicio" onClick={showHome}>Início</a>
          <button type="button" aria-current={page === 'lists' ? 'page' : undefined} onClick={showLists}>Minhas listas</button>
          <button type="button" aria-current={page === 'friends' ? 'page' : undefined} onClick={() => setPage('friends')}>Amigos</button>
          <button type="button" aria-current={page === 'communities' ? 'page' : undefined} onClick={() => setPage('communities')}>Comunidades</button>
        </nav>
        <a href="#catalogo" className="header-search" onClick={showHome}>
          <Icon name="search" />
          <span>Encontrar um filme</span>
        </a>
        {session ? (
          <div className="account-actions">
            <button className="profile-trigger" onClick={() => setProfileOpen(true)} aria-label="Abrir seu perfil">
              {session.usuario.avatar_url ? <img src={session.usuario.avatar_url} alt="" /> : <span>{session.usuario.nome.slice(0, 1).toUpperCase()}</span>}
              <span>Olá, {session.usuario.nome}</span>
            </button>
            {session.usuario.role === 'admin' && page === 'home' && (
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
            )}
            <button
              className="text-button"
              onClick={() => {
                encerrarSessao()
                setSession(null)
              }}
            >
              Sair
            </button>
          </div>
        ) : (
          <div className="account-actions">
            <button className="text-button" onClick={() => setAuthMode('login')}>
              Entrar
            </button>
            <button className="button button-outline" onClick={() => setAuthMode('cadastro')}>
              Criar conta
            </button>
          </div>
        )}
      </header>
      {page === 'home' ? (
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
      ) : page === 'lists' ? (
        <ListHub
          key={session?.usuario.id ?? 'guest'}
          usuario={session?.usuario ?? null}
          onLoginRequested={() => setAuthMode('login')}
          onOpenMovie={setSelected}
        />
      ) : page === 'friends' ? (
        <FriendshipHub
          key={session?.usuario.id ?? 'guest'}
          usuario={session?.usuario ?? null}
          onLoginRequested={() => setAuthMode('login')}
          onOpenMovie={setSelected}
        />
      ) : (
        <main id="comunidades">
          <CommunityHub
            usuario={session?.usuario ?? null}
            onBusyChange={setBusy}
            onLoginRequested={() => setAuthMode('login')}
            onOpenMovie={setSelected}
          />
        </main>
      )}
      <footer className="footer">
        <a className="footer-brand" href="#inicio" onClick={showHome}>
          CINEDATA
        </a>
        <p>Histórias que ficam. Olhares que se encontram.</p>
        {page === 'home' ? (
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
        ) : (
          <span className="community-footer-note">Cinema é experiência coletiva.</span>
        )}
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
      {authMode && (
        <Dialog
          title={authMode === 'cadastro' ? 'Criar conta' : 'Entrar'}
          className="editor-dialog"
          busy={busy}
          onClose={() => setAuthMode(null)}
        >
          <AuthForm
            mode={authMode}
            onBusyChange={setBusy}
            onAuthenticated={(newSession) => {
              setSession(newSession)
              setAuthMode(null)
            }}
          />
        </Dialog>
      )}
      {profileOpen && session && (
        <Dialog title="Seu perfil" className="editor-dialog" busy={busy} onClose={() => setProfileOpen(false)}>
          <ProfileForm
            user={session.usuario}
            onBusyChange={setBusy}
            onSaved={(user) => {
              const updated = atualizarUsuarioSessao(user)
              if (updated) setSession(updated)
              setNotice('Perfil atualizado.')
              setProfileOpen(false)
            }}
          />
        </Dialog>
      )}
      {selected && (
        <MovieDetail
          key={`${selected}-${session?.usuario.id ?? 'guest'}`}
          id={selected}
          onClose={() => setSelected(null)}
          onChanged={refresh}
          onDeleted={() => {
            refresh()
            setNotice('Filme e avaliações excluídos.')
            document.querySelector<HTMLElement>('.add-movie')?.focus()
          }}
          usuario={session?.usuario ?? null}
          onLoginRequested={() => setAuthMode('login')}
          onOpenLists={() => {
            setSelected(null)
            setPage('lists')
          }}
        />
      )}
    </div>
  )
}

export default App
