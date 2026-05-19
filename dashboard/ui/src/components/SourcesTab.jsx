import { timeAgo, countryStyle } from '../utils'

export default function SourcesTab({ sources }) {
  if (sources.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm py-16 text-center">
        <div className="text-4xl mb-4 opacity-20">📡</div>
        <p className="font-semibold text-slate-700">No sources configured</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <h6 className="font-semibold text-slate-700">Monitored Data Sources</h6>
        <span className="text-xs text-slate-400">{sources.length} sources configured</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-left">
              {['Status', 'Source', 'Type', 'Location', 'Records', 'Last Pull'].map(h => (
                <th key={h} className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sources.map((src, i) => {
              const { bg, text } = countryStyle(src.country)
              return (
                <tr key={i} className="border-t border-slate-50 hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`inline-block w-2.5 h-2.5 rounded-full ${src.active ? 'bg-emerald-400' : 'bg-slate-300'}`} />
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-800">{src.source_name}</td>
                  <td className="px-4 py-3">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 capitalize">
                      {(src.source_type || '').replace(/-/g, ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {src.country && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ background: bg, color: text }}>
                          {src.country === 'Ukraine' ? 'UA' : src.country === 'Moldova' ? 'MD' : src.country === 'Romania' ? 'RO' : src.country}
                        </span>
                      )}
                      <span className="text-slate-500">{src.city || ''}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-700">
                    {src.record_count ? src.record_count.toLocaleString() : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {src.last_fetched ? (
                      <span className="text-slate-400">{timeAgo(src.last_fetched)}</span>
                    ) : (
                      <span className="text-amber-600 font-medium">Pending first pull</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
