import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { obterResumoAnalytics } from '../api/client'
import type { PontoEvolucaoAnalytics, ResumoAnalytics } from '../types/api'
import { Icon } from './Icon'

const PERIODOS = [7, 30, 90] as const
const numero = new Intl.NumberFormat('pt-BR')

export function AnalyticsDashboard({ onOpenMovie }: { onOpenMovie: (id: string) => void }) {
  const [periodo, setPeriodo] = useState<(typeof PERIODOS)[number]>(30)
  const [dados, setDados] = useState<ResumoAnalytics | null>(null)
  const [erro, setErro] = useState('')
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    void obterResumoAnalytics(periodo, controller.signal)
      .then((resumo) => setDados(resumo))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setErro(error instanceof Error ? error.message : 'Não foi possível carregar os indicadores.')
        }
      })
    return () => controller.abort()
  }, [periodo, tentativa])

  const maiorGenero = useMemo(
    () => Math.max(1, ...(dados?.generos.map((genero) => genero.quantidade) ?? [])),
    [dados],
  )

  return (
    <main className="analytics-page" id="analytics">
      <header className="analytics-header">
        <div>
          <p className="eyebrow"><span className="red-line" />PAINEL ADMINISTRATIVO</p>
          <h1>Analytics</h1>
        </div>
        <div className="analytics-period" aria-label="Período analisado">
          <span>Período</span>
          {PERIODOS.map((dias) => (
            <button
              key={dias}
              type="button"
              aria-pressed={periodo === dias}
              onClick={() => {
                setDados(null)
                setErro('')
                setPeriodo(dias)
              }}
            >
              {dias} dias
            </button>
          ))}
        </div>
      </header>

      <div className="analytics-content">
        {erro ? (
          <section className="analytics-state" role="alert">
            <h2>Não foi possível abrir os indicadores.</h2>
            <p>{erro}</p>
            <button type="button" className="button button-outline" onClick={() => {
              setDados(null)
              setErro('')
              setTentativa((valor) => valor + 1)
            }}>
              Tentar novamente
            </button>
          </section>
        ) : !dados ? (
          <section className="analytics-loading" aria-label="Carregando indicadores">
            {Array.from({ length: 5 }, (_, indice) => <span className="skeleton" key={indice} />)}
          </section>
        ) : (
          <>
            <section className="analytics-metrics" aria-label="Resumo da plataforma">
              {dados.metricas.map((metrica) => (
                <article key={metrica.chave}>
                  <span>{metrica.rotulo}</span>
                  <strong>{numero.format(metrica.valor)}</strong>
                  <small>{metrica.detalhe}</small>
                </article>
              ))}
            </section>

            <section className="analytics-chart-panel" aria-labelledby="analytics-evolucao">
              <div className="analytics-section-heading">
                <div>
                  <p className="eyebrow">ATIVIDADE RECENTE</p>
                  <h2 id="analytics-evolucao">Atividade da comunidade</h2>
                </div>
                <span>Últimos {dados.periodo_dias} dias</span>
              </div>
              <ActivityChart pontos={dados.evolucao} />
            </section>

            <section className="analytics-two-columns">
              <article className="analytics-panel" aria-labelledby="analytics-generos">
                <div className="analytics-section-heading">
                  <div>
                    <p className="eyebrow">CATÁLOGO</p>
                    <h2 id="analytics-generos">Gêneros mais avaliados</h2>
                  </div>
                  <span>No período selecionado</span>
                </div>
                {dados.generos.length ? (
                  <ol className="analytics-genre-list">
                    {dados.generos.map((genero) => (
                      <li key={genero.nome}>
                        <span><b>{genero.nome}</b><small>{genero.nota_media !== null ? `média ${genero.nota_media.toFixed(1)}` : 'sem média'}</small></span>
                        <i><b style={{ width: `${(genero.quantidade / maiorGenero) * 100}%` }} /></i>
                        <strong>{numero.format(genero.quantidade)}</strong>
                      </li>
                    ))}
                  </ol>
                ) : <EmptyAnalytics>Os gêneros aparecerão aqui quando houver filmes cadastrados.</EmptyAnalytics>}
              </article>

              <article className="analytics-panel" aria-labelledby="analytics-comunidades">
                <div className="analytics-section-heading">
                  <div>
                    <p className="eyebrow">CONVERSA</p>
                    <h2 id="analytics-comunidades">Comunidades em alta</h2>
                  </div>
                  <span>Por atividade recente</span>
                </div>
                {dados.comunidades_em_alta.length ? (
                  <ol className="analytics-community-list">
                    {dados.comunidades_em_alta.map((comunidade) => (
                      <li key={comunidade.id}>
                        {comunidade.imagem_url ? <img src={comunidade.imagem_url} alt="" /> : <span><Icon name="film" /></span>}
                        <div><strong>{comunidade.nome}</strong><small>{numero.format(comunidade.membros)} membros · {numero.format(comunidade.publicacoes)} publicações</small></div>
                        <em>{numero.format(comunidade.visualizacoes)}<small>visitas</small></em>
                      </li>
                    ))}
                  </ol>
                ) : <EmptyAnalytics>As comunidades criadas aparecerão neste ranking.</EmptyAnalytics>}
              </article>
            </section>

            <section className="analytics-panel analytics-movies" aria-labelledby="analytics-filmes">
              <div className="analytics-section-heading">
                <div>
                  <p className="eyebrow">RECEPÇÃO DO PÚBLICO</p>
                  <h2 id="analytics-filmes">Filmes mais avaliados pela comunidade</h2>
                </div>
                <span>No período selecionado</span>
              </div>
              {dados.filmes_mais_avaliados.length ? (
                <ol className="analytics-movie-list">
                  {dados.filmes_mais_avaliados.map((filme, indice) => (
                    <li key={filme.id}>
                      <b>{String(indice + 1).padStart(2, '0')}</b>
                      <button type="button" onClick={() => onOpenMovie(filme.id)}>
                        {filme.url_poster ? <img src={filme.url_poster} alt="" /> : <span className="analytics-poster-fallback"><Icon name="film" /></span>}
                        <span><strong>{filme.titulo}</strong><small>{numero.format(filme.quantidade_avaliacoes)} avaliações</small></span>
                      </button>
                      <em>{filme.nota_media?.toFixed(1) ?? '—'}<small>média</small></em>
                    </li>
                  ))}
                </ol>
              ) : <EmptyAnalytics>As avaliações do catálogo formarão este ranking.</EmptyAnalytics>}
            </section>
          </>
        )}
      </div>
    </main>
  )
}

