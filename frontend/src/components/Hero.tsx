import { useEffect, useRef, useState } from 'react'
import {
  HOME_STILL,
  HOME_TRAILER_ID,
  HOME_TRAILER_URL,
  loadYouTube,
  type YouTubePlayer,
} from '../lib/youtube'
import { Dialog } from './Dialog'
import { Icon } from './Icon'

const DELAY_DE_ABERTURA_MS = 450
const DELAY_DE_REVELACAO_MS = 4200

export function Hero({ onExplore, paused = false }: { onExplore: () => void; paused?: boolean }) {
  const host = useRef<HTMLDivElement>(null)
  const section = useRef<HTMLElement>(null)
  const player = useRef<YouTubePlayer | null>(null)
  const delay = useRef<number | null>(null)
  const revealDelay = useRef<number | null>(null)
  const userPaused = useRef(false)
  const [shouldLoad, setShouldLoad] = useState(false)
  const [ready, setReady] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(true)
  const [unavailable, setUnavailable] = useState(false)
  const [trailerOpen, setTrailerOpen] = useState(false)

  useEffect(() => {
    function clearDelay() {
      if (delay.current !== null) window.clearTimeout(delay.current)
      delay.current = null
    }
    function reset() {
      clearDelay()
      if (revealDelay.current !== null) window.clearTimeout(revealDelay.current)
      revealDelay.current = null
      userPaused.current = false
      setShouldLoad(false)
      setReady(false)
      setPlaying(false)
    }
    function start() {
      if (paused || trailerOpen || userPaused.current) return
      clearDelay()
      setUnavailable(false)
      delay.current = window.setTimeout(() => {
        setShouldLoad(true)
        delay.current = null
      }, DELAY_DE_ABERTURA_MS)
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) start()
        else reset()
      },
      { threshold: 0.2 },
    )
    if (section.current) observer.observe(section.current)
    start()
    return () => {
      clearDelay()
      observer.disconnect()
    }
  }, [paused, trailerOpen])

  useEffect(() => {
    if (!shouldLoad) return
    let active = true
    let instance: YouTubePlayer | undefined
    const hostElement = host.current
    let fallbackShown = false
    let fallbackTimer: number | undefined
    const clearFallbackTimer = () => {
      if (fallbackTimer !== undefined) window.clearTimeout(fallbackTimer)
      fallbackTimer = undefined
    }
    const revealVideo = () => {
      if (revealDelay.current !== null) window.clearTimeout(revealDelay.current)
      revealDelay.current = window.setTimeout(() => {
        if (active) setReady(true)
        revealDelay.current = null
      }, DELAY_DE_REVELACAO_MS)
    }
    const showFallback = () => {
      if (!active || !hostElement) return
      fallbackShown = true
      clearFallbackTimer()
      const iframe = document.createElement('iframe')
      iframe.title = 'Trailer oficial de Spider-Man: Across the Spider-Verse'
      iframe.src = `https://www.youtube-nocookie.com/embed/${HOME_TRAILER_ID}?autoplay=1&mute=1&controls=0&loop=1&playlist=${HOME_TRAILER_ID}&rel=0`
      iframe.allow = 'autoplay; encrypted-media; fullscreen; picture-in-picture'
      iframe.allowFullscreen = true
      iframe.referrerPolicy = 'strict-origin-when-cross-origin'
      iframe.onload = () => {
        if (!active) return
        setPlaying(true)
        setUnavailable(false)
        revealVideo()
      }
      hostElement.replaceChildren(iframe)
      setReady(false)
      setPlaying(false)
      setUnavailable(false)
    }
    fallbackTimer = window.setTimeout(showFallback, 3500)
    const timeout = window.setTimeout(() => {
      if (!active) return
      setUnavailable(true)
      setPlaying(false)
      setReady(false)
    }, 18000)

    void loadYouTube()
      .then((api) => {
        if (!active || !hostElement || fallbackShown) return
        clearFallbackTimer()
        const mount = document.createElement('div')
        hostElement.replaceChildren(mount)
        instance = new api.Player(mount, {
          host: 'https://www.youtube-nocookie.com',
          videoId: HOME_TRAILER_ID,
          playerVars: {
            autoplay: 1,
            mute: 1,
            controls: 0,
            disablekb: 1,
            modestbranding: 1,
            playsinline: 1,
            loop: 1,
            playlist: HOME_TRAILER_ID,
            rel: 0,
            origin: window.location.origin,
          },
          events: {
            onReady: ({ target }) => {
              if (!active) return
              player.current = target
              target.getIframe().title = 'Trailer oficial de Spider-Man: Across the Spider-Verse'
              target.getIframe().tabIndex = -1
              target.mute()
              setMuted(true)
              target.playVideo()
            },
            onStateChange: ({ data }) => {
              if (!active) return
              if (data === 1) {
                window.clearTimeout(timeout)
                setPlaying(true)
                setUnavailable(false)
                revealVideo()
              } else if (data === 2) {
                if (revealDelay.current !== null) window.clearTimeout(revealDelay.current)
                revealDelay.current = null
                setPlaying(false)
              }
            },
            onError: () => {
              if (!active) return
              window.clearTimeout(timeout)
              showFallback()
            },
            onAutoplayBlocked: () => {
              if (!active) return
              window.clearTimeout(timeout)
              setPlaying(false)
            },
          },
        })
      })
      .catch(() => {
        if (!active) return
        window.clearTimeout(timeout)
        showFallback()
      })

    return () => {
      active = false
      clearFallbackTimer()
      if (revealDelay.current !== null) window.clearTimeout(revealDelay.current)
      revealDelay.current = null
      window.clearTimeout(timeout)
      instance?.destroy()
      player.current = null
      hostElement?.replaceChildren()
    }
  }, [shouldLoad])

  function togglePlayback() {
    if (playing) {
      userPaused.current = true
      player.current?.pauseVideo()
      setPlaying(false)
      return
    }
    userPaused.current = false
    player.current?.playVideo()
  }

  function toggleSound() {
    if (muted) player.current?.unMute()
    else player.current?.mute()
    setMuted(!muted)
  }

  const status = unavailable
    ? 'PRÉVIA EM IMAGEM'
    : playing
      ? 'TRAILER OFICIAL'
      : shouldLoad
        ? 'PREPARANDO TRAILER'
        : 'PRÉVIA EM IMAGEM'

  return (
    <>
      <section className="hero hero--editorial" id="inicio" aria-labelledby="hero-title" ref={section}>
        <img className="hero-still" src={HOME_STILL} alt="" fetchPriority="high" />
        <div
          className={`hero-video ${ready && playing && !unavailable ? 'is-ready' : ''}`}
          ref={host}
          aria-hidden="true"
        />
        <div className="hero-shade" />
        <div className="hero-content">
          <p className="eyebrow">
            <span className="red-line" /> ANIMAÇÃO · SONY PICTURES ANIMATION
          </p>
          <h1 id="hero-title" className="hero-title-long">
            Spider-Man:
            <br />
            <span>Across the</span>
            <br />
            Spider-Verse
          </h1>
          <div className="hero-meta">
            <span>2023</span>
            <span>2h 20min</span>
            <span>Dir. Joaquim Dos Santos</span>
          </div>
          <p className="hero-description">
            Miles Morales atravessa o multiverso e encontra outras versões do Homem-Aranha.
          </p>
          <div className="hero-genres">
            <span>Animação</span>
            <span>Ação</span>
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
          <p className="hero-credit">Seleção editorial · Trailer oficial da Sony Pictures</p>
        </div>
        <div className="hero-bottom">
          <a href="#colecoes" className="hero-scroll">
            DESCUBRA OUTRAS HISTÓRIAS <span>↓</span>
          </a>
          <div className="playback-controls">
            {shouldLoad && !unavailable && (
              <button
                className="icon-button"
                onClick={togglePlayback}
                aria-label={playing ? 'Pausar vídeo de fundo' : 'Reproduzir vídeo de fundo'}
              >
                <Icon name={playing ? 'pause' : 'play'} />
              </button>
            )}
            {ready && !unavailable && (
              <button
                className="icon-button"
                onClick={toggleSound}
                aria-label={muted ? 'Ativar som do vídeo' : 'Silenciar vídeo'}
              >
                <Icon name={muted ? 'mute' : 'volume'} />
              </button>
            )}
            <span>{status}</span>
          </div>
        </div>
      </section>
      {trailerOpen && (
        <Dialog
          title="Trailer de Spider-Man: Across the Spider-Verse"
          className="trailer-dialog"
          onClose={() => setTrailerOpen(false)}
        >
          <h2>
            Spider-Man: Across the Spider-Verse <span>Trailer oficial</span>
          </h2>
          <iframe
            title="Assistir ao trailer oficial de Spider-Man: Across the Spider-Verse"
            src={`https://www.youtube-nocookie.com/embed/${HOME_TRAILER_ID}?autoplay=1&rel=0&origin=${encodeURIComponent(window.location.origin)}`}
            allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
            allowFullScreen
            referrerPolicy="strict-origin-when-cross-origin"
          />
          <p>
            Se o player não estiver disponível,{' '}
            <a href={HOME_TRAILER_URL} target="_blank" rel="noreferrer">
              assista no YouTube ↗
            </a>
            .
          </p>
        </Dialog>
      )}
    </>
  )
}
