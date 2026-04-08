'use client'

import { useSessionStore, type Phase, PHASE_ORDER, phaseFromPath, phaseIndex } from '@/store/session'
import { usePathname, useRouter } from 'next/navigation'
import { ChevronLeft, ChevronRight, SkipForward } from 'lucide-react'

const PHASE_LABELS: Record<string | number, string> = {
  1: 'Business Profile',
  2: 'Flow Confirmation',
  3: 'AI Assessment',
  '3r': 'Risk Assessment',
  '3b': 'Business Case',
  4: 'CX Blueprint',
}

const HINTS: Record<string | number, string> = {
  2:    'Complete the discovery conversation to continue.',
  3:    'Run the AI Assessment to continue.',
  '3r': 'Review risk or skip to continue.',
  '3b': 'Calculate business case or skip to continue.',
}

const SKIPPABLE: (Phase)[] = ['3r', '3b']

export default function NavBar() {
  const { phaseFlags, currentPhase, setPhase } = useSessionStore()
  const pathname = usePathname()
  const router   = useRouter()

  // Everything driven by URL
  const urlPhase  = phaseFromPath(pathname)
  const cur       = urlPhase ?? currentPhase
  const curIdx    = phaseIndex(cur)
  const total     = PHASE_ORDER.length
  const hwIdx     = phaseIndex(currentPhase)  // highwater

  const isComplete = (phase: Phase) => phaseFlags[`phase_${phase}`] ?? false
  const phaseDone  = isComplete(cur)

  const hasPrev    = curIdx > 0
  const hasNext    = curIdx < total - 1
  const prevPhase  = hasPrev ? PHASE_ORDER[curIdx - 1] : null
  const nextPhase  = hasNext ? PHASE_ORDER[curIdx + 1] : null

  // Can go back always if there's a previous phase
  const canBack    = hasPrev

  // Can go forward if current phase is done, OR if we're below the highwater mark
  const canFwd     = hasNext && (phaseDone || curIdx < hwIdx)

  const isSkippable = SKIPPABLE.includes(cur) && !phaseDone
  const isLast      = !hasNext
  const hint        = !phaseDone && hasNext && curIdx >= hwIdx ? HINTS[cur as string | number] : ''

  const goBack = () => {
    if (canBack && prevPhase !== null) {
      router.push(`/phase/${prevPhase}`)
    }
  }

  const goForward = () => {
    if (canFwd && nextPhase !== null) {
      // Advance highwater if needed
      if (phaseIndex(nextPhase) > hwIdx) {
        setPhase(nextPhase)
      }
      router.push(`/phase/${nextPhase}`)
    }
  }

  const skip = () => {
    if (nextPhase !== null) {
      if (phaseIndex(nextPhase) > hwIdx) {
        setPhase(nextPhase)
      }
      router.push(`/phase/${nextPhase}`)
    }
  }

  return (
    <div className="flex items-center gap-4 px-6 py-3">

      {/* Back */}
      <div className="w-36 flex-shrink-0">
        {canBack && prevPhase !== null && (
          <button
            onClick={goBack}
            className="flex items-center gap-1.5 text-sm text-text-muted
                       border border-border rounded-lg px-3 py-2 w-full
                       hover:border-border-strong hover:text-text-primary
                       transition-all"
          >
            <ChevronLeft size={14} />
            <span className="truncate">{PHASE_LABELS[prevPhase as string | number]}</span>
          </button>
        )}
      </div>

      {/* Center */}
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
          nextPhase !== null && (
            <button
              onClick={goForward}
              disabled={!canFwd}
              className="flex items-center gap-1.5 text-sm font-semibold
                         bg-accent text-white rounded-lg px-4 py-2 w-full
                         justify-center hover:bg-accent-hover
                         transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <span className="truncate">{PHASE_LABELS[nextPhase as string | number]}</span>
              <ChevronRight size={14} className="flex-shrink-0" />
            </button>
          )
        )}
      </div>

    </div>
  )
}