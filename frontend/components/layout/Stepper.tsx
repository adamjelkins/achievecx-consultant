'use client'

import { useSessionStore, type Phase } from '@/store/session'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

const PHASE_ORDER: Phase[] = [1, 2, 3, '3r', '3b', 4]

const PHASE_SHORT: Record<string | number, string> = {
  1: 'Profile', 2: 'Flows', 3: 'Assessment',
  '3r': 'Risk', '3b': 'Business Case', 4: 'Blueprint',
}

export default function Stepper() {
  const { currentPhase, phaseFlags, setPhase } = useSessionStore()

  const isComplete = (phase: Phase) => phaseFlags[`phase_${phase}`] ?? false
  const isCurrent  = (phase: Phase) => phase === currentPhase

  const handleClick = (phase: Phase) => {
    if (isComplete(phase) && !isCurrent(phase)) {
      setPhase(phase)
    }
  }

  return (
    <div className="flex items-center gap-0 mb-3">
      {PHASE_ORDER.map((phase, i) => {
        const complete = isComplete(phase)
        const current  = isCurrent(phase)
        const label    = PHASE_SHORT[phase as string | number]
        const isLast   = i === PHASE_ORDER.length - 1
        const clickable = complete && !current

        return (
          <div key={String(phase)} className="flex items-center">
            <button
              onClick={() => handleClick(phase)}
              disabled={!clickable && !current}
              className={cn(
                'text-[10px] font-semibold px-3 py-1.5 rounded-full whitespace-nowrap transition-all',
                current && 'bg-accent/10 text-accent border border-accent/30 cursor-default',
                clickable && 'bg-success/8 text-success border border-success/25 hover:bg-success/15 cursor-pointer',
                !current && !clickable && 'text-text-faint cursor-default',
              )}
            >
              {complete && !current && (
                <Check size={9} className="inline mr-1 -mt-px" />
              )}
              {current && <span className="mr-1">●</span>}
              {label}
            </button>

            {!isLast && (
              <div className="w-5 h-px bg-border mx-0.5 flex-shrink-0" />
            )}
          </div>
        )
      })}
      <div className="h-px bg-gradient-to-r from-accent/20 via-accent/40 to-accent/20 mt-1 w-full absolute left-0" />
    </div>
  )
}
