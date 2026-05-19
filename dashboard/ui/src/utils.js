export function timeAgo(isoString) {
  if (!isoString) return 'Never'
  const diff = Date.now() - new Date(isoString).getTime()
  if (diff < 0) return 'Just now'
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return 'Just now'
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`
  return `${Math.floor(secs / 86400)}d ago`
}

export function formatDate(isoString) {
  if (!isoString) return '—'
  return new Date(isoString).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

export function confidenceInfo(score) {
  if (score >= 0.75) return { label: 'High',   color: '#059669' }
  if (score >= 0.5)  return { label: 'Medium', color: '#d97706' }
  return                     { label: 'Low',    color: '#dc2626' }
}

export function countryStyle(country) {
  const map = {
    Ukraine: { bg: '#005BBB', text: '#fff' },
    Moldova: { bg: '#6b21a8', text: '#fff' },
    Romania: { bg: '#b91c1c', text: '#fff' },
  }
  return map[country] || { bg: '#64748b', text: '#fff' }
}
