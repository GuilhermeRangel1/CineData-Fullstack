import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MovieForm } from './MovieForm'
import { createPayload, movieFields, updatePayload, validateMovie } from '../lib/movieForm'
import { json, movie } from '../test/movie'

describe('Formulário de filme', () => {
  it('valida campos vazios, ano, data, gêneros repetidos e imagens antes de enviar', () => {
    expect(validateMovie(movieFields())).toMatchObject({
      titulo: expect.any(String),
      diretor: expect.any(String),
      generos: expect.any(String),
    })
    expect(
      validateMovie({
        ...movieFields(movie),
        ano_lancamento: '1800',
        generos: 'Drama, drama',
        url_poster: 'javascript:alert(1)',
      }),
    ).toMatchObject({
      ano_lancamento: expect.any(String),
      generos: expect.any(String),
      url_poster: expect.any(String),
    })
    expect(
      validateMovie({ ...movieFields(movie), data_lancamento: '2004-02-30' }).data_lancamento,
    ).toBeTruthy()
    expect(
      validateMovie({ ...movieFields(movie), ano_lancamento: '2026' }).data_lancamento,
    ).toBeTruthy()
    expect(
      validateMovie({ ...movieFields(movie), data_lancamento: '', ano_lancamento: '2100' }),
    ).toEqual({})
    expect(
      validateMovie({ ...movieFields(movie), data_lancamento: '', ano_lancamento: '1888' }),
    ).toEqual({})
  })

  it('envia somente campos alterados e usa null para limpar opcionais', () => {
    expect(updatePayload(movieFields(movie), movie)).toEqual({})
    expect(
      updatePayload(
        {
          ...movieFields(movie),
          titulo: ' Novo título ',
          sinopse: '',
          ano_lancamento: '',
          data_lancamento: '',
        },
        movie,
      ),
    ).toEqual({ titulo: 'Novo título', sinopse: null, ano_lancamento: null, data_lancamento: null })
    const incomplete = { ...movie, pessoas: [], generos: [] }
    expect(validateMovie({ ...movieFields(incomplete), titulo: 'Renomeado' }, incomplete)).toEqual(
      {},
    )
    expect(updatePayload({ ...movieFields(incomplete), titulo: 'Renomeado' }, incomplete)).toEqual({
      titulo: 'Renomeado',
    })
    expect(createPayload(movieFields(movie))).not.toHaveProperty('produtoras')
  })

  it('mostra validação, foca o primeiro campo e não chama a API', async () => {
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    render(<MovieForm onSaved={vi.fn()} onCancel={vi.fn()} onBusyChange={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Cadastrar filme' }))
    expect(screen.getByLabelText('Título *')).toHaveFocus()
    expect(screen.getByText('Informe o título.')).toBeInTheDocument()
    expect(fetcher).not.toHaveBeenCalled()
  })

  it('cadastra com dados normalizados, bloqueia envio duplo e libera ao terminar', async () => {
    let finish!: (value: Response) => void
    const fetcher = vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve
        }),
    )
    vi.stubGlobal('fetch', fetcher)
    const saved = vi.fn(),
      busy = vi.fn()
    render(<MovieForm onSaved={saved} onCancel={vi.fn()} onBusyChange={busy} />)
    fireEvent.change(screen.getByLabelText('Título *'), { target: { value: ' História ' } })
    fireEvent.change(screen.getByLabelText('Diretor *'), { target: { value: ' Cineasta ' } })
    fireEvent.change(screen.getByLabelText('Gêneros *'), {
      target: { value: 'Animation, Adventure' },
    })
    const form = screen.getByRole('form', { name: 'Adicionar filme' })
    fireEvent.submit(form)
    fireEvent.submit(form)
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled()
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining('/filmes'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          titulo: 'História',
          diretor: 'Cineasta',
          generos: ['Animation', 'Adventure'],
        }),
      }),
    )
    await act(async () => finish(new Response(JSON.stringify(movie), { status: 201 })))
    expect(saved).toHaveBeenCalledWith(movie)
    expect(busy.mock.calls).toEqual([[true], [false]])
  })

  it('preserva os valores em falha e permite corrigir/repetir um PATCH sem apagar relações', async () => {
    const fetcher = vi
      .fn()
      .mockImplementationOnce(() =>
        json({ codigo: 'FALHA_DE_PERSISTENCIA', mensagem: 'Não foi possível salvar.' }, 500),
      )
      .mockImplementation(() => json(movie))
    vi.stubGlobal('fetch', fetcher)
    const saved = vi.fn()
    render(<MovieForm movie={movie} onSaved={saved} onCancel={vi.fn()} onBusyChange={vi.fn()} />)
    fireEvent.change(screen.getByLabelText('Título *'), { target: { value: 'História revisada' } })
    await userEvent.click(screen.getByRole('button', { name: 'Salvar alterações' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível salvar.')
    expect(screen.getByLabelText('Título *')).toHaveValue('História revisada')
    expect(saved).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Salvar alterações' }))
    expect(fetcher.mock.lastCall![1]).toMatchObject({
      method: 'PATCH',
      body: '{"titulo":"História revisada"}',
    })
    expect(saved).toHaveBeenCalledOnce()
  })

  it('não envia edição sem alterações e pode cancelar', async () => {
    const fetcher = vi.fn(),
      cancel = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    render(<MovieForm movie={movie} onSaved={vi.fn()} onCancel={cancel} onBusyChange={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Salvar alterações' }))
    expect(screen.getByRole('status')).toHaveTextContent('Nenhuma alteração')
    expect(fetcher).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('preenche apenas campos vazios com o resultado escolhido no TMDB', async () => {
    const fetcher = vi.fn((url: string) => {
      if (url.includes('/busca'))
        return json([{ id: 4935, titulo: 'O Castelo Animado', ano_lancamento: 2004, url_poster: null }])
      return json({
        titulo: 'O Castelo Animado', diretor: 'Hayao Miyazaki', generos: ['Animação', 'Fantasia'],
        sinopse: 'Uma jovem encontra um castelo.', ano_lancamento: 2004, data_lancamento: '2004-11-20',
        url_poster: 'https://image.test/poster.jpg', url_backdrop: null,
        url_trailer: 'https://www.youtube.com/watch?v=trailer',
      })
    })
    vi.stubGlobal('fetch', fetcher)
    render(<MovieForm onSaved={vi.fn()} onCancel={vi.fn()} onBusyChange={vi.fn()} />)
    fireEvent.change(screen.getByLabelText('Título *'), { target: { value: 'Meu título manual' } })
    await userEvent.click(screen.getByRole('button', { name: 'Buscar dados no TMDB' }))
    await userEvent.type(screen.getByLabelText('Título no TMDB'), 'Castelo')
    await userEvent.click(screen.getByRole('button', { name: 'Buscar' }))
    await userEvent.click(await screen.findByRole('button', { name: /O Castelo Animado/ }))
    expect(await screen.findByRole('status')).toHaveTextContent('campos que estavam vazios')
    expect(screen.getByLabelText('Título *')).toHaveValue('Meu título manual')
    expect(screen.getByLabelText('Diretor *')).toHaveValue('Hayao Miyazaki')
    expect(screen.getByLabelText('Gêneros *')).toHaveValue('Animação, Fantasia')
  })
})
