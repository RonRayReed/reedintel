import { useState } from 'react'
import { ExternalLink, MapPin, ClipboardCheck, Languages, FileText, X, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react'
import { formatDate, confidenceInfo, countryStyle } from '../utils'

const FILTERS = ['all', 'new', 'in_review', 'published', 'dismissed']
const PAGE_SIZE = 15

// ── Pagination ────────────────────────────────────────────────────────────────

function Pagination({ page, totalPages, total, pageSize, onChange }) {
  if (totalPages <= 1) return null

  const pages = []
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= page - 2 && i <= page + 2)) {
      pages.push(i)
    } else if (pages[pages.length - 1] !== '…') {
      pages.push('…')
    }
  }

  const from = (page - 1) * pageSize + 1
  const to   = Math.min(page * pageSize, total)

  return (
    <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
      <span className="text-xs text-slate-400">
        Showing <span className="font-medium text-slate-600">{from}–{to}</span> of <span className="font-medium text-slate-600">{total.toLocaleString()}</span> signals
      </span>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page === 1}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft size={13} /> Prev
        </button>

        {pages.map((p, i) =>
          p === '…' ? (
            <span key={`e${i}`} className="px-1.5 text-slate-300 text-xs">…</span>
          ) : (
            <button
              key={p}
              onClick={() => onChange(p)}
              className={`w-8 h-8 rounded-lg text-xs font-semibold transition-colors ${
                p === page ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
              }`}
            >
              {p}
            </button>
          )
        )}

        <button
          onClick={() => onChange(page + 1)}
          disabled={page === totalPages}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          Next <ChevronRight size={13} />
        </button>
      </div>
    </div>
  )
}

// ── Translation helpers ───────────────────────────────────────────────────────

async function fetchTranslation(text) {
  if (!text) return { translated: text, changed: false }
  const r = await fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return r.json()
}

// ── Status styling ────────────────────────────────────────────────────────────

const STATUS_DOT = {
  new:       'bg-blue-500',
  in_review: 'bg-amber-500',
  published: 'bg-emerald-500',
  dismissed: 'bg-slate-300',
}

const STATUS_LABEL = {
  new:       { cls: 'bg-blue-50 text-blue-700 border-blue-200/60',     label: 'New'       },
  in_review: { cls: 'bg-amber-50 text-amber-700 border-amber-200/60',  label: 'In Review' },
  published: { cls: 'bg-emerald-50 text-emerald-700 border-emerald-200/60', label: 'Published' },
  dismissed: { cls: 'bg-slate-50 text-slate-400 border-slate-200/60',  label: 'Dismissed' },
}

// ── AI Draft Modal ────────────────────────────────────────────────────────────

