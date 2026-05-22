import { Zap, Building2, FileText, Database } from 'lucide-react'

const TAB_ICONS = {
  signals:   Zap,
  companies: Building2,
  report:    FileText,
  sources:   Database,
}

export default function TabBar({ tabs, active, onChange, newCount }) {
  return (
    <div className="flex gap-1 bg-white rounded-xl p-1.5 border border-slate-200 shadow-sm mb-5 overflow-x-auto">
      {tabs.map(tab => {
        const Icon = TAB_ICONS[tab.id]
        const isActive = active === tab.id
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`flex-1 min-w-max px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap flex items-center justify-center gap-2 ${
              isActive
                ? 'bg-navy text-white shadow-sm'
                : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
            }`}
          >
            {Icon && <Icon size={14} className={isActive ? 'opacity-90' : 'opacity-50'} />}
            {tab.label}
            {tab.id === 'signals' && newCount > 0 && (
              <span className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold ${
                isActive ? 'bg-white/20 text-white' : 'bg-blue-100 text-blue-700'
              }`}>
                {newCount}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
