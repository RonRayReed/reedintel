import { useState, useEffect, useCallback } from 'react'
import Login from './components/Login'
import Navbar from './components/Navbar'
import StatCards from './components/StatCards'
import TabBar from './components/TabBar'
import SignalsTab from './components/SignalsTab'
import CompaniesTab from './components/CompaniesTab'
import ReportTab from './components/ReportTab'
import SourcesTab from './components/SourcesTab'

const TABS = [
  { id: 'signals',   label: 'Intelligence Signals' },
  { id: 'companies', label: 'Market Participants' },
  { id: 'report',    label: 'Weekly Report' },
  { id: 'sources',   label: 'Data Sources' },
]

export default function App() {
  const [authed, setAuthed]         = useState(!!sessionStorage.getItem('reed_auth'))
  const [data, setData]             = useState(null)
  const [loading, setLoading]       = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [activeTab, setActiveTab]   = useState('signals')

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/dashboard')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
      setFetchError(null)
    } catch (e) {
      setFetchError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Runs whenever authed flips to true — fires immediately after login
  useEffect(() => {
    if (!authed) return
    load()
    const t = setInterval(load, 300_000)
    return () => clearInterval(t)
  }, [authed, load])

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
          <p className="text-slate-500 text-sm">{fetchError}</p>
          <button onClick={load} className="mt-4 px-4 py-2 bg-navy text-white rounded-lg text-sm">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar lastUpdated={data.last_updated} />

      <div className="max-w-7xl mx-auto px-4 py-6">
        {data.error && (
          <div className="mb-4 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-700">
            Database connection issue — some data may be unavailable.
          </div>
        )}

        <StatCards stats={data.stats} />
        <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} newCount={data.stats.new_items} />

        {activeTab === 'signals'   && <SignalsTab   signals={data.editorial} />}
        {activeTab === 'companies' && <CompaniesTab companies={data.companies} />}
        {activeTab === 'report'    && <ReportTab    report={data.report} />}
        {activeTab === 'sources'   && <SourcesTab   sources={data.sources} />}
      </div>

      <footer className="text-center py-6 text-slate-400 text-xs">
        Reed Intel &copy; 2025 — Confidential. Not for redistribution.
      </footer>
    </div>
  )
}
