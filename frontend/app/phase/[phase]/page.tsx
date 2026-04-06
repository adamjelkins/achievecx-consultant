'use client'

import { useParams } from 'next/navigation'
import AppShell from '@/components/layout/AppShell'

export default function PhasePage() {
  const { phase } = useParams()

  return (
    <AppShell>
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-text-dim text-sm">Phase {phase}</div>
          <div className="text-text-faint text-xs mt-1">Coming soon</div>
        </div>
      </div>
    </AppShell>
  )
}