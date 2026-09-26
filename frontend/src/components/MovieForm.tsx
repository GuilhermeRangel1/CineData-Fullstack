import { useRef, useState, type FormEvent } from 'react'
import { atualizarFilme, criarFilme } from '../api/client'
import { useMutation } from '../hooks/useMutation'
import {
  createPayload,
  movieFields,
  updatePayload,
  validateMovie,
  type MovieFields,
} from '../lib/movieForm'
import type { FilmeDetalhe } from '../types/api'

export function MovieForm({
  movie,
  onSaved,
  onCancel,
  onBusyChange,
}: {
  movie?: FilmeDetalhe
  onSaved: (movie: FilmeDetalhe) => void
  onCancel: () => void
  onBusyChange: (busy: boolean) => void
}) {
  const [fields, setFields] = useState(() => movieFields(movie))
  const [errors, setErrors] = useState<Partial<Record<keyof MovieFields, string>>>({})
  const [notice, setNotice] = useState('')
  const form = useRef<HTMLFormElement>(null)
  const { pending, error, run } = useMutation(onBusyChange)
  function submit(event: FormEvent) {
    event.preventDefault()
    const invalid = validateMovie(fields, movie)
    setErrors(invalid)
    setNotice('')
    const first = Object.keys(invalid)[0]
    if (first) {
      form.current?.querySelector<HTMLElement>(`[name="${first}"]`)?.focus()
      return
    }
    if (movie) {
      const changes = updatePayload(fields, movie)
      if (!Object.keys(changes).length) {
        setNotice('Nenhuma alteração para salvar.')
        return
      }
      void run(() => atualizarFilme(movie.id, changes), onSaved)
    } else void run(() => criarFilme(createPayload(fields)), onSaved)
  }
  function input(key: keyof MovieFields) {
    return {
      id: `movie-${key}`,
      name: key,
      value: fields[key],
      'aria-labelledby': `label-${key}`,
      'aria-invalid': Boolean(errors[key]),
      'aria-describedby': errors[key] ? `error-${key}` : undefined,
      onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        setFields({ ...fields, [key]: event.target.value }),
    }
  }
  const message = (key: keyof MovieFields) =>
    errors[key] && (
      <span className="field-error" id={`error-${key}`}>
        {errors[key]}
      </span>
    )
  return (
    <div className="editor-body">
      <p className="eyebrow">SEU CATÁLOGO, SUAS HISTÓRIAS</p>
      <h2>{movie ? 'Editar filme' : 'Adicionar filme'}</h2>
      <p className="muted">
        {movie
          ? 'Ajuste os detalhes desta história.'
          : 'Abra espaço para a próxima grande história.'}{' '}
        Campos com * são obrigatórios.
      </p>
      <form
        ref={form}
        onSubmit={submit}
        noValidate
        aria-label={movie ? 'Editar filme' : 'Adicionar filme'}
      >
        <fieldset disabled={pending} className="form-grid">
          <label className="full-field">
            <span id="label-titulo">Título *</span>
            <input {...input('titulo')} maxLength={500} autoFocus data-initial-focus required />
            {message('titulo')}
          </label>
          <label>
            <span id="label-diretor">Diretor{!movie && ' *'}</span>
            <input {...input('diretor')} maxLength={255} required={!movie} />
            {message('diretor')}
          </label>
          <label>
            <span id="label-ano_lancamento">Ano de lançamento</span>
            <input
              {...input('ano_lancamento')}
              inputMode="numeric"
              maxLength={4}
              placeholder="Ex.: 2004"
            />
            {message('ano_lancamento')}
          </label>
          {movie && movie.pessoas.filter((person) => person.papel === 'Diretor').length > 1 && (
            <p className="field-hint full-field">
              Este filme possui vários diretores. Alterar o campo Diretor substitui todos eles pelo
              nome informado; sem alteração, todos são preservados.
            </p>
          )}
          <label className="full-field">
            <span id="label-generos">Gêneros{!movie && ' *'}</span>
            <input
              {...input('generos')}
              placeholder="Ex.: Animation, Adventure"
              aria-describedby={errors.generos ? 'error-generos genre-hint' : 'genre-hint'}
            />
            {message('generos')}
            <span id="genre-hint" className="field-hint">
              Separe por vírgulas. Para aparecer nas coleções, use Animation ou Adventure, como na
              base original.
            </span>
          </label>
          <label className="full-field">
            <span id="label-sinopse">Sinopse</span>
            <textarea
              {...input('sinopse')}
              rows={4}
              maxLength={4000}
              placeholder="O que torna esse filme uma história que fica?"
            />
            {message('sinopse')}
          </label>
          <label className="full-field">
            <span id="label-data_lancamento">Data de lançamento</span>
            <input {...input('data_lancamento')} type="date" min="1888-01-01" max="2100-12-31" />
            {message('data_lancamento')}
          </label>
          <label className="full-field">
            <span id="label-url_poster">Link do pôster</span>
            <input {...input('url_poster')} type="url" maxLength={2048} placeholder="https://…" />
            {message('url_poster')}
          </label>
          <label className="full-field">
            <span id="label-url_backdrop">Link da imagem de fundo</span>
            <input {...input('url_backdrop')} type="url" maxLength={2048} placeholder="https://…" />
            {message('url_backdrop')}
          </label>
          <label className="full-field">
            <span id="label-url_trailer">Link do trailer no YouTube</span>
            <input {...input('url_trailer')} type="url" maxLength={2048} placeholder="https://www.youtube.com/watch?v=…" />
            {message('url_trailer')}
            <span className="field-hint">Opcional. Somente links HTTPS do YouTube são aceitos.</span>
          </label>
        </fieldset>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {notice && <p role="status">{notice}</p>}
        <div className="form-actions">
          <button
            type="button"
            className="button button-outline"
            onClick={onCancel}
            disabled={pending}
          >
            Cancelar
          </button>
          <button className="button button-light" disabled={pending}>
            {pending ? 'Salvando…' : movie ? 'Salvar alterações' : 'Cadastrar filme'}
          </button>
        </div>
      </form>
    </div>
  )
}
