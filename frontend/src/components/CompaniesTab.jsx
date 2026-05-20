import { useState } from 'react'
import { Search } from 'lucide-react'
import { timeAgo, confidenceInfo, countryStyle } from '../utils'

export default function CompaniesTab({ companies }) {
  const [query, setQuery] = useState('')

  const filtered = companies.filter(c =>
    [c.legal_name, c.country, c.city, c.sector].some(v =>
      (v || '').toLowerCase().includes(query.toLowerCase())
    )
  )

  if (companies.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm py-16 text-center">
        <div className="text-4xl mb-4 opacity-20">🏢</div>
        <p className="font-semibold text-slate-700 mb-1">No companies tracked yet</p>
        <p className="text-slate-400 text-sm max-w-sm mx-auto">
          Company profiles will be built automatically as procurement and registry data is processed.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
        <h6 className="font-semibold text-slate-700">Market Participants</h6>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search companies…"
            className="pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-blue-400 w-56"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-left">
              {['Company Name', 'Country', 'City', 'Sector', 'Signal Strength', 'Last Seen'].map(h => (
                <th key={h} className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400 text-sm">
                  No companies match your search.
                </td>
              </tr>
            ) : (
              filtered.map((co, i) => {
                const score = co.confidence_score ?? 0
                const { color } = confidenceInfo(score)
                const pct = Math.round(score * 100)
                const { bg, text } = countryStyle(co.country)
                return (
                  <tr key={i} className="border-t border-slate-50 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-800">{co.legal_name}</td>
                    <td className="px-4 py-3">
                      {co.country ? (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded" style={{ background: bg, color: text }}>
                          {co.country}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{co.city || '—'}</td>
                    <td className="px-4 py-3">
                      {co.sector ? (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700">{co.sector}</span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
                        </div>
                        <span className="text-xs text-slate-400">{pct}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">{timeAgo(co.last_updated)}</td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