function ActivityChart({ pontos }: { pontos: PontoEvolucaoAnalytics[] }) {
  const linhas = [
    { chave: 'usuarios' as const, nome: 'Pessoas', cor: '#82dc91' },
    { chave: 'avaliacoes' as const, nome: 'Avaliações', cor: '#f4c95d' },
    { chave: 'listas' as const, nome: 'Listas', cor: '#e5a26f' },
    { chave: 'publicacoes' as const, nome: 'Publicações', cor: '#f2656d' },
  ]
  const maximo = Math.max(1, ...pontos.flatMap((ponto) => linhas.map((linha) => ponto[linha.chave])))
  const ultimoPonto = pontos[pontos.length - 1]
  const ultimo = ultimoPonto?.data ? new Date(`${ultimoPonto.data}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }) : ''
  const primeiro = pontos[0]?.data ? new Date(`${pontos[0].data}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }) : ''
  const pointsFor = (chave: (typeof linhas)[number]['chave']) => pontos.map((ponto, indice) => {
    const x = pontos.length === 1 ? 300 : 12 + (indice / (pontos.length - 1)) * 576
    const y = 168 - (ponto[chave] / maximo) * 144
    return `${x},${y}`
  }).join(' ')

  return <div className="analytics-chart-wrap">
    <div className="analytics-legend">{linhas.map((linha) => <span key={linha.chave}><i style={{ background: linha.cor }} />{linha.nome}</span>)}</div>
    <svg className="analytics-chart" viewBox="0 0 600 180" role="img" aria-label="Atividade de pessoas, avaliações, listas e publicações">
      {[24, 72, 120, 168].map((y) => <line key={y} x1="12" x2="588" y1={y} y2={y} />)}
      {linhas.map((linha) => <polyline key={linha.chave} points={pointsFor(linha.chave)} stroke={linha.cor} />)}
    </svg>
    <div className="analytics-chart-dates"><span>{primeiro}</span><span>{ultimo}</span></div>
  </div>
}

function EmptyAnalytics({ children }: { children: ReactNode }) {
  return <p className="analytics-empty">{children}</p>
}
