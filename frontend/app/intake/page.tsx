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
  const [loadingStep, setLoadingStep] = useState(0)
  const [error, setError] = useState('')

  const LOADING_STEPS = [
    { label: 'Identifying business',    sub: 'Researching domain...' },
    { label: 'Mapping industry & type', sub: 'Analyzing business context...' },
    { label: 'Pre-loading CX flows',    sub: 'Matching interaction patterns...' },
  ]

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
    setLoadingStep(0)
    setError('')

    try {
      // Create session
      const session = await Sessions.create()
      setSession(session)
      setSessionId(session.session_id)

      // Step 1 — identifying business
      setLoadingStep(1)
      await new Promise(r => setTimeout(r, 600))

      // Step 2 — run inference (this is the slow one)
      setLoadingStep(2)
      const result = await Inference.run({
        session_id: session.session_id,
        email: form.email,
        first_name: form.first_name,
        last_name: form.last_name,
        company_name: form.company_name,
        phone: form.phone,
      })

      // Step 3 — pre-loading flows
      setLoadingStep(3)
      await new Promise(r => setTimeout(r, 400))

      setBusinessProfile(result.business_profile)
      setDiscovery(result.suggested_flows)

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
                  placeholder="John"
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
                  placeholder="Doe"
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
                placeholder="john.doe@acme.com"
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
            {!loading ? (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full bg-accent hover:bg-accent-hover text-white
                         font-semibold text-sm rounded-lg py-2.5 mt-2
                         transition-all disabled:opacity-50
                         disabled:cursor-not-allowed flex items-center
                         justify-center gap-2"
            >
              Begin Session →
            </button>
            ) : (
              <div className="mt-4 space-y-3">
                {LOADING_STEPS.map((step, i) => {
                  const done   = loadingStep > i + 1
                  const active = loadingStep === i + 1
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                        {done ? (
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <circle cx="8" cy="8" r="8" fill="#4ade80" opacity="0.2"/>
                            <path d="M5 8l2 2 4-4" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round"/>
                          </svg>
                        ) : active ? (
                          <Loader2 size={14} className="animate-spin text-accent" />
                        ) : (
                          <div className="w-3 h-3 rounded-full border border-border" />
                        )}
                      </div>
                      <div>
                        <div className={`text-sm font-medium transition-colors ${
                          done ? 'text-success' : active ? 'text-text-primary' : 'text-text-faint'
                        }`}>
                          {step.label}
                        </div>
                        {active && (
                          <div className="text-xs text-text-dim mt-0.5">{step.sub}</div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
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