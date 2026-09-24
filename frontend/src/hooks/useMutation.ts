import { useRef, useState } from 'react'
import { ErroDaApi } from '../api/client'

export function useMutation(onBusyChange?: (busy: boolean) => void) {
  const lock = useRef(false)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  async function run<T>(operation: () => Promise<T>, onSuccess: (value: T) => void) {
    if (lock.current) return
    lock.current = true
    setPending(true)
    setError('')
    onBusyChange?.(true)
    let result: T
    try {
      result = await operation()
    } catch (cause) {
      setError(
        cause instanceof ErroDaApi
          ? cause.message
          : 'Não foi possível confirmar a operação. Verifique sua conexão e atualize os dados antes de tentar novamente.',
      )
      return
    } finally {
      lock.current = false
      setPending(false)
      onBusyChange?.(false)
    }
    // A failed refresh must never be presented as a failed write.
    onSuccess(result)
  }
  return { pending, error, run }
}
