'use client'

import { useEffect } from 'react'
import { useSessionStore } from '@/store/session'
import { Sessions } from '@/lib/api'
import Sidebar from '@/components/layout/Sidebar'
import NavBar from '@/components/layout/NavBar'
import Stepper from '@/components/layout/Stepper'

interface AppShellProps {
  children: React.ReactNode
}

export default function AppShell({ children }: AppShellProps) {
  const { sessionId, setSession } = useSessionStore()

  // Bootstrap session on mount
  useEffect(() => {
    async function init() {
      if (sessionId) {
        try {
          const session = await Sessions.get(sessionId)
          setSession(session)
          return
        } catch {
          // Session expired — create new one
        }
      }
      const session = await Sessions.create()
      setSession(session)
    }
    init()
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-bg">

      {/* ── Sidebar ── */}
      <aside className="w-60 flex-shrink-0 flex flex-col border-r border-border bg-bg overflow-y-auto">
        <Sidebar />
      </aside>

      {/* ── Main content ── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Stepper */}
        <div className="flex-shrink-0 px-6 pt-4 pb-0">
          <Stepper />
        </div>

        {/* Phase content — scrollable */}
        <main className="flex-1 overflow-y-auto px-6 pt-4 pb-24">
          {children}
        </main>

        {/* ── Sticky nav bar — always visible ── */}
        <div className="flex-shrink-0 border-t border-border bg-bg/95 backdrop-blur-sm">
          <NavBar />
        </div>

      </div>
    </div>
  )
}
