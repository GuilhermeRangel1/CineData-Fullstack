import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { Dialog } from './Dialog'

it('bloqueia Escape, clique fora e fechamento enquanto uma escrita está em andamento', async () => {
  const close = vi.fn()
  const { rerender } = render(
    <Dialog title="Formulário" busy onClose={close}>
      <p>Enviando…</p>
    </Dialog>,
  )
  fireEvent(screen.getByRole('dialog'), new Event('cancel', { cancelable: true }))
  fireEvent.click(screen.getByRole('dialog'))
  await userEvent.click(screen.getByRole('button', { name: 'Fechar' }))
  expect(close).not.toHaveBeenCalled()
  rerender(
    <Dialog title="Formulário" onClose={close}>
      <p>Concluído</p>
    </Dialog>,
  )
  fireEvent(screen.getByRole('dialog'), new Event('cancel', { cancelable: true }))
  expect(close).toHaveBeenCalledOnce()
})

it('foca o campo inicial e devolve o foco ao acionador ao fechar', () => {
  const opener = document.createElement('button')
  document.body.appendChild(opener)
  opener.focus()
  const { unmount } = render(
    <Dialog title="Formulário" onClose={vi.fn()}>
      <input aria-label="Título" data-initial-focus />
    </Dialog>,
  )
  expect(screen.getByLabelText('Título')).toHaveFocus()
  expect(document.body.style.overflow).toBe('hidden')
  unmount()
  expect(opener).toHaveFocus()
  expect(document.body.style.overflow).toBe('')
  opener.remove()
})
