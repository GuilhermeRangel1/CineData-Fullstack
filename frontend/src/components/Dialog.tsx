import { useEffect, useRef, type ReactNode } from 'react'
import { Icon } from './Icon'

export function Dialog({
  title,
  onClose,
  children,
  className = '',
  busy = false,
}: {
  title: string
  onClose: () => void
  children: ReactNode
  className?: string
  busy?: boolean
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = ref.current
    const previous = document.activeElement as HTMLElement | null
    const overflow = document.body.style.overflow
    dialog?.showModal()
    dialog?.querySelector<HTMLElement>('[data-initial-focus]')?.focus()
    document.body.style.overflow = 'hidden'
    return () => {
      dialog?.close()
      document.body.style.overflow = overflow
      if (previous?.isConnected) previous.focus()
      else document.querySelector<HTMLElement>('[data-dialog-focus-return]')?.focus()
    }
  }, [])
  return (
    <dialog
      ref={ref}
      className={className}
      aria-label={title}
      onCancel={(event) => {
        event.preventDefault()
        if (!busy) onClose()
      }}
      onClick={(event) => {
        if (!busy && event.target === ref.current) onClose()
      }}
    >
      <div className="dialog-content">
        <button
          className="icon-button dialog-close"
          aria-label="Fechar"
          onClick={onClose}
          disabled={busy}
        >
          <Icon name="close" />
        </button>
        {children}
      </div>
    </dialog>
  )
}
