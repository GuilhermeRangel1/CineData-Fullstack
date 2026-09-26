import { useState, type FormEvent } from 'react'
import { criarAvaliacao, removerMinhaAvaliacao } from '../api/client'
import { useMutation } from '../hooks/useMutation'
import type { AvaliacaoLeitura } from '../types/api'

export function ReviewForm({
  movieId,
  initialReview = null,
  onSaved,
  onDeleted = () => undefined,
  onBusyChange,
}: {
  movieId: string
  initialReview?: AvaliacaoLeitura | null
  onSaved: () => void
  onDeleted?: () => void
  onBusyChange: (busy: boolean) => void
}) {
  const [score, setScore] = useState(() => initialReview ? String(initialReview.nota).replace('.', ',') : '')
  const [comment, setComment] = useState(() => initialReview?.comentario ?? '')
  const [visibility, setVisibility] = useState<'publica' | 'privada'>(() => initialReview?.visibilidade ?? 'publica')
  const [validation, setValidation] = useState('')
  const [confirmingDeletion, setConfirmingDeletion] = useState(false)
  const { pending, error, run } = useMutation(onBusyChange)
  function submit(event: FormEvent) {
    event.preventDefault()
    const numericScore = Number(score.replace(',', '.'))
    if (
      !comment.trim() ||
      score === '' ||
      !Number.isFinite(numericScore) ||
      numericScore < 0 ||
      numericScore > 10 ||
      comment.trim().length > 4000
    ) {
      setValidation('Escolha uma nota entre 0 e 10 e escreva sua resenha.')
      return
    }
    setValidation('')
    void run(
      () =>
        criarAvaliacao(movieId, {
          nota: numericScore,
          comentario: comment.trim(),
          visibilidade: visibility,
        }),
      () => {
        if (!initialReview) {
          setScore('')
          setComment('')
          setVisibility('publica')
        }
        onSaved()
      },
    )
  }
  function remove() {
    if (!initialReview) return
    if (!confirmingDeletion) {
      setConfirmingDeletion(true)
      return
    }
    void run(
      () => removerMinhaAvaliacao(movieId),
      () => onDeleted(),
    )
  }
  return (
    <form className="review-form" onSubmit={submit} aria-label="Avaliar filme">
      <h4>{initialReview ? 'Editar seu olhar' : 'E qual é o seu olhar?'}</h4>
      <p className="muted">{initialReview ? 'Atualize sua nota e resenha quando quiser.' : 'Sua nota faz parte da história. Todos os campos são obrigatórios.'}</p>
      <fieldset className="form-grid" disabled={pending}>
        <label>
          Sua nota (0 a 10)
          <input
            type="text"
            inputMode="decimal"
            value={score}
            onChange={(event) => setScore(event.target.value)}
            placeholder="Ex.: 8,5"
            required
          />
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
            <option value="publica">Pública</option>
            <option value="privada">Privada</option>
          </select>
        </label>
      </fieldset>
      {(error || validation) && (
        <p role="alert" className="form-error">
          {error || validation}
        </p>
      )}
      <div className="form-actions">
        {initialReview && (
          <button
            className="text-button review-delete"
            type="button"
            disabled={pending}
            onClick={remove}
          >
            {confirmingDeletion ? 'Confirmar exclusão' : 'Apagar avaliação'}
          </button>
        )}
        <button className="button button-light" disabled={pending}>
          {pending ? 'Salvando…' : initialReview ? 'Salvar alteração' : 'Publicar avaliação'}
        </button>
      </div>
    </form>
  )
}
