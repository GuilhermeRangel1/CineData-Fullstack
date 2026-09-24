import { useEffect, useRef, useState } from 'react'
import {
  GHIBLI_STILL,
  GHIBLI_TRAILER_ID,
  GHIBLI_TRAILER_URL,
  loadYouTube,
  type YouTubePlayer,
} from '../lib/youtube'
import { Dialog } from './Dialog'
import { Icon } from './Icon'

export function Hero({ onExplore }: { onExplore: () => void }) {
  const host = useRef<HTMLDivElement>(null)
  const section = useRef<HTMLElement>(null)
  const player = useRef<YouTubePlayer | null>(null)
  const [ready, setReady] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(true)
  const [trailerOpen, setTrailerOpen] = useState(false)
  const [unavailable, setUnavailable] = useState(false)
  const [motionAllowed, setMotionAllowed] = useState(
    () => !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  const userPaused = useRef(false)

  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setMotionAllowed(!preference.matches)
    preference.addEventListener('change', update)
    return () => preference.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (!motionAllowed) return
    let active = true
    let instance: YouTubePlayer | undefined
    // Keep the still visible until PLAYING, never a black rectangle or an error embed.
    const timeout = window.setTimeout(() => {
      if (active) {
        setUnavailable(true)
        player.current?.pauseVideo()
      }
    }, 18000)
    loadYouTube()
      .then((api) => {
        if (!active || !host.current) return
        const mount = document.createElement('div')
        host.current.replaceChildren(mount)
        instance = new api.Player(mount, {
          host: 'https://www.youtube-nocookie.com',
          videoId: GHIBLI_TRAILER_ID,
          playerVars: {
            autoplay: 1,
            mute: 1,
            controls: 0,
            playsinline: 1,
            loop: 1,
            playlist: GHIBLI_TRAILER_ID,
            rel: 0,
            origin: window.location.origin,
          },
          events: {
            onReady: ({ target }) => {
              if (!active) return
              player.current = target
              target.getIframe().title = 'Trailer oficial de O Castelo Animado'
              target.getIframe().tabIndex = -1
              target.mute()
              setMuted(true)
              target.playVideo()
            },
            onStateChange: ({ data }) => {
              if (!active) return
              setPlaying(data === 1)
              if (data === 1) {
                clearTimeout(timeout)
                setReady(true)
                setUnavailable(false)
              }
            },
            onError: () => {
              if (active) {
                clearTimeout(timeout)
                setUnavailable(true)
                setPlaying(false)
              }
            },
            onAutoplayBlocked: () => {
              if (active) {
                clearTimeout(timeout)
                setUnavailable(true)
              }
            },
          },
        })
      })
      .catch(() => {
        if (active) {
          clearTimeout(timeout)
          setUnavailable(true)
        }
      })
    return () => {
      active = false
      clearTimeout(timeout)
      instance?.destroy()
      player.current = null
      setReady(false)
      setPlaying(false)
    }
  }, [motionAllowed])

  useEffect(() => {
    const visible = { current: true }
    const synchronize = () => {
      if (document.hidden || !visible.current || trailerOpen || userPaused.current)
        player.current?.pauseVideo()
      else if (ready && !unavailable) player.current?.playVideo()
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        visible.current = entry.isIntersecting
        synchronize()
      },
      { threshold: 0.15 },
    )
    if (section.current) observer.observe(section.current)
    document.addEventListener('visibilitychange', synchronize)
    synchronize()
    return () => {
      observer.disconnect()
      document.removeEventListener('visibilitychange', synchronize)
    }
  }, [ready, trailerOpen, unavailable])

  function togglePlayback() {
    if (!motionAllowed) {
      userPaused.current = false
      setMotionAllowed(true)
      return
    }
    userPaused.current = playing
    if (playing) player.current?.pauseVideo()
    else player.current?.playVideo()
  }
  function toggleSound() {
    if (muted) player.current?.unMute()
    else player.current?.mute()
    setMuted(!muted)
  }

  return (
    <>
      <section className="hero" id="inicio" aria-labelledby="hero-title" ref={section}>
        <img className="hero-still" src={GHIBLI_STILL} alt="" fetchPriority="high" />
        <div
          className={`hero-video ${ready && !unavailable && motionAllowed ? 'is-ready' : ''}`}
          ref={host}
          aria-hidden="true"
        />
        <div className="hero-shade" />
        <div className="hero-content">
          <p className="eyebrow">
            <span className="red-line" /> EM CENA · STUDIO GHIBLI
          </p>
          <h1 id="hero-title">
            O Castelo
            <br />
            <span>Animado</span>
          </h1>
          <div className="hero-meta">
            <span>2004</span>
            <span>1h 59min</span>
            <span>Hayao Miyazaki</span>
          </div>
          <p className="hero-description">
            Uma maldição. Um castelo que caminha.
            <br className="desktop-break" /> E um encontro capaz de transformar tudo.
          </p>
          <div className="hero-genres">
            <span>Animação</span>
            <span>Fantasia</span>
            <span>Aventura</span>
          </div>
          <div className="hero-actions">
            <button className="button button-light" onClick={() => setTrailerOpen(true)}>
              <Icon name="play" /> Assistir trailer
            </button>
            <button className="button button-glass" onClick={onExplore}>
              Explorar animações <Icon name="arrow" />
            </button>
          </div>
          <p className="hero-credit">Seleção editorial · Trailer oficial por GKIDS</p>
        </div>
        <div className="hero-bottom">
          <a href="#colecoes" className="hero-scroll">
            DESCUBRA OUTRAS HISTÓRIAS <span>↓</span>
          </a>
          <div className="playback-controls">
            {!unavailable && (
              <>
                <button
                  className="icon-button"
                  onClick={togglePlayback}
                  aria-label={playing ? 'Pausar vídeo de fundo' : 'Reproduzir vídeo de fundo'}
                >
                  <Icon name={playing ? 'pause' : 'play'} />
                </button>
                {ready && (
                  <button
                    className="icon-button"
                    onClick={toggleSound}
                    aria-label={muted ? 'Ativar som do vídeo' : 'Silenciar vídeo'}
                  >
                    <Icon name={muted ? 'mute' : 'volume'} />
                  </button>
                )}
              </>
            )}
            <span>
              {unavailable ? 'PRÉVIA EM IMAGEM' : playing ? 'TRAILER OFICIAL' : 'STUDIO GHIBLI'}
            </span>
          </div>
        </div>
      </section>
      {trailerOpen && (
        <Dialog
          title="Trailer de O Castelo Animado"
          className="trailer-dialog"
          onClose={() => setTrailerOpen(false)}
        >
          <h2>
            O Castelo Animado <span>Trailer oficial</span>
          </h2>
          <iframe
            title="Assistir ao trailer oficial de O Castelo Animado"
            src={`https://www.youtube-nocookie.com/embed/${GHIBLI_TRAILER_ID}?autoplay=1&rel=0&origin=${encodeURIComponent(window.location.origin)}`}
            allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
            allowFullScreen
            referrerPolicy="strict-origin-when-cross-origin"
          />
          <p>
            Se o player não estiver disponível,{' '}
            <a href={GHIBLI_TRAILER_URL} target="_blank" rel="noreferrer">
              assista no canal oficial da GKIDS ↗
            </a>
            .
          </p>
        </Dialog>
      )}
    </>
  )
}
