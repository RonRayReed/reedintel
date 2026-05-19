export default function TabBar({ tabs, active, onChange, newCount }) {
  return (
    <div className="flex gap-1 bg-white rounded-xl p-1.5 border border-slate-200 shadow-sm mb-5 overflow-x-auto">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`flex-1 min-w-max px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
            active === tab.id
              ? 'bg-navy text-white shadow-sm'
              : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
          }`}
        >
          {tab.label}
          {tab.id === 'signals' && newCount > 0 && (
            <span className="ml-2 inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold">
              {newCount}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}
