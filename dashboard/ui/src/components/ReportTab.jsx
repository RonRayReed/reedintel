import Markdown from 'react-markdown'
import { formatDate } from '../utils'

export default function ReportTab({ report }) {
  if (!report) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm py-16 text-center">
        <div className="text-4xl mb-4 opacity-20">📄</div>
        <p className="font-semibold text-slate-700 mb-1">No weekly report yet</p>
        <p className="text-slate-400 text-sm max-w-sm mx-auto">
          Your first weekly intelligence report will be generated automatically on Monday morning.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
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

      {/* Executive summary */}
      {report.executive_summary && (
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-100">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Executive Summary
          </p>
          <p className="text-sm text-slate-700 leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {/* Full markdown body */}
      {report.report_markdown && (
        <div className="px-6 py-5 report-content">
          <Markdown>{report.report_markdown}</Markdown>
        </div>
      )}
    </div>
  )
}
