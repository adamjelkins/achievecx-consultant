'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSessionStore } from '@/store/session'
import { Sessions, Inference } from '@/lib/api'
import { Loader2 } from 'lucide-react'
import DebugLoader from '@/components/DebugLoader'

export default function IntakePage() {
  const router = useRouter()
  const { setSession, setBusinessProfile, setDiscovery, setSessionId } = useSessionStore()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    company_name: '',
    phone: '',
  })

  const update = (field: string, value: string) =>
    setForm(prev => ({ ...prev, [field]: value }))

  const handleSubmit = async () => {
    if (!form.email || !form.first_name || !form.last_name) {
      setError('Please fill in your name and email.')
      return
    }
    if (!form.email.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }

    setLoading(true)
    setError('')

    try {
      // Create session first
      const session = await Sessions.create()
      setSession(session)
      setSessionId(session.session_id)

      // Run inference
      const result = await Inference.run({
        session_id: session.session_id,
        email: form.email,
        first_name: form.first_name,
        last_name: form.last_name,
        company_name: form.company_name,
        phone: form.phone,
      })

      setBusinessProfile(result.business_profile)
      setDiscovery(result.suggested_flows)

      // Go to Phase 2
      router.push('/phase/2')

    } catch (e: any) {
      setError('Something went wrong. Please try again.')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Logo / Wordmark */}
        <div className="text-center mb-10">
          <div className="text-2xl font-bold tracking-tight text-white mb-1">
            AchieveCX
          </div>
          <div className="text-sm text-text-dim">
            AI-Powered CX Architecture
          </div>
        </div>

        {/* Card */}
        <div className="bg-bg-card border border-border rounded-xl p-8">
          <h1 className="text-lg font-semibold text-white mb-1">
            Start a new session
          </h1>
          <p className="text-sm text-text-muted mb-6">
            Enter your client's details to begin.
          </p>

          <div className="space-y-4">

            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-text-muted mb-1.5">
                  First name <span className="text-danger">*</span>
                </label>
                <input
                  type="text"
                  value={form.first_name}
                  onChange={e => update('first_name', e.target.value)}
                  placeholder="Adam"
                  className="w-full bg-bg-surface border border-border rounded-lg
                             px-3 py-2 text-sm text-white placeholder-text-faint
                             focus:outline-none focus:border-accent transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1.5">
                  Last name <span className="text-danger">*</span>
                </label>
                <input
                  type="text"
                  value={form.last_name}
                  onChange={e => update('last_name', e.target.value)}
                  placeholder="Elkins"
                  className="w-full bg-bg-surface border border-border rounded-lg
                             px-3 py-2 text-sm text-white placeholder-text-faint
                             focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs text-text-muted mb-1.5">
                Work email <span className="text-danger">*</span>
              </label>
              <input
                type="email"
                value={form.email}
                onChange={e => update('email', e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                placeholder="adam@company.com"
                className="w-full bg-bg-surface border border-border rounded-lg
                           px-3 py-2 text-sm text-white placeholder-text-faint
                           focus:outline-none focus:border-accent transition-colors"
              />
              <p className="text-[10px] text-text-faint mt-1">
                Used to research the company automatically.
              </p>
            </div>

            {/* Company name */}
            <div>
              <label className="block text-xs text-text-muted mb-1.5">
                Company name
              </label>
              <input
                type="text"
                value={form.company_name}
                onChange={e => update('company_name', e.target.value)}
                placeholder="Acme Corp"
                className="w-full bg-bg-surface border border-border rounded-lg
                           px-3 py-2 text-sm text-white placeholder-text-faint
                           focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            {/* Phone */}
            <div>
              <label className="block text-xs text-text-muted mb-1.5">
                Phone <span className="text-text-faint">(optional)</span>
              </label>
              <input
                type="tel"
                value={form.phone}
                onChange={e => update('phone', e.target.value)}
                placeholder="+1 (555) 000-0000"
                className="w-full bg-bg-surface border border-border rounded-lg
                           px-3 py-2 text-sm text-white placeholder-text-faint
                           focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            {/* Error */}
            {error && (
              <p className="text-xs text-danger">{error}</p>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full bg-accent hover:bg-accent-hover text-white
                         font-semibold text-sm rounded-lg py-2.5 mt-2
                         transition-all disabled:opacity-50
                         disabled:cursor-not-allowed flex items-center
                         justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Researching company...
                </>
              ) : (
                'Begin Session →'
              )}
            </button>
          </div>
        </div>

        {/* Debug loader — dev only */}
        <DebugLoader />

        {/* Footer */}
        <p className="text-center text-[10px] text-text-faint mt-6">
          Session data is private and not shared.
        </p>

      </div>
    </div>
  )
}