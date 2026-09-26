import { useEffect, useMemo, useState } from 'react'
import { obterMapaGostos } from '../api/client'
import type { MapaGostos, NoMapaGostos } from '../types/api'
import { Icon } from './Icon'

const PALETA_DE_GENEROS = ['#ed5a86', '#aa7cf4', '#55c4d4', '#e5b65b', '#78c985', '#e88c62']

function corDoGenero(genero: string | null): string {
  if (!genero) return '#a47adf'
  return PALETA_DE_GENEROS[[...genero].reduce((total, letra) => total + letra.charCodeAt(0), 0) % PALETA_DE_GENEROS.length]
}

type Posicao = { x: number; y: number }

function distribuir(nos: NoMapaGostos[]): Map<string, Posicao> {
  const avaliados = nos.filter((no) => no.tipo === 'avaliado')
  const recomendados = nos.filter((no) => no.tipo === 'recomendado')
  const centro = { x: 500, y: 275 }
  const resultado = new Map<string, Posicao>()
  const colocar = (itens: NoMapaGostos[], raioX: number, raioY: number, deslocamento: number) => {
    itens.forEach((no, indice) => {
      const angulo = deslocamento + (Math.PI * 2 * indice) / Math.max(1, itens.length)
      resultado.set(no.id, { x: centro.x + Math.cos(angulo) * raioX, y: centro.y + Math.sin(angulo) * raioY })
    })
  }
  colocar(avaliados, avaliados.length === 1 ? 0 : 185, avaliados.length === 1 ? 0 : 130, -Math.PI / 2)
  colocar(recomendados, 390, 205, -Math.PI / 2 + Math.PI / Math.max(1, recomendados.length))
  return resultado
}

