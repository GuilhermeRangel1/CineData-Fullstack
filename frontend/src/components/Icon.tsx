export type IconName =
  'search' | 'play' | 'pause' | 'arrow' | 'left' | 'close' | 'volume' | 'mute' | 'film' | 'filter'

const paths: Record<IconName, string> = {
  search: 'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
  play: 'm8 4 13 8-13 8Z',
  pause: 'M8 5v14M16 5v14',
  arrow: 'M4 12h16m-6-6 6 6-6 6',
  left: 'm15 5-7 7 7 7',
  close: 'm6 6 12 12M6 18 18 6',
  volume: 'm11 4-6 5H2v6h3l6 5ZM15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14',
  mute: 'm11 4-6 5H2v6h3l6 5ZM16 9l6 6m0-6-6 6',
  film: 'M4 3h16v18H4ZM8 3v18M16 3v18M4 8h4m-4 8h4m8-8h4m-4 8h4',
  filter: 'M4 5h16M7 12h10m-7 7h4',
}

export function Icon({ name }: { name: IconName }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  )
}
