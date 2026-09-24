import type {
  AvaliacaoCriacao,
  AvaliacaoLeitura,
  ErroApi,
  FilmeAtualizacao,
  FilmeCriacao,
  FilmeDetalhe,
  FilmeResumo,
  Pagina,
} from '../types/api'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export class ErroDaApi extends Error {
  readonly status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  const resposta = await fetch(`${apiBaseUrl}${caminho}`, {
    ...init,
    headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers },
  })

  if (!resposta.ok) {
    const erro = (await resposta.json().catch(() => null)) as ErroApi | null
    throw new ErroDaApi(erro?.mensagem ?? 'Não foi possível concluir a operação.', resposta.status)
  }
  if (resposta.status === 204) return undefined as T
  return resposta.json() as Promise<T>
}

export function listarFilmes(
  parametros: URLSearchParams,
  signal?: AbortSignal,
): Promise<Pagina<FilmeResumo>> {
  return requisitar(`/filmes?${parametros.toString()}`, { signal })
}

export function obterFilme(id: string, signal?: AbortSignal): Promise<FilmeDetalhe> {
  return requisitar(`/filmes/${encodeURIComponent(id)}`, { signal })
}

export function criarFilme(dados: FilmeCriacao): Promise<FilmeDetalhe> {
  return requisitar('/filmes', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarFilme(id: string, dados: FilmeAtualizacao): Promise<FilmeDetalhe> {
  return requisitar(`/filmes/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify(dados),
  })
}

export function removerFilme(id: string): Promise<void> {
  return requisitar(`/filmes/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function criarAvaliacao(id: string, dados: AvaliacaoCriacao): Promise<AvaliacaoLeitura> {
  return requisitar(`/filmes/${encodeURIComponent(id)}/avaliacoes`, {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}
