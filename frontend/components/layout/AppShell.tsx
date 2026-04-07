'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useSessionStore } from '@/store/session'
import { Sessions } from '@/lib/api'
import Sidebar from '@/components/layout/Sidebar'
import NavBar from '@/components/layout/NavBar'
import Stepper from '@/components/layout/Stepper'
import PhaseContext from '@/components/layout/PhaseContext'

interface AppShellProps {
  children: React.ReactNode
}

export default function AppShell({ children }: AppShellProps) {
  const { sessionId, setSession, currentPhase } = useSessionStore()
  const router = useRouter()
  const pathname = usePathname()

  // Redirect to correct phase URL if store and URL are out of sync
  useEffect(() => {
    if (!pathname || !currentPhase) return
    if (!pathname.startsWith('/phase/')) return
    const urlPhase = pathname.replace('/phase/', '')
    const expectedPath = `/phase/${currentPhase}`
    // Only redirect if URL phase exactly matches but we need to go somewhere different
    // Don't redirect if user is on a valid phase page (let them navigate manually)
    if (urlPhase === String(currentPhase)) return
    // Only redirect if the URL phase is not a real page (catch-all)
    const builtPhases = ['2', '3', '3r', '3b', '4']
    if (!builtPhases.includes(urlPhase)) {
      router.replace(expectedPath)
    }
  }, [currentPhase, pathname])

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

      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 flex flex-col border-r border-border bg-bg overflow-y-auto">
        <Sidebar />
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Stepper */}
        <div className="flex-shrink-0 px-6 pt-4 pb-3 border-b border-border">
          <Stepper />
        </div>

        {/* Phase context */}
        <PhaseContext />

        {/* Phase content — scrollable */}
        <main className="flex-1 overflow-y-auto px-6 pt-4 pb-24">
          {children}
        </main>

        {/* Sticky nav bar */}
        <div className="flex-shrink-0 border-t border-border bg-bg/95 backdrop-blur-sm">
          <NavBar />
        </div>

      </div>
    </div>
  )
}