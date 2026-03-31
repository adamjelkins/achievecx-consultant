'use client'

import { useSessionStore, type Phase } from '@/store/session'
import { ChevronLeft, ChevronRight, SkipForward } from 'lucide-react'

const PHASE_ORDER: Phase[] = [1, 2, 3, '3r', '3b', 4]

const PHASE_LABELS: Record<string | number, string> = {
  1: 'Business Profile',
  2: 'Flow Confirmation',
  3: 'AI Assessment',
  '3r': 'Risk Assessment',
  '3b': 'Business Case',
  4: 'CX Blueprint',
}

const FORWARD_LABELS: Record<string | number, string | null> = {
  1: 'Flow Confirmation',
  2: 'AI Assessment',
  3: 'Risk Assessment',
  '3r': 'Business Case',
  '3b': 'CX Blueprint',
  4: null,
}

const BACK_LABELS: Record<string | number, string | null> = {
  1: null,
  2: 'Business Profile',
  3: 'Flow Confirmation',
  '3r': 'AI Assessment',
  '3b': 'Risk Assessment',
  4: 'Business Case',
}

const HINTS: Record<string | number, string> = {
  2: 'Complete the discovery conversation to continue.',
  3: 'Run the AI Assessment to continue.',
  '3r': 'Review risk or skip to continue.',
  '3b': 'Calculate business case or skip to continue.',
}

function isPhaseComplete(phase: Phase, flags: Record<string, boolean>): boolean {
  const key = `phase_${phase}`
  return flags[key] ?? false
}

export default function NavBar() {
  const { currentPhase, phaseFlags, setPhase } = useSessionStore()

  const cur       = currentPhase
  const curIdx    = PHASE_ORDER.indexOf(cur)
  const total     = PHASE_ORDER.length
  const phaseDone = isPhaseComplete(cur, phaseFlags)
  const fwdLabel  = FORWARD_LABELS[cur as string | number]
  const backLabel = BACK_LABELS[cur as string | number]
  const isLast    = fwdLabel === null
  const canBack   = backLabel !== null && curIdx > 0
  const canFwd    = phaseDone && !isLast
  const isSkippable = (cur === '3r' || cur === '3b') && !phaseDone
  const hint      = !phaseDone && !isLast ? HINTS[cur as string | number] : ''

  const goBack = () => {
    if (canBack) setPhase(PHASE_ORDER[curIdx - 1])
  }

  const goForward = () => {
    if (canFwd) setPhase(PHASE_ORDER[curIdx + 1])
  }

  const skip = () => {
    setPhase(PHASE_ORDER[curIdx + 1])
  }

  return (
    <div className="flex items-center gap-4 px-6 py-3">

      {/* Back */}
      <div className="w-36 flex-shrink-0">
        {canBack && (
          <button
            onClick={goBack}
            className="flex items-center gap-1.5 text-sm text-text-muted
                       border border-border rounded-lg px-3 py-2 w-full
                       hover:border-border-strong hover:text-text-primary
                       transition-all"
          >
            <ChevronLeft size={14} />
            <span className="truncate">{backLabel}</span>
          </button>
        )}
      </div>

      {/* Center — phase indicator */}
      <div className="flex-1 text-center">
        <div className="text-[10px] text-text-dim mb-0.5 uppercase tracking-wider">
          Step {curIdx + 1} of {total}
        </div>
        <div className="text-sm font-semibold text-text-secondary">
          {PHASE_LABELS[cur as string | number]}
        </div>
        {hint && (
          <div className="text-[10px] text-text-faint mt-0.5">{hint}</div>
        )}
      </div>

      {/* Forward */}
      <div className="w-36 flex-shrink-0 flex justify-end gap-2">
        {isLast ? (
          <span className="text-xs text-text-faint py-2">✓ Final deliverable</span>
        ) : isSkippable ? (
          <>
            <button
              onClick={skip}
              className="flex items-center gap-1 text-xs text-text-dim
                         border border-border rounded-lg px-2.5 py-2
                         hover:text-text-muted hover:border-border-strong transition-all"
            >
              <SkipForward size={12} />
              Skip
            </button>
            <button
              onClick={goForward}
              disabled={!canFwd}
              className="flex items-center gap-1.5 text-sm font-semibold
                         bg-accent text-white rounded-lg px-3 py-2
                         hover:bg-accent-hover transition-all
                         disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Continue
              <ChevronRight size={14} />
            </button>
          </>
        ) : (
          <button
            onClick={goForward}
            disabled={!canFwd}
            className="flex items-center gap-1.5 text-sm font-semibold
                       bg-accent text-white rounded-lg px-4 py-2 w-full
                       justify-center hover:bg-accent-hover
                       transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <span className="truncate">{fwdLabel}</span>
            <ChevronRight size={14} className="flex-shrink-0" />
          </button>
        )}
      </div>

    </div>
  )
}
