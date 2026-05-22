import { timeAgo, countryStyle } from '../utils'

const TYPE_STYLES = {
  'open-procurement': 'bg-purple-50 text-purple-700',
  'open-data':        'bg-blue-50 text-blue-700',
  'rss':              'bg-emerald-50 text-emerald-700',
  'api':              'bg-amber-50 text-amber-700',
}

export default function SourcesTab({ sources }) {
  if (sources.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm py-16 text-center">
        <div className="text-4xl mb-4 opacity-20">📡</div>
        <p className="font-semibold text-slate-700">No sources configured</p>
      </div>
    )
  }

  const active   = sources.filter(s => s.active).length
  const withData = sources.filter(s => s.record_count > 0).length

  return (
    <div>
      {/* Summary row */}
      <div className="flex items-center gap-4 mb-4 text-sm text-slate-500">
        <span>
          <span className="font-semibold text-slate-800">{active}</span> active
        </span>
        <span className="text-slate-200">|</span>
        <span>
          <span className="font-semibold text-slate-800">{withData}</span> with data
        </span>
        <span className="text-slate-200">|</span>
        <span>
          <span className="font-semibold text-slate-800">{sources.reduce((n, s) => n + (s.record_count || 0), 0).toLocaleString()}</span> total records
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {sources.map((src, i) => {
          const { bg, text } = countryStyle(src.country)
          const typeKey = (src.source_type || '').toLowerCase().replace(/_/g, '-')
          const typeCls = TYPE_STYLES[typeKey] || 'bg-slate-50 text-slate-500'
          return (
            <div
              key={i}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-col gap-3"
            >
              {/* Top row: status dot + name */}
              <div className="flex items-start gap-2.5">
                <span
                  className={`mt-1 inline-block w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                    src.active ? 'bg-emerald-400' : 'bg-slate-300'
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-800 text-sm leading-snug">{src.source_name}</p>
                  {src.city && (
                    <p className="text-xs text-slate-400 mt-0.5">{src.city}</p>
                  )}
                </div>
              </div>

              {/* Badges row */}
              <div className="flex items-center gap-1.5 flex-wrap">
                {src.source_type && (
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${typeCls}`}>
                    {src.source_type.replace(/-/g, ' ')}
                  </span>
                )}
                {src.country && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded" style={{ background: bg, color: text }}>
                    {src.country}
                  </span>
                )}
              </div>

              {/* Footer: records + last pull */}
              <div className="flex items-center justify-between text-xs border-t border-slate-50 pt-2.5">
                <span className="text-slate-500">
                  {src.record_count
                    ? <><span className="font-semibold text-slate-700">{src.record_count.toLocaleString()}</span> records</>
                    : <span className="text-slate-300">No records yet</span>
                  }
                </span>
                <span className={src.last_fetched ? 'text-slate-400' : 'text-amber-500 font-medium'}>
                  {src.last_fetched ? timeAgo(src.last_fetched) : 'Pending pull'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
