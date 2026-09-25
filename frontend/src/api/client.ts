import type {
  AvaliacaoCriacao,
  AvaliacaoLeitura,
  TokenAcesso,
  ErroApi,
  FilmeAtualizacao,
  FilmeCriacao,
  FilmeDetalhe,
  FilmeResumo,
  Pagina,
  UsuarioLeitura,
} from '../types/api'
import { obterTokenSessao } from '../auth/session'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
const CACHE_TTL_MS = 60_000

type CacheEntry = { expiraEm: number; valor: unknown }
const cacheDeLeitura = new Map<string, CacheEntry>()

export class ErroDaApi extends Error {
  readonly status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  const token = obterTokenSessao()
  const resposta = await fetch(`${apiBaseUrl}${caminho}`, {
    ...init,
    headers: {
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })

  if (!resposta.ok) {
    const erro = (await resposta.json().catch(() => null)) as ErroApi | null
    throw new ErroDaApi(erro?.mensagem ?? 'Não foi possível concluir a operação.', resposta.status)
  }
  if (resposta.status === 204) return undefined as T
  return resposta.json() as Promise<T>
}

async function requisitarComCache<T>(caminho: string, signal?: AbortSignal): Promise<T> {
  const chave = `${apiBaseUrl}${caminho}`
  const entrada = cacheDeLeitura.get(chave)
  if (entrada && entrada.expiraEm > Date.now()) return entrada.valor as T

  const dados = await requisitar<T>(caminho, { signal, cache: 'no-store' })
  cacheDeLeitura.set(chave, { expiraEm: Date.now() + CACHE_TTL_MS, valor: dados })
  return dados
}

function invalidarCacheDeFilmes() {
  cacheDeLeitura.clear()
}

/** Uso exclusivo dos testes: cada caso começa sem respostas em memória. */
export function limparCacheDaApiParaTeste() {
  cacheDeLeitura.clear()
}

export function registrar(dados: {
  nome: string
  email: string
  senha: string
}): Promise<UsuarioLeitura> {
  return requisitar<UsuarioLeitura>('/auth/cadastro', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function entrar(dados: { email: string; senha: string }): Promise<TokenAcesso> {
  return requisitar<TokenAcesso>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function listarFilmes(
  parametros: URLSearchParams,
  signal?: AbortSignal,
): Promise<Pagina<FilmeResumo>> {
  return requisitarComCache(`/filmes?${parametros.toString()}`, signal)
}

export function obterFilme(id: string, signal?: AbortSignal): Promise<FilmeDetalhe> {
  return requisitarComCache(`/filmes/${encodeURIComponent(id)}`, signal)
}

export async function criarFilme(dados: FilmeCriacao): Promise<FilmeDetalhe> {
  const filme = await requisitar<FilmeDetalhe>('/filmes', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
  invalidarCacheDeFilmes()
  return filme
}

export async function atualizarFilme(id: string, dados: FilmeAtualizacao): Promise<FilmeDetalhe> {
  const filme = await requisitar<FilmeDetalhe>(`/filmes/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify(dados),
  })
  invalidarCacheDeFilmes()
  return filme
}

export async function removerFilme(id: string): Promise<void> {
  await requisitar<void>(`/filmes/${encodeURIComponent(id)}`, { method: 'DELETE' })
  invalidarCacheDeFilmes()
}

export async function criarAvaliacao(
  id: string,
  dados: AvaliacaoCriacao,
): Promise<AvaliacaoLeitura> {
  const avaliacao = await requisitar<AvaliacaoLeitura>(
    `/filmes/${encodeURIComponent(id)}/avaliacoes`,
    {
    method: 'POST',
    body: JSON.stringify(dados),
    },
  )
  invalidarCacheDeFilmes()
  return avaliacao
}
