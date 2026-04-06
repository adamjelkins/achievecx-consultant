'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSessionStore } from '@/store/session'
import { Sessions } from '@/lib/api'

export default function Home() {
  const router = useRouter()
  const { sessionId, currentPhase, setSession } = useSessionStore()

  useEffect(() => {
    async function init() {
      if (sessionId) {
        try {
          const session = await Sessions.get(sessionId)
          setSession(session)
          // Route to current phase
          if (session.intake_complete) {
            router.push('/phase/' + session.current_phase)
          } else {
            router.push('/intake')
          }
          return
        } catch {
          // Session expired
        }
      }
      router.push('/intake')
    }
    init()
  }, [])

  return (
    <div className="flex h-screen items-center justify-center bg-bg">
      <div className="text-text-dim text-sm">Loading...</div>
    </div>
  )
}