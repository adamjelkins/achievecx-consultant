'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const router = useRouter()

  const handleSubmit = async () => {
    if (!password) return
    setLoading(true)
    setError('')

    const res = await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    })

    if (res.ok) {
      router.push('/')
    } else {
      setError('Incorrect password.')
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center h-screen bg-bg">
      <div className="w-80">
        <div className="mb-8 text-center">
          <div className="text-xs text-text-faint">Private Access</div>
        </div>

        <div className="bg-bg-card border border-border rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-xs text-text-muted mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              autoFocus
              className="w-full bg-bg border border-border rounded-lg px-3 py-2
                         text-sm text-text-primary focus:outline-none focus:border-accent
                         transition-colors"
              placeholder="Enter access password"
            />
          </div>

          {error && (
            <div className="text-xs text-danger">{error}</div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading || !password}
            className="w-full bg-accent hover:bg-accent-hover text-white
                       font-semibold text-sm rounded-lg py-2.5 transition-all
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Verifying...' : 'Enter'}
          </button>
        </div>
      </div>
    </div>
  )
}