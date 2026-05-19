import { useState } from 'react'
import { ExternalLink, MapPin } from 'lucide-react'
import { formatDate, confidenceInfo, countryStyle } from '../utils'

const FILTERS = ['all', 'new', 'in_review', 'published']

function SignalStrength({ score }) {
  const { label, color } = confidenceInfo(score ?? 0)
  const filled = Math.round((score ?? 0) * 5)
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-end gap-0.5" style={{ height: 16 }}>
        {[4, 7, 10, 13, 16].map((h, i) => (
          <div
            key={i}
            style={{
              width: 5, height: h, borderRadius: 2,
              background: i < filled ? color : '#e2e8f0',
            }}
          />
        ))}
      </div>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  )
}

function CountryBadge({ country }) {
  if (!country) return null
  const { bg, text } = countryStyle(country)
  return (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded" style={{ background: bg, color: text }}>
      {country}
    </span>
  )
}

const STATUS_STYLES = {
  new:        'bg-blue-50 text-blue-700',
  in_review:  'bg-amber-50 text-amber-700',
  published:  'bg-emerald-50 text-emerald-700',
}

const BORDER_COLORS = {
  new:        'border-l-blue-500',
  in_review:  'border-l-amber-500',
  published:  'border-l-emerald-500',
}

export default function SignalsTab({ signals }) {
  const [filter, setFilter] = useState('all')

  const visible = filter === 'all' ? signals : signals.filter(s => s.status === filter)

  return (
    <div>
      {/* Filter row */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
              filter === f
                ? 'bg-navy text-white'
                : 'bg-white border border-slate-200 text-slate-500 hover:border-slate-300'
            }`}
          >
            {f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState
          title="No signals yet"
          desc="Intelligence signals will appear here as data collection systems process new procurement and market activity."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {visible.map(item => (
            <div
              key={item.queue_id}
              className={`bg-white rounded-xl border border-slate-200 border-l-4 p-5 shadow-sm hover:shadow-md transition-shadow ${BORDER_COLORS[item.status] || 'border-l-slate-300'}`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <p className="font-semibold text-slate-800 text-sm leading-snug">{item.title}</p>
                <span className={`flex-shrink-0 text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${STATUS_STYLES[item.status] || 'bg-slate-100 text-slate-500'}`}>
                  {(item.status || '').replace('_', ' ')}
                </span>
              </div>

              {item.why_it_matters && (
                <p className="text-slate-500 text-xs leading-relaxed mb-3 line-clamp-2">{item.why_it_matters}</p>
              )}

              <div className="flex items-center gap-2 flex-wrap">
                <CountryBadge country={item.country} />
                {item.city && (
                  <span className="flex items-center gap-1 text-xs text-slate-400">
                    <MapPin size={11} /> {item.city}
                  </span>
                )}
                {item.sector && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                    {item.sector}
                  </span>
                )}
                <div className="ml-auto flex items-center gap-3">
                  <SignalStrength score={item.confidence_score} />
                  <span className="text-xs text-slate-400">{formatDate(item.created_at)}</span>
                  {item.source_url && (
                    <a href={item.source_url} target="_blank" rel="noreferrer" className="text-blue-500 hover:text-blue-700">
                      <ExternalLink size={13} />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function EmptyState({ title, desc }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm py-16 text-center">
      <div className="text-4xl mb-4 opacity-20">📡</div>
      <p className="font-semibold text-slate-700 mb-1">{title}</p>
      <p className="text-slate-400 text-sm max-w-sm mx-auto">{desc}</p>
    </div>
  )
}
