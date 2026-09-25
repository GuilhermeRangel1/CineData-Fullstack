import type { TokenAcesso, UsuarioLeitura } from '../types/api'

const SESSION_KEY = 'cinedata.session'

export interface Sessao {
  token: string
  usuario: UsuarioLeitura
}

export function carregarSessao(): Sessao | null {
  if (typeof window === 'undefined') return null
  try {
    const sessao = JSON.parse(window.localStorage.getItem(SESSION_KEY) ?? 'null') as Sessao | null
    if (!sessao?.token || !sessao.usuario?.id) return null
    return sessao
  } catch {
    return null
  }
}

export function salvarSessao(resposta: TokenAcesso): Sessao {
  const sessao = { token: resposta.access_token, usuario: resposta.usuario }
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(sessao))
  return sessao
}

export function encerrarSessao(): void {
  window.localStorage.removeItem(SESSION_KEY)
}

export function obterTokenSessao(): string | null {
  return carregarSessao()?.token ?? null
}
