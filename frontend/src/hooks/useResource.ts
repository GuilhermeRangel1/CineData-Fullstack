import { useEffect, useState } from 'react'
import { ErroDaApi } from '../api/client'

// The caller memoizes the loader. Aborting protects searches and closing dialogs
// from late responses replacing newer results.
export function useResource<T>(loader: (signal: AbortSignal) => Promise<T>) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState<{
    loader: typeof loader
    attempt: number
    data: T | null
    loading: boolean
    error: string
  }>({ loader, attempt, data: null, loading: true, error: '' })
  useEffect(() => {
    const controller = new AbortController()
    loader(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted)
          setState({ loader, attempt, data, loading: false, error: '' })
      },
      (error: unknown) => {
        if (!controller.signal.aborted)
          setState({
            loader,
            attempt,
            data: null,
            loading: false,
            error:
              error instanceof ErroDaApi
                ? error.message
                : 'Não foi possível conectar ao catálogo. Tente novamente em instantes.',
          })
      },
    )
    return () => controller.abort()
  }, [loader, attempt])
  const current =
    state.loader === loader && state.attempt === attempt
      ? state
      : { data: null, loading: true, error: '' }
  return { ...current, retry: () => setAttempt((value) => value + 1) }
}