function DraftModal({ draft, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[88vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 sticky top-0 bg-white rounded-t-2xl">
          <div className="flex items-center gap-2.5">
            <FileText size={15} className="text-indigo-500" />
            <span className="font-semibold text-slate-800 text-sm">AI Draft Brief</span>
            {draft?.data?.model_name && (
              <span className="text-[10px] bg-indigo-50 text-indigo-600 border border-indigo-100 px-2 py-0.5 rounded-full font-semibold">
                {draft.data.model_name}
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors">
            <X size={15} className="text-slate-400" />
          </button>
        </div>

        <div className="px-6 py-5">
          {draft?.busy ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
              <span className="w-7 h-7 border-2 border-indigo-300 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-medium">Generating with GPT-4.1-mini…</span>
              <span className="text-xs text-slate-300">Usually 5–10 seconds</span>
            </div>
          ) : draft?.error ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2">
              <AlertCircle size={24} className="text-red-300" />
              <p className="text-red-500 font-semibold text-sm">Draft generation failed</p>
              <p className="text-slate-400 text-xs max-w-xs text-center">{draft.error}</p>
            </div>
          ) : draft?.data ? (
            <div className="space-y-6">
              {draft.data.headline && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Headline</p>
                  <h2 className="text-xl font-bold text-slate-900 leading-snug">{draft.data.headline}</h2>
                </div>
              )}
              {draft.data.deck && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Deck</p>
                  <p className="text-base text-slate-600 italic leading-relaxed">{draft.data.deck}</p>
                </div>
              )}
              {draft.data.body && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Body</p>
                  <p className="text-sm text-slate-700 leading-[1.75] whitespace-pre-wrap">{draft.data.body}</p>
                </div>
              )}
              {draft.data.editor_notes && (
                <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-amber-600 mb-2">Editor Verification Notes</p>
                  <p className="text-xs text-amber-800 leading-relaxed">{draft.data.editor_notes}</p>
                </div>
              )}
              {draft.data.created_at && (
                <p className="text-[10px] text-slate-300 pt-2 border-t border-slate-100">
                  Generated {formatDate(draft.data.created_at)} · {draft.data.prompt_version || 'v1'}
                </p>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

// ── Signal row ────────────────────────────────────────────────────────────────

function SignalRow({ item, status, busy, trans, showingTrans, draftState,
                     onMoveToReview, onToggleTranslate, onOpenDraft }) {
  const { color } = confidenceInfo(item.confidence_score ?? 0)
  const { bg, text: textColor } = countryStyle(item.country)
  const sl = STATUS_LABEL[status] || STATUS_LABEL.new
  const displayTitle = showingTrans && trans?.title ? trans.title : item.title
  const displayWhy   = showingTrans && trans?.why   ? trans.why   : item.why_it_matters

  return (
    <div className="group flex items-start gap-4 px-5 py-4 hover:bg-slate-50/80 border-b border-slate-100 last:border-0 transition-colors">

      {/* Status dot */}
      <div className="pt-1.5 flex-shrink-0">
        <span className={`block w-2 h-2 rounded-full ${STATUS_DOT[status] || 'bg-slate-300'}`} />
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Title line */}
        <div className="flex items-start gap-2 mb-1.5">
          <p className="text-sm font-medium text-slate-800 leading-snug flex-1 min-w-0">{displayTitle}</p>
          <span className={`flex-shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-md border ${sl.cls}`}>
            {sl.label}
          </span>
        </div>

        {/* Summary line */}
        {displayWhy && (
          <p className="text-xs text-slate-400 leading-relaxed mb-2.5 line-clamp-1">{displayWhy}</p>
        )}

        {/* Meta + actions row */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Country */}
          {item.country && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded" style={{ background: bg, color: textColor }}>
              {item.country}
            </span>
          )}
          {item.city && (
            <span className="flex items-center gap-0.5 text-[11px] text-slate-400">
              <MapPin size={10} /> {item.city}
            </span>
          )}
          {item.sector && (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-500">
              {item.sector}
            </span>
          )}

          {/* Confidence bar */}
          <div className="flex items-center gap-1.5">
            <div className="flex items-end gap-px" style={{ height: 12 }}>
              {[3, 6, 9, 12].map((h, i) => (
                <div key={i} style={{ width: 3, height: h, borderRadius: 1,
                  background: i < Math.round((item.confidence_score ?? 0) * 4) ? color : '#e2e8f0' }} />
              ))}
            </div>
            <span className="text-[10px] text-slate-400">{Math.round((item.confidence_score ?? 0) * 100)}%</span>
          </div>

          <span className="text-[11px] text-slate-400">{formatDate(item.created_at)}</span>

          {/* Action buttons — always visible */}
          <div className="flex items-center gap-1.5 ml-auto">
            {/* Translate pill */}
            <div
              onClick={() => !trans?.busy && onToggleTranslate(item)}
              title={showingTrans ? 'Show original' : 'Translate to English'}
              className={`flex items-center rounded-md border text-[10px] font-semibold overflow-hidden cursor-pointer select-none ${
                trans?.error ? 'border-red-200 opacity-40' : 'border-slate-200'
              }`}
            >
              <span className={`px-2 py-1 transition-colors ${!showingTrans ? 'bg-slate-800 text-white' : 'bg-white text-slate-400 hover:text-slate-600'}`}>
                Orig
              </span>
              <span className={`px-2 py-1 flex items-center gap-1 transition-colors ${showingTrans ? 'bg-indigo-600 text-white' : 'bg-white text-slate-400 hover:text-slate-600'}`}>
                {trans?.busy
                  ? <span className="w-2.5 h-2.5 border-2 border-indigo-300 border-t-transparent rounded-full animate-spin inline-block" />
                  : <Languages size={9} />}
                EN
              </span>
            </div>

            {/* Draft button */}
            <button
              onClick={() => onOpenDraft(item)}
              disabled={draftState?.busy}
              title="View / generate AI draft"
              className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-600 hover:bg-indigo-100 text-[11px] font-semibold transition-colors disabled:opacity-40 border border-indigo-100"
            >
              {draftState?.busy
                ? <span className="w-2.5 h-2.5 border-2 border-indigo-300 border-t-transparent rounded-full animate-spin inline-block" />
                : <FileText size={11} />}
              Draft
            </button>

            {/* External link */}
            {item.source_url && (
              <a href={item.source_url} target="_blank" rel="noreferrer"
                className="p-1 rounded-md text-slate-400 hover:text-blue-500 hover:bg-slate-100 transition-colors">
                <ExternalLink size={12} />
              </a>
            )}

            {/* Move to review */}
            {status === 'new' && (
              <button
                onClick={() => onMoveToReview(item)}
                disabled={busy}
                title="Move to review"
                className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 hover:bg-amber-100 text-[11px] font-semibold transition-colors disabled:opacity-40 border border-amber-100"
              >
                <ClipboardCheck size={11} />
                {busy ? '…' : 'Review'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function SignalsTab({ signals }) {
  const [filter, setFilter]         = useState('all')
  const [page, setPage]             = useState(1)
  const [statuses, setStatuses]     = useState({})
  const [loading, setLoading]       = useState({})
  const [translations, setTrans]    = useState({})
  const [drafts, setDrafts]         = useState({})
  const [draftModal, setDraftModal] = useState(null)

  const effective = (item) => statuses[item.queue_id] || item.status

  const visible = filter === 'all'
    ? signals
    : signals.filter(s => effective(s) === filter)

  const totalPages = Math.ceil(visible.length / PAGE_SIZE)
  const safePage   = Math.min(page, Math.max(totalPages, 1))
  const pageItems  = visible.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  const handleFilterChange = (f) => { setFilter(f); setPage(1) }
  const handlePageChange   = (p) => {
    setPage(p)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const moveToReview = async (item) => {
    setLoading(prev => ({ ...prev, [item.queue_id]: true }))
    try {
      await fetch(`/api/signals/${item.queue_id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'in_review' }),
      })
      setStatuses(prev => ({ ...prev, [item.queue_id]: 'in_review' }))
    } finally {
      setLoading(prev => ({ ...prev, [item.queue_id]: false }))
    }
  }

  const toggleTranslate = async (item) => {
    const existing = translations[item.queue_id]
    if (existing?.title !== undefined) {
      setTrans(prev => ({ ...prev, [item.queue_id]: { ...existing, shown: !existing.shown } }))
      return
    }
    setTrans(prev => ({ ...prev, [item.queue_id]: { busy: true, shown: false } }))
    try {
      const [titleRes, whyRes] = await Promise.all([
        fetchTranslation(item.title),
        fetchTranslation(item.why_it_matters),
      ])
      setTrans(prev => ({
        ...prev,
        [item.queue_id]: { title: titleRes.translated, why: whyRes.translated, busy: false, shown: true },
      }))
    } catch {
      setTrans(prev => ({ ...prev, [item.queue_id]: { busy: false, shown: false, error: true } }))
    }
  }

  const openDraft = async (item) => {
    if (drafts[item.queue_id]?.data) { setDraftModal(item.queue_id); return }
    setDraftModal(item.queue_id)
    setDrafts(prev => ({ ...prev, [item.queue_id]: { busy: true } }))
    try {
      let data
      const getRes = await fetch(`/api/drafts/${item.queue_id}`)
      if (getRes.ok) {
        data = await getRes.json()
      } else if (getRes.status === 404) {
        const genRes = await fetch(`/api/drafts/${item.queue_id}/generate`, { method: 'POST' })
        if (!genRes.ok) throw new Error(await genRes.text())
        data = await genRes.json()
      } else {
        throw new Error(`HTTP ${getRes.status}`)
      }
      setDrafts(prev => ({ ...prev, [item.queue_id]: { busy: false, data } }))
    } catch (e) {
      setDrafts(prev => ({ ...prev, [item.queue_id]: { busy: false, error: e.message } }))
    }
  }

  const newCount       = signals.filter(s => effective(s) === 'new').length
  const inReviewCount  = signals.filter(s => effective(s) === 'in_review').length
  const publishedCount = signals.filter(s => effective(s) === 'published').length

  return (
    <div>
      {/* Pipeline summary */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: 'New',       count: newCount,       dot: 'bg-blue-500',    bg: 'bg-blue-50',    text: 'text-blue-700'   },
          { label: 'In Review', count: inReviewCount,  dot: 'bg-amber-500',   bg: 'bg-amber-50',   text: 'text-amber-700'  },
          { label: 'Published', count: publishedCount, dot: 'bg-emerald-500', bg: 'bg-emerald-50', text: 'text-emerald-700'},
        ].map(({ label, count, dot, bg, text }) => (
          <button
            key={label}
            onClick={() => handleFilterChange(label.toLowerCase().replace(' ', '_'))}
            className={`${bg} rounded-xl px-4 py-3 flex items-center gap-3 hover:opacity-80 transition-opacity text-left`}
          >
            <span className={`w-2.5 h-2.5 rounded-full ${dot} flex-shrink-0`} />
            <div>
              <p className={`text-xl font-bold ${text}`}>{count.toLocaleString()}</p>
              <p className={`text-[11px] font-medium ${text} opacity-70`}>{label}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Filter + search row */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        {FILTERS.map(f => {
          const cnt = f === 'all' ? signals.length : signals.filter(s => effective(s) === f).length
          return (
            <button
              key={f}
              onClick={() => handleFilterChange(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all flex items-center gap-1.5 ${
                filter === f
                  ? 'bg-slate-900 text-white'
                  : 'bg-white border border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-700'
              }`}
            >
              {f.replace('_', ' ')}
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${filter === f ? 'bg-white/20' : 'bg-slate-100 text-slate-400'}`}>
                {cnt}
              </span>
            </button>
          )
        })}
      </div>

      {/* Signal list */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* List header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 bg-slate-50/50">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            {filter === 'all' ? 'All Signals' : filter.replace('_', ' ')}
          </p>
          <p className="text-[11px] text-slate-400">
            {visible.length > 0
              ? `${(safePage - 1) * PAGE_SIZE + 1}–${Math.min(safePage * PAGE_SIZE, visible.length)} of ${visible.length.toLocaleString()}`
              : '0 results'}
          </p>
        </div>

        {pageItems.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-slate-400 text-sm">No signals in this category</p>
          </div>
        ) : (
          pageItems.map(item => {
            const status   = effective(item)
            const trans    = translations[item.queue_id]
            const showing  = !!(trans?.shown && !trans?.busy)
            return (
              <SignalRow
                key={item.queue_id}
                item={item}
                status={status}
                busy={loading[item.queue_id]}
                trans={trans}
                showingTrans={showing}
                draftState={drafts[item.queue_id]}
                onMoveToReview={moveToReview}
                onToggleTranslate={toggleTranslate}
                onOpenDraft={openDraft}
              />
            )
          })
        )}

        {/* Pagination inside card */}
        {totalPages > 1 && (
          <div className="px-5 py-3">
            <Pagination
              page={safePage}
              totalPages={totalPages}
              total={visible.length}
              pageSize={PAGE_SIZE}
              onChange={handlePageChange}
            />
          </div>
        )}
      </div>

      {/* Draft modal */}
      {draftModal && (
        <DraftModal
          draft={drafts[draftModal]}
          onClose={() => setDraftModal(null)}
        />
      )}
    </div>
  )
}
