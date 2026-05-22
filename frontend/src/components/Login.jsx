import { useState } from 'react'

const FEATURES = [
  'ProZorro procurement tenders — Ukraine',
  'ANSC / date.gov.md datasets — Moldova',
  'ANAF / data.gov.ro procurement — Romania',
  'Live RSS news from 5 regional outlets',
  'AI-drafted briefs via GPT-4.1-mini',
  'Auto-translation from Ukrainian & Romanian',
]

export default function Login({ onSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (res.ok) {
        sessionStorage.setItem('reed_auth', '1')
        onSuccess()
      } else {
        setError('Invalid username or password.')
      }
    } catch {
      setError('Connection error — please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-[420px] flex-shrink-0 bg-navy px-10 py-12">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center font-extrabold text-navy text-sm">
              RI
            </div>
            <span className="text-white font-bold text-xl tracking-tight">Reed Intel</span>
          </div>

          <h2 className="text-white text-3xl font-bold leading-snug mb-3">
            Eastern European<br />Market Intelligence
          </h2>
          <p className="text-white/50 text-sm leading-relaxed mb-10">
            Real-time procurement signals, company data, and AI-generated briefs across
            Ukraine, Moldova, and Romania.
          </p>

          <div className="space-y-3">
            {FEATURES.map(f => (
              <div key={f} className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                <span className="text-white/70 text-sm">{f}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-white/25 text-xs">
          Confidential · Not for redistribution
        </p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center bg-slate-50 px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-9 h-9 bg-navy rounded-lg flex items-center justify-center font-extrabold text-white text-sm">
              RI
            </div>
            <span className="text-navy font-bold text-lg">Reed Intel</span>
          </div>

          <h1 className="text-2xl font-bold text-slate-800 mb-1">Sign in</h1>
          <p className="text-slate-400 text-sm mb-8">Access the intelligence dashboard</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Username</label>
              <input
                type="text"
                autoComplete="username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-navy/30 focus:border-navy/60 transition"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-navy/30 focus:border-navy/60 transition"
                required
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-navy text-white py-3 rounded-xl text-sm font-semibold hover:bg-navy/90 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
