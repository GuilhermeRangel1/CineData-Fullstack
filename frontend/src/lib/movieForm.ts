import type { FilmeAtualizacao, FilmeCriacao, FilmeDetalhe } from '../types/api'

export interface MovieFields {
  titulo: string
  diretor: string
  ano_lancamento: string
  generos: string
  sinopse: string
  data_lancamento: string
  url_poster: string
  url_backdrop: string
  url_trailer: string
}

export function movieFields(movie?: FilmeDetalhe): MovieFields {
  return {
    titulo: movie?.titulo ?? '',
    diretor: movie?.pessoas.find((person) => person.papel === 'Diretor')?.nome ?? '',
    ano_lancamento: movie?.ano_lancamento?.toString() ?? '',
    generos: movie?.generos.map((genre) => genre.nome).join(', ') ?? '',
    sinopse: movie?.sinopse ?? '',
    data_lancamento: movie?.data_lancamento ?? '',
    url_poster: movie?.url_poster ?? '',
    url_backdrop: movie?.url_backdrop ?? '',
    url_trailer: movie?.url_trailer ?? '',
  }
}

export function validateMovie(fields: MovieFields, original?: FilmeDetalhe) {
  const errors: Partial<Record<keyof MovieFields, string>> = {}
  const initial = movieFields(original)
  // Existing imports may have no director/genre; unchanged relationships stay untouched.
  if (!original || fields.titulo !== initial.titulo) {
    if (!fields.titulo.trim()) errors.titulo = 'Informe o título.'
    else if (fields.titulo.trim().length > 500) errors.titulo = 'Use até 500 caracteres.'
  }
  if (!original || fields.diretor !== initial.diretor) {
    if (!fields.diretor.trim()) errors.diretor = 'Informe o nome do diretor.'
    else if (fields.diretor.trim().length > 255) errors.diretor = 'Use até 255 caracteres.'
  }
  if (
    fields.ano_lancamento &&
    (!/^\d{4}$/.test(fields.ano_lancamento) ||
      Number(fields.ano_lancamento) < 1888 ||
      Number(fields.ano_lancamento) > 2100)
  ) {
    errors.ano_lancamento = 'Informe um ano entre 1888 e 2100.'
  }
  if (
    fields.data_lancamento &&
    fields.ano_lancamento &&
    fields.data_lancamento.slice(0, 4) !== fields.ano_lancamento
  ) {
    errors.data_lancamento = 'A data de lançamento deve ter o mesmo ano informado acima.'
  }
  if (fields.data_lancamento) {
    const parsed = new Date(`${fields.data_lancamento}T00:00:00Z`)
    if (
      !Number.isFinite(parsed.getTime()) ||
      parsed.toISOString().slice(0, 10) !== fields.data_lancamento ||
      fields.data_lancamento < '1888-01-01' ||
      fields.data_lancamento > '2100-12-31'
    )
      errors.data_lancamento = 'Informe uma data válida entre 1888 e 2100.'
  }
  if (!original || fields.generos !== initial.generos) {
    const genres = fields.generos.split(',').map((genre) => genre.trim())
    if (genres.some((genre) => !genre || genre.length > 50) || genres.length > 20)
      errors.generos =
        'Informe de 1 a 20 gêneros, com até 50 caracteres cada, separados por vírgulas.'
    else if (new Set(genres.map((genre) => genre.toLocaleLowerCase())).size !== genres.length)
      errors.generos = 'Não repita o mesmo gênero.'
  }
  if (fields.sinopse.trim().length > 4000) errors.sinopse = 'Use até 4.000 caracteres.'
  for (const key of ['url_poster', 'url_backdrop'] as const) {
    if (!fields[key] || fields[key] === initial[key]) continue
    try {
      const url = new URL(fields[key].trim())
      if (!['https:', 'http:'].includes(url.protocol) || fields[key].trim().length > 2048)
        throw new Error()
    } catch {
      errors[key] = 'Use um endereço completo de imagem (https:// ou http://).'
    }
  }
  if (fields.url_trailer && fields.url_trailer !== initial.url_trailer) {
    try {
      const url = new URL(fields.url_trailer.trim())
      const validHosts = ['youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtube-nocookie.com']
      if (url.protocol !== 'https:' || !validHosts.includes(url.hostname)) throw new Error()
    } catch {
      errors.url_trailer = 'Use um link HTTPS válido do YouTube.'
    }
  }
  return errors
}

export function createPayload(fields: MovieFields): FilmeCriacao {
  return {
    titulo: fields.titulo.trim(),
    diretor: fields.diretor.trim(),
    generos: fields.generos.split(',').map((genre) => genre.trim()),
    ...(fields.ano_lancamento ? { ano_lancamento: Number(fields.ano_lancamento) } : {}),
    ...Object.fromEntries(
      (['sinopse', 'data_lancamento', 'url_poster', 'url_backdrop', 'url_trailer'] as const)
        .filter((key) => fields[key].trim())
        .map((key) => [key, fields[key].trim()]),
    ),
  }
}

export function updatePayload(fields: MovieFields, movie: FilmeDetalhe): FilmeAtualizacao {
  const initial = movieFields(movie)
  const changes: FilmeAtualizacao = {}
  if (fields.titulo.trim() !== initial.titulo) changes.titulo = fields.titulo.trim()
  if (fields.diretor.trim() !== initial.diretor) changes.diretor = fields.diretor.trim()
  if (fields.generos !== initial.generos)
    changes.generos = fields.generos.split(',').map((genre) => genre.trim())
  if (fields.ano_lancamento !== initial.ano_lancamento)
    changes.ano_lancamento = fields.ano_lancamento ? Number(fields.ano_lancamento) : null
  for (const key of ['sinopse', 'data_lancamento', 'url_poster', 'url_backdrop', 'url_trailer'] as const) {
    if (fields[key].trim() !== initial[key]) changes[key] = fields[key].trim() || null
  }
  return changes
}
