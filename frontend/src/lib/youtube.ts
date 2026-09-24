export interface YouTubePlayer {
  playVideo(): void
  pauseVideo(): void
  mute(): void
  unMute(): void
  destroy(): void
  getIframe(): HTMLIFrameElement
}

interface PlayerEvent {
  target: YouTubePlayer
}
interface PlayerOptions {
  host: string
  videoId: string
  playerVars: Record<string, string | number>
  events: {
    onReady: (event: PlayerEvent) => void
    onStateChange: (event: PlayerEvent & { data: number }) => void
    onError: () => void
    onAutoplayBlocked: () => void
  }
}
interface YouTubeApi {
  Player: new (element: HTMLElement, options: PlayerOptions) => YouTubePlayer
}

declare global {
  interface Window {
    YT?: YouTubeApi
    onYouTubeIframeAPIReady?: () => void
  }
}

let pending: Promise<YouTubeApi> | undefined
export function loadYouTube(): Promise<YouTubeApi> {
  if (window.YT?.Player) return Promise.resolve(window.YT)
  if (pending) return pending
  pending = new Promise<YouTubeApi>((resolve, reject) => {
    const script = document.createElement('script')
    const timer = window.setTimeout(() => {
      script.remove()
      reject(new Error('O player demorou a responder.'))
    }, 12000)
    script.src = 'https://www.youtube.com/iframe_api'
    script.async = true
    script.onerror = () => {
      clearTimeout(timer)
      script.remove()
      reject(new Error('Player indisponível.'))
    }
    window.onYouTubeIframeAPIReady = () => {
      clearTimeout(timer)
      if (window.YT) resolve(window.YT)
    }
    document.head.append(script)
  }).catch((error: unknown) => {
    pending = undefined
    throw error
  })
  return pending
}

export const GHIBLI_TRAILER_ID = '2x5SejvTMeA'
export const GHIBLI_TRAILER_URL = `https://www.youtube.com/watch?v=${GHIBLI_TRAILER_ID}`
export const GHIBLI_STILL = 'https://www.ghibli.jp/gallery/howl003.jpg'
