import { Radio, Zap, Building2, Database } from 'lucide-react'

const CARDS = [
  { key: 'active_sources',  label: 'Sources',    Icon: Radio,     color: 'text-blue-500',    bg: 'bg-blue-500/10'    },
  { key: 'new_items',       label: 'New Signals', Icon: Zap,       color: 'text-amber-400',   bg: 'bg-amber-400/10'   },
  { key: 'total_companies', label: 'Companies',   Icon: Building2, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
  { key: 'total_records',   label: 'Records',     Icon: Database,  color: 'text-slate-400',   bg: 'bg-slate-400/10'   },
]

function fmt(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

export default function StatCards({ stats }) {
  return (
    <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-6">
      {CARDS.map(({ key, label, Icon, color, bg }) => (
        <div key={key} className="bg-white rounded-xl border border-slate-100 shadow-sm px-4 py-3.5 flex items-center gap-3">
          <div className={`w-9 h-9 rounded-lg ${bg} flex items-center justify-center flex-shrink-0`}>
            <Icon size={16} className={color} />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900 leading-none">{fmt(stats[key] ?? 0)}</p>
            <p className="text-[11px] text-slate-400 mt-0.5 font-medium">{label}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
