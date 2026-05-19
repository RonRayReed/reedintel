import { Radio, Zap, Building2, Database } from 'lucide-react'

const CARDS = [
  { key: 'active_sources',  label: 'Active Sources',    sub: 'Markets monitored',   Icon: Radio,     accent: 'text-blue-500' },
  { key: 'new_items',       label: 'New Signals',       sub: 'Awaiting review',     Icon: Zap,       accent: 'text-blue-600' },
  { key: 'total_companies', label: 'Companies Tracked', sub: 'Market participants', Icon: Building2, accent: 'text-emerald-500' },
  { key: 'total_records',   label: 'Data Records',      sub: 'Total collected',     Icon: Database,  accent: 'text-slate-400' },
]

export default function StatCards({ stats }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
      {CARDS.map(({ key, label, sub, Icon, accent }) => (
        <div key={key} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">{label}</p>
              <p className="text-3xl font-bold text-navy">{(stats[key] ?? 0).toLocaleString()}</p>
              <p className="text-xs text-slate-400 mt-1">{sub}</p>
            </div>
            <Icon className={`w-6 h-6 ${accent} opacity-20`} />
          </div>
        </div>
      ))}
    </div>
  )
}
