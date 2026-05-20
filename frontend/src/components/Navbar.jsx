import { formatDate } from '../utils'

export default function Navbar({ lastUpdated }) {
  const time = lastUpdated
    ? new Date(lastUpdated).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) +
      ' UTC, ' +
      formatDate(lastUpdated)
    : '—'

  return (
    <nav className="bg-navy sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center font-extrabold text-navy text-sm flex-shrink-0">
            RI
          </div>
          <div>
            <div className="text-white font-bold text-lg leading-none">Reed Intel</div>
            <div className="text-white/50 text-[10px] tracking-widest uppercase">Business Intelligence</div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-white/60 text-xs">
          <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          Live &nbsp;|&nbsp; Updated {time}
        </div>
      </div>
    </nav>
  )
}
