import { useState, type FormEvent } from 'react'
import { criarAvaliacao } from '../api/client'
import { useMutation } from '../hooks/useMutation'

export function ReviewForm({
  movieId,
  onSaved,
  onBusyChange,
}: {
  movieId: string
  onSaved: () => void
  onBusyChange: (busy: boolean) => void
}) {
  const [score, setScore] = useState('')
  const [comment, setComment] = useState('')
  const [visibility, setVisibility] = useState<'publica' | 'privada'>('publica')
  const [validation, setValidation] = useState('')
  const { pending, error, run } = useMutation(onBusyChange)
  function submit(event: FormEvent) {
    event.preventDefault()
    if (
      !comment.trim() ||
      score === '' ||
      !Number.isFinite(Number(score)) ||
      Number(score) < 0 ||
      Number(score) > 10 ||
      comment.trim().length > 4000
    ) {
      setValidation('Escolha uma nota entre 0 e 10 e escreva sua resenha.')
      return
    }
    setValidation('')
    void run(
      () =>
        criarAvaliacao(movieId, {
          nota: Number(score),
          comentario: comment.trim(),
          visibilidade: visibility,
        }),
      () => {
        setScore('')
        setComment('')
        setVisibility('publica')
        onSaved()
      },
    )
  }
  return (
    <form className="review-form" onSubmit={submit} aria-label="Avaliar filme">
      <h4>E qual é o seu olhar?</h4>
      <p className="muted">Sua nota faz parte da história. Todos os campos são obrigatórios.</p>
      <fieldset className="form-grid" disabled={pending}>
        <label>
          Sua nota (0 a 10)
          <select value={score} onChange={(event) => setScore(event.target.value)} required>
            <option value="">Escolha uma nota</option>
            {Array.from({ length: 21 }, (_, index) => index / 2).map((value) => (
              <option key={value} value={value}>
                {value.toLocaleString('pt-BR')} / 10
              </option>
            ))}
          </select>
        </label>
        <label className="full-field">
          Sua resenha
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            required
            maxLength={4000}
            rows={3}
            placeholder="Conte o que ficou com você depois dos créditos."
          />
        </label>
        <label>
          Visibilidade
          <select
            value={visibility}
            onChange={(event) => setVisibility(event.target.value as 'publica' | 'privada')}
          >
            <option value="publica">Pública — aparece no seu perfil</option>
            <option value="privada">Privada — visível somente para você</option>
          </select>
        </label>
      </fieldset>
      {(error || validation) && (
        <p role="alert" className="form-error">
          {error || validation}
        </p>
      )}
      <div className="form-actions">
        <button className="button button-light" disabled={pending}>
          {pending ? 'Enviando…' : 'Publicar avaliação'}
        </button>
      </div>
    </form>
  )
}
