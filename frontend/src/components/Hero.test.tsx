import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Hero } from './Hero'
import { loadYouTube } from '../lib/youtube'

vi.mock('../lib/youtube', async (original) => ({
  ...(await original<typeof import('../lib/youtube')>()),
  loadYouTube: vi.fn(),
}))
const load = vi.mocked(loadYouTube)
afterEach(() => { vi.useRealTimers() })

beforeEach(() => {
  load.mockReset()
  vi.mocked(window.matchMedia).mockImplementation(
    (query: string) =>
      ({
        matches: false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }) as unknown as MediaQueryList,
  )
})
describe('Destaque cinematográfico', () => {
  it('retorna à imagem se o iframe nunca ficar pronto', async () => {
    vi.useFakeTimers()
    class PendingPlayer { destroy() {} }
    load.mockResolvedValue({ Player: PendingPlayer } as unknown as Awaited<ReturnType<typeof loadYouTube>>)
    render(<Hero onExplore={vi.fn()} />)
    await act(async () => { await vi.advanceTimersByTimeAsync(18000) })
    expect(screen.getByText('PRÉVIA EM IMAGEM')).toBeInTheDocument()
  })
  it('mantém a imagem e o link oficial quando o player falha', async () => {
    load.mockRejectedValue(new Error('blocked'))
    render(<Hero onExplore={vi.fn()} />)
    expect(await screen.findByText('PRÉVIA EM IMAGEM')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Assistir trailer' }))
    expect(screen.getByRole('dialog')).toHaveAccessibleName('Trailer de O Castelo Animado')
    expect(screen.getByRole('link', { name: /canal oficial da GKIDS/ })).toHaveAttribute(
      'href',
      'https://www.youtube.com/watch?v=2x5SejvTMeA',
    )
  })

  it('não carrega vídeo automaticamente com movimento reduzido', async () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as unknown as MediaQueryList)
    load.mockRejectedValue(new Error('offline'))
    render(<Hero onExplore={vi.fn()} />)
    expect(load).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Reproduzir vídeo de fundo' }))
    await waitFor(() => expect(load).toHaveBeenCalledTimes(1))
  })

  it('controla pausa e som e destrói o player ao desmontar', async () => {
    const pauseVideo = vi.fn()
    const playVideo = vi.fn()
    const mute = vi.fn()
    const unMute = vi.fn()
    const destroy = vi.fn()
    type Options = ConstructorParameters<Awaited<ReturnType<typeof loadYouTube>>['Player']>[1]
    let options!: Options
    const target = {
      playVideo,
      pauseVideo,
      mute,
      unMute,
      destroy,
      getIframe: () => document.createElement('iframe'),
    }
    class Player {
      constructor(_element: HTMLElement, passed: Options) {
        options = passed
        return target
      }
    }
    load.mockResolvedValue({ Player } as unknown as Awaited<ReturnType<typeof loadYouTube>>)
    const { unmount } = render(<Hero onExplore={vi.fn()} />)
    await waitFor(() => expect(options).toBeDefined())
    act(() => {
      options.events.onReady({ target })
      options.events.onStateChange({ target, data: 1 })
    })
    expect(mute).toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Pausar vídeo de fundo' }))
    expect(pauseVideo).toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Ativar som do vídeo' }))
    expect(unMute).toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Silenciar vídeo' }))
    expect(mute).toHaveBeenCalledTimes(2)
    unmount()
    expect(destroy).toHaveBeenCalled()
  })
})
