import { useMemo, useState } from 'react'
import { Search, TrendingUp } from 'lucide-react'
import { timeAgo, confidenceInfo, countryStyle } from '../utils'

function deriveFromSignals(signals) {
  const map = {}
  for (const s of signals) {
    const sector  = s.sector  || 'General'
    const country = s.country || 'Unknown'
    const key = `${sector}||${country}`
    if (!map[key]) {
      map[key] = {
        legal_name:       sector,
        country,
        city:             s.city || null,
        sector,
        confidence_score: 0,
        source_system:    'ProZorro',
        last_updated:     s.created_at,
        _count:           0,
        _scoreSum:        0,
      }
    }
    map[key]._count++
    map[key]._scoreSum += s.confidence_score || 0
    if (s.created_at > map[key].last_updated) map[key].last_updated = s.created_at
  }
  return Object.values(map)
    .map(r => ({ ...r, confidence_score: r._scoreSum / r._count, _signals: r._count }))
    .sort((a, b) => b._count - a._count)
}

export default function CompaniesTab({ companies, signals = [] }) {
  const [query, setQuery] = useState('')

  const isDerived = companies.length === 0
  const rows = useMemo(
    () => isDerived ? deriveFromSignals(signals) : companies,
    [companies, signals, isDerived]
  )

  const filtered = rows.filter(c =>
    [c.legal_name, c.country, c.city, c.sector].some(v =>
      (v || '').toLowerCase().includes(query.toLowerCase())
    )
  )

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h6 className="font-semibold text-slate-700">Market Participants</h6>
          {isDerived && (
            <p className="text-[11px] text-amber-600 mt-0.5 flex items-center gap-1">
              <TrendingUp size={11} />
              Showing sector activity derived from intelligence signals — company profiles populate over time
            </p>
          )}
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search…"
            className="pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-lg bg-slate-50 focus:outline-none focus:border-blue-400 w-48"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-left">
              {[
                isDerived ? 'Sector' : 'Company Name',
                'Country', 'City', 'Sector',
                isDerived ? 'Signal Count' : 'Signal Strength',
                'Last Seen'
              ].map(h => (
                <th key={h} className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400 whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-slate-400 text-sm">
                  {rows.length === 0
                    ? 'No intelligence signals collected yet — data will appear as the worker processes sources.'
                    : 'No results match your search.'}
                </td>
              </tr>
            ) : (
              filtered.map((co, i) => {
                const score    = co.confidence_score ?? 0
                const { color } = confidenceInfo(score)
                const pct      = Math.round(score * 100)
                const { bg, text } = countryStyle(co.country)
                return (
                  <tr key={i} className="border-t border-slate-50 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-800">
                      {co.legal_name}
                      {isDerived && co._signals && (
                        <span className="ml-2 text-[10px] text-slate-400 font-normal">{co._signals} signals</span>
                      )}
                    </td>
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
                      {isDerived ? (
                        <span className="font-semibold text-slate-700">{co._signals}</span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                            <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
                          </div>
                          <span className="text-xs text-slate-400">{pct}%</span>
                        </div>
                      )}
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
