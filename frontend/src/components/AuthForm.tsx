import { useState, type FormEvent } from 'react'
import { entrar, registrar } from '../api/client'
import { salvarSessao, type Sessao } from '../auth/session'
import { useMutation } from '../hooks/useMutation'

export function AuthForm({
  mode,
  onAuthenticated,
  onBusyChange,
}: {
  mode: 'login' | 'cadastro'
  onAuthenticated: (session: Sessao) => void
  onBusyChange: (busy: boolean) => void
}) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [validation, setValidation] = useState('')
  const { pending, error, run } = useMutation(onBusyChange)
  const isRegistration = mode === 'cadastro'

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!email.trim() || !password || (isRegistration && !name.trim())) {
      setValidation('Preencha todos os campos para continuar.')
      return
    }
    if (password.length < 8) {
      setValidation('A senha precisa ter pelo menos 8 caracteres.')
      return
    }
    setValidation('')
    void run(
      async () => {
        if (isRegistration) await registrar({ nome: name.trim(), email: email.trim(), senha: password })
        return entrar({ email: email.trim(), senha: password })
      },
      (response) => onAuthenticated(salvarSessao(response)),
    )
  }

  return (
    <div className="auth-form editor-body">
      <p className="eyebrow">SUA CONTA CINEDATA</p>
      <h2>{isRegistration ? 'Crie sua conta' : 'Entre na sua conta'}</h2>
      <p className="muted">
        {isRegistration
          ? 'Avalie filmes e acompanhe seus próximos olhares.'
          : 'Entre para avaliar filmes com o seu perfil.'}
      </p>
      <form onSubmit={submit} noValidate aria-label={isRegistration ? 'Criar conta' : 'Entrar'}>
        <fieldset disabled={pending} className="form-grid">
          {isRegistration && (
            <label className="full-field">
              Seu nome
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                maxLength={120}
                autoComplete="name"
                autoFocus
                required
              />
            </label>
          )}
          <label className="full-field">
            E-mail
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              autoComplete="email"
              autoFocus={!isRegistration}
              required
            />
          </label>
          <label className="full-field">
            Senha
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              minLength={8}
              maxLength={128}
              autoComplete={isRegistration ? 'new-password' : 'current-password'}
              required
            />
          </label>
        </fieldset>
        {(error || validation) && <p role="alert" className="form-error">{error || validation}</p>}
        <div className="form-actions">
          <button className="button button-light" disabled={pending}>
            {pending ? 'Aguarde…' : isRegistration ? 'Criar conta e entrar' : 'Entrar'}
          </button>
        </div>
      </form>
    </div>
  )
}
