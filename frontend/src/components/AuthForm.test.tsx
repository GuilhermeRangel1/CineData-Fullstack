import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { AuthForm } from './AuthForm'
import { json } from '../test/movie'

function renderRegistration() {
  const authenticated = vi.fn()
  render(<AuthForm mode="cadastro" onAuthenticated={authenticated} onBusyChange={vi.fn()} />)
  return authenticated
}

it('orienta uma senha de cadastro que ainda não atende aos requisitos', async () => {
  renderRegistration()
  await userEvent.type(screen.getByLabelText('Seu nome'), 'Ana')
  await userEvent.type(screen.getByLabelText('E-mail'), 'ana@example.com')
  await userEvent.type(screen.getByLabelText(/Senha/), 'somenteletras')

  expect(screen.getByText('Inclua ao menos uma letra e um número.')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Criar conta e entrar' }))
  expect(screen.getByRole('alert')).toHaveTextContent('Use uma senha com pelo menos uma letra e um número.')
})

it('explica quando o e-mail não tem formato válido antes de consultar a API', async () => {
  renderRegistration()
  await userEvent.type(screen.getByLabelText('Seu nome'), 'Ana')
  await userEvent.type(screen.getByLabelText('E-mail'), 'ana@exemplo')
  await userEvent.type(screen.getByLabelText(/Senha/), 'senha123')

  await userEvent.click(screen.getByRole('button', { name: 'Criar conta e entrar' }))
  expect(screen.getByRole('alert')).toHaveTextContent('Informe um e-mail válido, como nome@exemplo.com.')
})

it('mostra uma orientação útil quando o e-mail já possui conta', async () => {
  const authenticated = renderRegistration()
  vi.stubGlobal(
    'fetch',
    vi.fn(() => json({ codigo: 'USUARIO_JA_EXISTE', mensagem: 'Já existe uma conta com este e-mail. Tente entrar ou use outro endereço.' }, 409)),
  )
  await userEvent.type(screen.getByLabelText('Seu nome'), 'Ana')
  await userEvent.type(screen.getByLabelText('E-mail'), 'ana@example.com')
  await userEvent.type(screen.getByLabelText(/Senha/), 'senha123')

  await userEvent.click(screen.getByRole('button', { name: 'Criar conta e entrar' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Já existe uma conta com este e-mail. Tente entrar ou use outro endereço.')
  expect(authenticated).not.toHaveBeenCalled()
})

it('mantém o erro de login seguro e orienta a pessoa a conferir os dados', async () => {
  render(<AuthForm mode="login" onAuthenticated={vi.fn()} onBusyChange={vi.fn()} />)
  vi.stubGlobal(
    'fetch',
    vi.fn(() => json({ codigo: 'CREDENCIAIS_INVALIDAS', mensagem: 'E-mail ou senha inválidos. Confira os dados e tente novamente.' }, 401)),
  )
  await userEvent.type(screen.getByLabelText('E-mail'), 'ana@example.com')
  await userEvent.type(screen.getByLabelText('Senha'), 'senha123')

  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha inválidos. Confira os dados e tente novamente.')
})
