import Markdown from 'react-markdown'
import { formatDate, confidenceInfo, countryStyle } from '../utils'

function tally(signals, key) {
  const map = {}
  for (const s of signals) {
    const v = s[key]
    if (v) map[v] = (map[v] || 0) + 1
  }
  return Object.entries(map).sort((a, b) => b[1] - a[1])
}

function LiveBrief({ stats, signals }) {
  const topSignals   = [...signals].sort((a, b) => (b.confidence_score ?? 0) - (a.confidence_score ?? 0)).slice(0, 5)
  const bySector     = tally(signals, 'sector').slice(0, 5)
  const byCountry    = tally(signals, 'country').slice(0, 5)
  const newCount     = signals.filter(s => s.status === 'new').length
  const reviewCount  = signals.filter(s => s.status === 'in_review').length
  const today        = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h6 className="font-semibold text-slate-800 text-base mb-1">Live Intelligence Brief</h6>
          <p className="text-xs text-slate-400">Generated from current signals · as of {today}</p>
        </div>
        <span className="text-[11px] bg-amber-50 text-amber-700 px-3 py-1 rounded-full font-semibold">
          Week in progress — full report generated Monday
        </span>
      </div>

      {/* Summary banner */}
      <div className="px-6 py-4 bg-slate-50 border-b border-slate-100">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-3">Executive Overview</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Signals',    value: stats.total_records  },
            { label: 'New This Cycle',   value: newCount             },
            { label: 'Under Review',     value: reviewCount          },
            { label: 'Active Sources',   value: stats.active_sources },
          ].map(({ label, value }) => (
            <div key={label} className="text-center">
              <div className="text-2xl font-bold text-slate-800">{value ?? '—'}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-100">
        {/* Sector breakdown */}
        <div className="px-6 py-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-3">Activity by Sector</p>
          {bySector.length === 0 ? (
            <p className="text-sm text-slate-400">No sector data yet.</p>
          ) : (
            <div className="space-y-2">
              {bySector.map(([sector, count]) => {
                const pct = Math.round((count / signals.length) * 100)
                return (
                  <div key={sector}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium text-slate-700">{sector}</span>
                      <span className="text-slate-400">{count} signals</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-blue-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Country breakdown */}
        <div className="px-6 py-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-3">Activity by Country</p>
          {byCountry.length === 0 ? (
            <p className="text-sm text-slate-400">No country data yet.</p>
          ) : (
            <div className="space-y-2">
              {byCountry.map(([country, count]) => {
                const { bg, text } = countryStyle(country)
                const pct = Math.round((count / signals.length) * 100)
                return (
                  <div key={country}>
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span className="font-semibold px-2 py-0.5 rounded text-[10px]" style={{ background: bg, color: text }}>{country}</span>
                      <span className="text-slate-400">{count} signals · {pct}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Top signals */}
      {topSignals.length > 0 && (
        <div className="px-6 py-5 border-t border-slate-100">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-3">Highest-Confidence Signals</p>
          <div className="space-y-3">
            {topSignals.map(s => {
              const { color } = confidenceInfo(s.confidence_score ?? 0)
              const { bg, text } = countryStyle(s.country)
              return (
                <div key={s.queue_id} className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: color }} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 leading-snug">{s.title}</p>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {s.country && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ background: bg, color: text }}>{s.country}</span>
                      )}
                      {s.sector && (
                        <span className="text-[10px] text-blue-600 font-semibold">{s.sector}</span>
                      )}
                      <span className="text-[10px] text-slate-400">{formatDate(s.created_at)}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default function ReportTab({ report, stats, signals = [] }) {
  if (!report) return <LiveBrief stats={stats} signals={signals} />

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h6 className="font-semibold text-slate-800 text-base mb-1">
            {report.title || 'Weekly Intelligence Report'}
          </h6>
          {report.week_start && report.week_end && (
            <p className="text-xs text-slate-400">
              {formatDate(report.week_start)} – {formatDate(report.week_end)}
            </p>
          )}
        </div>
        <span className="text-xs text-slate-400">Generated {formatDate(report.created_at)}</span>
      </div>

      {report.executive_summary && (
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-100">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">Executive Summary</p>
          <p className="text-sm text-slate-700 leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {report.report_markdown && (
        <div className="px-6 py-5 report-content">
          <Markdown>{report.report_markdown}</Markdown>
        </div>
      )}
    </div>
  )
}