export function TasteMap({ onOpenMovie, revision = 0 }: { onOpenMovie: (id: string) => void; revision?: number }) {
  const [busca, setBusca] = useState('')
  const [dados, setDados] = useState<MapaGostos | null>(null)
  const [erro, setErro] = useState('')
  const [selecionado, setSelecionado] = useState<NoMapaGostos | null>(null)
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      void obterMapaGostos({ limiteNos: 24, vizinhosPorFilme: 3, busca }, controller.signal)
        .then((mapa) => {
          setDados(mapa)
          setErro('')
          setSelecionado((atual) => mapa.nos.find((no) => no.id === atual?.id) ?? null)
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted) setErro(error instanceof Error ? error.message : 'Não foi possível montar o mapa.')
        })
    }, busca ? 250 : 0)
    return () => {
      controller.abort()
      window.clearTimeout(timer)
    }
  }, [busca, tentativa, revision])

  const posicoes = useMemo(() => distribuir(dados?.nos ?? []), [dados])
  return (
    <main className="taste-map-page" id="mapa-de-gostos">
      <header className="taste-map-header">
        <div>
          <p className="eyebrow"><span className="red-line" />DESCOBERTA PESSOAL</p>
          <h1>Seu mapa de gostos.</h1>
          <p>Uma malha que parte do que você avaliou e revela histórias próximas por gênero, pessoas e época.</p>
        </div>
        <div className="taste-map-header-note"><span>↗</span><p>As conexões indicam por que uma sugestão apareceu para você.</p></div>
      </header>

      <div className="taste-map-content">
        <section className="taste-map-controls" aria-label="Controles do mapa de gostos">
          <label className="taste-map-search"><Icon name="search" /><span className="sr-only">Pesquisar dentro do mapa</span><input value={busca} onChange={(event) => setBusca(event.target.value)} placeholder="Buscar um filme na malha" /></label>
          <button className="taste-map-refresh" type="button" onClick={() => { setErro(''); setTentativa((valor) => valor + 1) }}>↻ Atualizar mapa</button>
        </section>

        {erro ? (
          <section className="taste-map-state" role="alert"><h2>O mapa não pôde ser aberto.</h2><p>{erro}</p><button className="button button-outline" type="button" onClick={() => setTentativa((valor) => valor + 1)}>Tentar novamente</button></section>
        ) : !dados ? (
          <section className="taste-map-loading" aria-label="Montando o mapa de gostos"><span className="skeleton" /><span className="skeleton" /><span className="skeleton" /></section>
        ) : dados.total_avaliados === 0 ? (
          <section className="taste-map-empty"><span><Icon name="film" /></span><h2>Seu mapa começa com um olhar.</h2><p>Quando você avaliar um filme, vamos conectar seus gêneros, pessoas e época a novas histórias do catálogo.</p></section>
        ) : dados.nos.length === 0 ? (
          <section className="taste-map-empty"><span><Icon name="search" /></span><h2>Nenhum ponto encontrado.</h2><p>Tente outro título para voltar a enxergar sua malha.</p></section>
        ) : (
          <section className="taste-map-workspace" aria-label="Grafo de filmes avaliados e recomendações">
            <div className="taste-map-graph-wrap">
              <svg className="taste-map-graph" viewBox="0 0 1000 550" role="img" aria-label="Grafo direcionado do seu mapa de gostos">
                <defs>
                  <marker id="taste-map-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" /></marker>
                  {dados.nos.filter((no) => no.url_poster).map((no) => <clipPath id={`clip-${no.id}`} key={`clip-${no.id}`}><circle cx="0" cy="0" r="25" /></clipPath>)}
                </defs>
                <circle className="taste-map-orbit taste-map-orbit--inner" cx="500" cy="275" r="170" />
                <ellipse className="taste-map-orbit" cx="500" cy="275" rx="390" ry="205" />
                {dados.arestas.map((aresta) => {
                  const origem = posicoes.get(aresta.origem)
                  const destino = posicoes.get(aresta.destino)
                  if (!origem || !destino) return null
                  return <line key={`${aresta.origem}-${aresta.destino}`} className="taste-map-edge" x1={origem.x} y1={origem.y} x2={destino.x} y2={destino.y} markerEnd="url(#taste-map-arrow)"><title>{aresta.explicacao}</title></line>
                })}
                {dados.nos.map((no) => {
                  const posicao = posicoes.get(no.id)
                  if (!posicao) return null
                  const cor = corDoGenero(no.genero_principal)
                  return <g className={`taste-map-node taste-map-node--${no.tipo} ${selecionado?.id === no.id ? 'is-selected' : ''}`} key={no.id} transform={`translate(${posicao.x} ${posicao.y})`} tabIndex={0} role="button" aria-label={`Abrir ${no.titulo}`} onClick={() => setSelecionado(no)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelecionado(no) } }}>
                    <circle className="taste-map-node-ring" r={no.tipo === 'avaliado' ? 35 : 30} style={{ stroke: no.tipo === 'avaliado' ? cor : undefined }} />
                    {no.url_poster ? <image href={no.url_poster} x="-25" y="-37" width="50" height="74" preserveAspectRatio="xMidYMid slice" clipPath={`url(#clip-${no.id})`} /> : <circle className="taste-map-node-fallback" r="25" style={{ fill: no.tipo === 'avaliado' ? cor : undefined }} />}
                    {no.tipo === 'avaliado' && <text className="taste-map-score" y="47">{no.nota_usuario?.toFixed(1)}</text>}
                    <text className="taste-map-label" y={no.tipo === 'avaliado' ? 62 : 45}>{encurtar(no.titulo)}</text>
                  </g>
                })}
              </svg>
            </div>
            <aside className="taste-map-inspector" aria-live="polite">
              {selecionado ? <>
                {selecionado.url_poster ? <img src={selecionado.url_poster} alt="" /> : <span className="taste-map-inspector-fallback"><Icon name="film" /></span>}
                <p className="eyebrow">{selecionado.tipo === 'avaliado' ? 'SEU OLHAR' : 'SUGESTÃO PRÓXIMA'}</p>
                <h2>{selecionado.titulo}</h2>
                <p>{selecionado.ano_lancamento ?? 'Ano não informado'} · {selecionado.generos.join(' · ') || 'Sem gênero informado'}</p>
                <strong>{selecionado.tipo === 'avaliado' ? `${selecionado.nota_usuario?.toFixed(1)} / 10` : `${Math.round((selecionado.afinidade ?? 0) * 100)}% de afinidade`}</strong>
                {selecionado.tipo === 'recomendado' && <small>{dados.arestas.find((aresta) => aresta.destino === selecionado.id)?.explicacao ?? 'Sugestão próxima ao que você avaliou.'}</small>}
                <button className="button button-outline" type="button" onClick={() => onOpenMovie(selecionado.id)}>Ver filme <Icon name="arrow" /></button>
              </> : <><span className="taste-map-inspector-hint">+</span><h2>Escolha um ponto</h2><p>Clique em um filme para ver o caminho que o trouxe até sua malha.</p></>}
            </aside>
          </section>
        )}
        {dados && dados.total_avaliados > 0 && <p className="taste-map-footnote"><b>{dados.total_avaliados}</b> {dados.total_avaliados === 1 ? 'filme avaliado alimenta' : 'filmes avaliados alimentam'} este mapa. Avalie algo novo para recalcular suas conexões.</p>}
      </div>
    </main>
  )
}

function encurtar(titulo: string): string {
  return titulo.length > 22 ? `${titulo.slice(0, 20)}…` : titulo
}
