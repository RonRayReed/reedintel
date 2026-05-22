import { useState, useEffect, useCallback } from 'react'
import Login from './components/Login'
import Sidebar from './components/Sidebar'
import StatCards from './components/StatCards'
import SignalsTab from './components/SignalsTab'
import CompaniesTab from './components/CompaniesTab'
import ReportTab from './components/ReportTab'
import SourcesTab from './components/SourcesTab'

const PAGE_META = {
  signals:   { title: 'Intelligence Signals',  desc: 'Procurement events and market signals ingested from Eastern Europe' },
  companies: { title: 'Market Participants',    desc: 'Companies and entities identified across monitored regions' },
  report:    { title: 'Weekly Report',          desc: 'AI-generated intelligence briefs and editorial summaries' },
  sources:   { title: 'Data Sources',           desc: 'Status and health of all active ingestion connectors' },
}

export default function App() {
  const [authed, setAuthed]         = useState(!!sessionStorage.getItem('reed_auth'))
  const [data, setData]             = useState(null)
  const [loading, setLoading]       = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [fetchError, setFetchError] = useState(null)
  const [activeTab, setActiveTab]   = useState('signals')

  const load = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true)
    try {
      const res = await fetch('/api/dashboard')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
      setFetchError(null)
    } catch (e) {
      setFetchError(e.message)
    } finally {
      setLoading(false)
      if (manual) setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    if (!authed) return
    load()
    const t = setInterval(load, 300_000)
    return () => clearInterval(t)
  }, [authed, load])

  const handleLogout = () => {
    sessionStorage.removeItem('reed_auth')
    setAuthed(false)
    setData(null)
    setLoading(true)
  }

  if (!authed) return <Login onSuccess={() => setAuthed(true)} />

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-navy border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500 text-sm">Loading intelligence data…</p>
        </div>
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center max-w-md">
          <p className="text-red-500 font-semibold mb-2">Connection Error</p>
          <p className="text-slate-500 text-sm mb-4">{fetchError}</p>
          <button onClick={() => load(true)} className="px-4 py-2 bg-navy text-white rounded-lg text-sm font-medium hover:bg-navy/90 transition-colors">
            Retry
          </button>
        </div>
      </div>
    )
  }

  const meta = PAGE_META[activeTab]

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar
        active={activeTab}
        onChange={setActiveTab}
        stats={data.stats}
        sources={data.sources}
        onRefresh={() => load(true)}
        onLogout={handleLogout}
        refreshing={refreshing}
      />

      {/* Main content */}
      <div className="ml-[220px] flex-1 flex flex-col min-h-screen">

        {/* Page header */}
        <header className="bg-white border-b border-slate-200 px-7 py-5">
          {data.error && (
            <div className="mb-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 text-xs text-amber-700">
              Database connection issue — some data may be unavailable.
            </div>
          )}
          <div>
            <h1 className="text-[17px] font-bold text-slate-900 leading-none">{meta.title}</h1>
            <p className="text-xs text-slate-400 mt-1">{meta.desc}</p>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 px-7 py-6">
          <StatCards stats={data.stats} />

          {activeTab === 'signals'   && <SignalsTab   signals={data.editorial} />}
          {activeTab === 'companies' && <CompaniesTab companies={data.companies} signals={data.editorial} />}
          {activeTab === 'report'    && <ReportTab    report={data.report} stats={data.stats} signals={data.editorial} />}
          {activeTab === 'sources'   && <SourcesTab   sources={data.sources} />}
        </main>

        <footer className="px-7 py-4 border-t border-slate-200 flex items-center justify-between">
          <span className="text-xs text-slate-400">Reed Intel &copy; 2026</span>
          <span className="text-xs text-slate-400">Confidential · Not for redistribution</span>
        </footer>
      </div>
    </div>
  )
}
