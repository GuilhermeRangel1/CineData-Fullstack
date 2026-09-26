import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ReviewForm } from './ReviewForm'
import { json } from '../test/movie'

describe('Nova avaliação', () => {
  it.each(['0', '10'])('aceita nota %s e limpa o formulário apenas no sucesso', async (score) => {
    const fetcher = vi.fn(() => json({ id: 'r' }, 201)),
      saved = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    render(<ReviewForm movieId="1" onSaved={saved} onBusyChange={vi.fn()} />)
    await userEvent.type(screen.getByLabelText('Sua nota (0 a 10)'), score)
    fireEvent.change(screen.getByLabelText('Sua resenha'), { target: { value: ' Meu olhar. ' } })
    await userEvent.click(screen.getByRole('button', { name: 'Publicar avaliação' }))
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining('/filmes/1/avaliacoes'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          nota: Number(score),
          comentario: 'Meu olhar.',
          visibilidade: 'publica',
        }),
      }),
    )
    expect(saved).toHaveBeenCalledOnce()
    expect(screen.getByLabelText('Sua nota (0 a 10)')).toHaveValue('')
  })

  it('rejeita textos em branco e preserva o conteúdo se o filme não existir', async () => {
    const fetcher = vi.fn(() =>
        json({ codigo: 'FILME_NAO_ENCONTRADO', mensagem: 'Filme não encontrado.' }, 404),
      ),
      saved = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    render(<ReviewForm movieId="1" onSaved={saved} onBusyChange={vi.fn()} />)
    fireEvent.submit(screen.getByRole('form'))
    expect(screen.getByRole('alert')).toHaveTextContent('Escolha uma nota')
    expect(fetcher).not.toHaveBeenCalled()
    await userEvent.type(screen.getByLabelText('Sua nota (0 a 10)'), '8.5')
    fireEvent.change(screen.getByLabelText('Sua resenha'), { target: { value: 'Gostei muito.' } })
    await userEvent.click(screen.getByRole('button', { name: 'Publicar avaliação' }))
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('Filme não encontrado.'),
    )
    expect(screen.getByLabelText('Sua resenha')).toHaveValue('Gostei muito.')
    expect(saved).not.toHaveBeenCalled()
  })

  it('permite publicar uma resenha privada', async () => {
    const fetcher = vi.fn(() => json({ id: 'r' }, 201))
    vi.stubGlobal('fetch', fetcher)
    render(<ReviewForm movieId="1" onSaved={vi.fn()} onBusyChange={vi.fn()} />)
    await userEvent.type(screen.getByLabelText('Sua nota (0 a 10)'), '8')
    await userEvent.selectOptions(screen.getByLabelText('Visibilidade'), 'privada')
    fireEvent.change(screen.getByLabelText('Sua resenha'), { target: { value: 'Só minha.' } })
    await userEvent.click(screen.getByRole('button', { name: 'Publicar avaliação' }))

    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining('/filmes/1/avaliacoes'),
      expect.objectContaining({
        body: JSON.stringify({ nota: 8, comentario: 'Só minha.', visibilidade: 'privada' }),
      }),
    )
  })
})
