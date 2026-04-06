'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSessionStore } from '@/store/session'
import { Sessions, Inference } from '@/lib/api'
import axios from 'axios'
import { Bug, Loader2 } from 'lucide-react'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Complete test session data for AT&T
const TEST_CONV_ANSWERS = {
  flow_confirmation: ['Billing Inquiry', 'Technical Support', 'Outage Reporting',
                      'Account Changes', 'New Service Activation', 'Retention/Win-back'],
  regions:    'North America',
  channels:   ['Phone', 'Live Chat', 'Web / Self-service', 'SMS'],
  volume:     '50,000+',
  pain_point: 'High call volume with long handle times. Agents spending too much time on repetitive billing and technical support inquiries that could be self-served.',
  automation: 'Basic IVR only',
  crm:        'Salesforce',
  cc_platform:'Genesys',
  goal:       'Reduce cost per contact while improving CSAT',
  timeline:   '6-12 months',
}

export default function DebugLoader() {
  const [loading, setLoading] = useState(false)
  const [targetPhase, setTargetPhase] = useState<string>('2')
  const [open, setOpen] = useState(false)
  const router = useRouter()
  const { setSession, setSessionId, setBusinessProfile, setDiscovery, setConversation } = useSessionStore()

  if (process.env.NODE_ENV === 'production') return null

  const load = async () => {
    setLoading(true)
    try {
      // 1. Create session
      const session = await Sessions.create()
      setSession(session)
      setSessionId(session.session_id)

      // 2. Run inference with AT&T
      const inf = await Inference.run({
        session_id:   session.session_id,
        email:        'john.doe@att.com',
        first_name:   'John',
        last_name:    'Doe',
        company_name: 'AT&T',
        phone:        '',
      })
      setBusinessProfile(inf.business_profile)
      setDiscovery(inf.suggested_flows)

      if (targetPhase === '2') {
        router.push('/phase/2')
        return
      }

      // For all phases beyond 2, seed conv answers first
      await axios.post(`${BASE}/api/debug/seed-session`, {
        session_id:   session.session_id,
        conv_answers: TEST_CONV_ANSWERS,
      })

      if (targetPhase === '3') {
        await axios.post(`${BASE}/api/assessment/${session.session_id}/run`)
        router.push('/phase/3')
        return
      }

      if (targetPhase === '3r') {
        await axios.post(`${BASE}/api/assessment/${session.session_id}/run`)
        await axios.post(`${BASE}/api/risk/${session.session_id}/run`)
        router.push('/phase/3r')
        return
      }

      if (targetPhase === '3b') {
        await axios.post(`${BASE}/api/assessment/${session.session_id}/run`)
        await axios.post(`${BASE}/api/risk/${session.session_id}/run`)
        router.push('/phase/3b')
        return
      }

      if (targetPhase === '4') {
        await axios.post(`${BASE}/api/assessment/${session.session_id}/run`)
        await axios.post(`${BASE}/api/risk/${session.session_id}/run`)
        await axios.post(`${BASE}/api/business-case/run`, {
          session_id: session.session_id,
          inputs: null,
        })
        await axios.post(`${BASE}/api/blueprint/${session.session_id}/generate`)
        router.push('/phase/4')
        return
      }

      router.push('/phase/' + targetPhase)

    } catch (e) {
      console.error('Debug load failed:', e)
    } finally {
      setLoading(false)
      setOpen(false)
    }
  }

  return (
    <div className="mt-4">
      {!open ? (
        <button
          onClick={() => setOpen(true)}
          className="w-full flex items-center justify-center gap-2 text-xs
                     text-text-faint border border-border/50 rounded-lg py-2
                     hover:border-border hover:text-text-dim transition-all"
        >
          <Bug size={11} />
          Dev: Load test session
        </button>
      ) : (
        <div className="border border-border rounded-lg p-3 bg-bg-surface">
          <div className="text-xs font-semibold text-text-muted mb-2">
            Load AT&T test session
          </div>
          <div className="text-[10px] text-text-dim mb-3">
            john.doe@att.com · 500 agents · Salesforce + Genesys · 50K+ contacts
          </div>
          <select
            value={targetPhase}
            onChange={e => setTargetPhase(e.target.value)}
            className="w-full bg-bg border border-border rounded text-xs
                       text-text-secondary px-2 py-1.5 mb-3"
          >
            <option value="2">Phase 2 — CX Explorer</option>
            <option value="3">Phase 3 — Assessment</option>
            <option value="3r">Phase 3r — Risk</option>
            <option value="3b">Phase 3b — Business Case</option>
            <option value="4">Phase 4 — Blueprint</option>
          </select>
          <div className="flex gap-2">
            <button
              onClick={() => setOpen(false)}
              className="flex-1 text-xs text-text-dim border border-border
                         rounded py-1.5 hover:text-text-muted transition-all"
            >
              Cancel
            </button>
            <button
              onClick={load}
              disabled={loading}
              className="flex-1 text-xs bg-accent text-white rounded py-1.5
                         hover:bg-accent-hover transition-all
                         disabled:opacity-50 flex items-center justify-center gap-1"
            >
              {loading ? <><Loader2 size={10} className="animate-spin" />Loading...</> : 'Load →'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}