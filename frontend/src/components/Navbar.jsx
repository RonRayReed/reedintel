import { RefreshCw, LogOut } from 'lucide-react'
import { formatDate } from '../utils'

export default function Navbar({ lastUpdated, onRefresh, onLogout, refreshing }) {
  const time = lastUpdated
    ? new Date(lastUpdated).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) +
      ' · ' + formatDate(lastUpdated)
    : '—'

  return (
    <nav className="bg-navy sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center font-extrabold text-navy text-sm flex-shrink-0">
            RI
          </div>
          <div>
            <div className="text-white font-bold text-lg leading-none">Reed Intel</div>
            <div className="text-white/40 text-[10px] tracking-widest uppercase">Business Intelligence</div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-white/50 text-xs">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Live · {time}
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={onRefresh}
              disabled={refreshing}
              title="Refresh data"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 text-xs font-medium transition-colors disabled:opacity-40"
            >
              <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">Refresh</span>
            </button>

            <button
              onClick={onLogout}
              title="Sign out"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 text-xs font-medium transition-colors"
            >
              <LogOut size={13} />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
