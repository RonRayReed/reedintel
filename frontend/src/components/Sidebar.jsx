import { Zap, Building2, FileText, Database, RefreshCw, LogOut, Radio } from 'lucide-react'
import { timeAgo } from '../utils'

const NAV = [
  { id: 'signals',   label: 'Signals',      Icon: Zap       },
  { id: 'companies', label: 'Companies',     Icon: Building2 },
  { id: 'report',    label: 'Report',        Icon: FileText  },
  { id: 'sources',   label: 'Data Sources',  Icon: Database  },
]

export default function Sidebar({ active, onChange, stats, sources, onRefresh, onLogout, refreshing }) {
  const newCount = stats?.new_items ?? 0

  return (
    <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#0b1829] flex flex-col z-40 select-none">

      {/* Brand */}
      <div className="px-5 pt-5 pb-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center font-extrabold text-white text-xs flex-shrink-0">
            RI
          </div>
          <div>
            <div className="text-white font-bold text-[13px] leading-none tracking-tight">Reed Intel</div>
            <div className="text-white/25 text-[9px] tracking-[0.15em] uppercase mt-0.5">Admin Console</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="px-3 pt-4 pb-2">
        <p className="text-white/20 text-[9px] font-bold uppercase tracking-[0.12em] px-2 mb-1.5">Workspace</p>
        {NAV.map(({ id, label, Icon }) => {
          const isActive = active === id
          return (
            <button
              key={id}
              onClick={() => onChange(id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium mb-0.5 transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
                  : 'text-white/45 hover:text-white/80 hover:bg-white/[0.05]'
              }`}
            >
              <Icon size={14} className="flex-shrink-0" />
              <span className="flex-1 text-left">{label}</span>
              {id === 'signals' && newCount > 0 && (
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                  isActive ? 'bg-white/20 text-white' : 'bg-blue-600/80 text-blue-100'
                }`}>
                  {newCount >= 1000 ? `${Math.floor(newCount / 1000)}k` : newCount}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Source health */}
      <div className="flex-1 overflow-y-auto px-3 pt-4 pb-2 min-h-0">
        <p className="text-white/20 text-[9px] font-bold uppercase tracking-[0.12em] px-2 mb-2">Source Health</p>
        <div className="space-y-0.5">
          {(sources ?? []).map((src, i) => {
            const hasData    = (src.record_count ?? 0) > 0
            const hasFetched = !!src.last_fetched
            return (
              <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-white/[0.03] group">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  src.active && hasFetched ? 'bg-emerald-400' : src.active ? 'bg-amber-400' : 'bg-white/15'
                }`} />
                <span className="text-white/35 text-[11px] truncate flex-1 group-hover:text-white/55 transition-colors">
                  {src.source_name}
                </span>
                <span className="text-white/20 text-[10px] flex-shrink-0 font-mono">
                  {hasData ? src.record_count.toLocaleString() : '—'}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Bottom actions */}
      <div className="px-3 py-3 border-t border-white/[0.06] space-y-0.5">
        <div className="flex items-center gap-2 px-2 pb-2 mb-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
          <span className="text-white/25 text-[10px]">Live · auto-refresh 5m</span>
        </div>
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium text-white/40 hover:text-white/70 hover:bg-white/[0.05] transition-all disabled:opacity-25"
        >
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
          {refreshing ? 'Refreshing…' : 'Refresh Data'}
        </button>
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium text-white/40 hover:text-white/70 hover:bg-white/[0.05] transition-all"
        >
          <LogOut size={13} />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
