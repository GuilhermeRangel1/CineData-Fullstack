import { useState, type ChangeEvent, type FormEvent } from 'react'
import { atualizarPerfil } from '../api/client'
import { useMutation } from '../hooks/useMutation'
import type { UsuarioLeitura } from '../types/api'

const ACCEPTED_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp'])

function readImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('Não foi possível ler a imagem.'))
    reader.onload = () => resolve(String(reader.result))
    reader.readAsDataURL(file)
  })
}

export function ProfileForm({
  user,
  onSaved,
  onBusyChange,
}: {
  user: UsuarioLeitura
  onSaved: (user: UsuarioLeitura) => void
  onBusyChange: (busy: boolean) => void
}) {
  const [name, setName] = useState(user.nome)
  const [avatar, setAvatar] = useState<string | null>(user.avatar_url ?? null)
  const [notice, setNotice] = useState('')
  const { pending, error, run } = useMutation(onBusyChange)

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    if (!ACCEPTED_TYPES.has(file.type) || file.size > 1_000_000) {
      setNotice('Escolha uma imagem PNG, JPEG ou WebP de até 1 MB.')
      event.target.value = ''
      return
    }
    setNotice('')
    void readImage(file).then(setAvatar).catch((failure: Error) => setNotice(failure.message))
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    const trimmedName = name.trim()
    if (!trimmedName) {
      setNotice('Informe seu nome para salvar o perfil.')
      return
    }
    const changes: { nome?: string; avatar_url?: string | null } = {}
    if (trimmedName !== user.nome) changes.nome = trimmedName
    if (avatar !== (user.avatar_url ?? null)) changes.avatar_url = avatar
    if (!Object.keys(changes).length) {
      setNotice('Nenhuma alteração para salvar.')
      return
    }
    setNotice('')
    void run(() => atualizarPerfil(changes), onSaved)
  }

  return (
    <div className="profile-form editor-body">
      <p className="eyebrow">SEU PERFIL CINEDATA</p>
      <h2>Seu perfil</h2>
      <p className="muted">Sua foto fica associada à sua conta e aparece ao lado do seu nome.</p>
      <form onSubmit={submit} noValidate aria-label="Editar perfil">
        <fieldset disabled={pending} className="form-grid">
          <div className="profile-preview full-field">
            {avatar ? <img src={avatar} alt="Prévia da sua foto de perfil" /> : <span>{name.trim().slice(0, 1).toUpperCase() || '?'}</span>}
          </div>
          <label className="full-field">
            Seu nome
            <input value={name} onChange={(event) => setName(event.target.value)} maxLength={120} data-initial-focus required />
          </label>
          <label className="full-field">
            Foto de perfil
            <input type="file" accept="image/png,image/jpeg,image/webp" onChange={chooseFile} />
            <span className="field-hint">PNG, JPEG ou WebP, até 1 MB.</span>
          </label>
          {avatar && (
            <button type="button" className="text-button profile-remove" onClick={() => setAvatar(null)}>
              Remover foto
            </button>
          )}
        </fieldset>
        {(error || notice) && <p className={error ? 'form-error' : 'success-message'} role={error ? 'alert' : 'status'}>{error || notice}</p>}
        <div className="form-actions">
          <button className="button button-light" disabled={pending}>{pending ? 'Salvando…' : 'Salvar perfil'}</button>
        </div>
      </form>
    </div>
  )
}
