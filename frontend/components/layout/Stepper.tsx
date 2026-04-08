'use client'

import { useSessionStore, type Phase, PHASE_ORDER, phaseFromPath, phaseIndex } from '@/store/session'
import { usePathname, useRouter } from 'next/navigation'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

const PHASE_SHORT: Record<string | number, string> = {
  1: 'Profile', 2: 'Flows', 3: 'Assessment',
  '3r': 'Risk', '3b': 'Business Case', 4: 'Blueprint',
}

export default function Stepper() {
  const { phaseFlags, currentPhase } = useSessionStore()
  const pathname = usePathname()
  const router   = useRouter()

  // Active pill = URL-driven
  const urlPhase  = phaseFromPath(pathname)
  const hwIdx     = phaseIndex(currentPhase)   // highwater mark index

  const isComplete   = (phase: Phase) => phaseFlags[`phase_${phase}`] ?? false
  const isActive     = (phase: Phase) => phase === urlPhase
  const isAccessible = (phase: Phase) => phaseIndex(phase) <= hwIdx + 1

  const handleClick = (phase: Phase) => {
    if (!isActive(phase) && isAccessible(phase)) {
      router.push(`/phase/${phase}`)
    }
  }

  return (
    <div className="flex items-center gap-0 mb-3 relative">
      {PHASE_ORDER.map((phase, i) => {
        const complete   = isComplete(phase)
        const active     = isActive(phase)
        const accessible = isAccessible(phase)
        const label      = PHASE_SHORT[phase as string | number]
        const isLast     = i === PHASE_ORDER.length - 1
        const clickable  = accessible && !active

        return (
          <div key={String(phase)} className="flex items-center">
            <button
              onClick={() => handleClick(phase)}
              disabled={!accessible}
              title={!accessible ? 'Complete previous phases to unlock' : undefined}
              className={cn(
                'text-[10px] font-semibold px-3 py-1.5 rounded-full whitespace-nowrap transition-all',
                // Currently viewing this page
                active && 'bg-accent/10 text-accent border border-accent/30 cursor-default',
                // Completed and not active — clickable
                !active && complete && clickable &&
                  'bg-success/8 text-success border border-success/25 hover:bg-success/15 cursor-pointer',
                // Accessible but not complete and not active (next phase)
                !active && !complete && accessible &&
                  'text-text-muted border border-border cursor-pointer hover:border-border-strong',
                // Locked
                !accessible && 'text-text-faint cursor-default opacity-40',
              )}
            >
              {complete && !active && (
                <Check size={9} className="inline mr-1 -mt-px" />
              )}
              {active && <span className="mr-1">●</span>}
              {label}
            </button>

            {!isLast && (
              <div className="w-5 h-px bg-border mx-0.5 flex-shrink-0" />
            )}
          </div>
        )
      })}
    </div>
  )
}