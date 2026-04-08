'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { useRouter } from 'next/navigation'
import { useSessionStore, type Phase, PHASE_ORDER, phaseFromPath, phaseIndex } from '@/store/session'
import { Sessions } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Check, Info } from 'lucide-react'
import Sidebar from '@/components/layout/Sidebar'
import NavBar from '@/components/layout/NavBar'

// ── Phase info ───────────────────────────────────────────────────

const PHASE_SHORT: Record<string | number, string> = {
  1: 'Profile', 2: 'Flows', 3: 'Assessment',
  '3r': 'Risk', '3b': 'Business Case', 4: 'Blueprint',
}

interface PhaseInfo { what: string; why: string }

function getPhaseInfo(phase: Phase, company: string): PhaseInfo {
  const co = company || 'your client'
  const map: Record<string | number, PhaseInfo> = {
    1:    { what: `Researching ${co} to identify likely customer interaction flows.`,
             why:  'Starting with a pre-built hypothesis saves hours of prep.' },
    2:    { what: `Mapping ${co}'s customer interaction flows and building their CX platform diagram.`,
             why:  'Confirmed flows become the foundation of the AI assessment, risk model, and financial case.' },
    3:    { what: `Scoring each of ${co}'s flows for AI readiness.`,
             why:  'This tells the client exactly where AI creates value and in what sequence to pursue it.' },
    '3r': { what: `Assessing implementation risk for ${co}'s AI transformation.`,
             why:  'Clients need to understand both sides of risk. Inaction has a cost too.' },
    '3b': { what: `Modeling the financial impact of AI-enabled CX for ${co}.`,
             why:  'A credible dollar figure changes the conversation from "interesting idea" to "when do we start."' },
    4:    { what: `Assembling ${co}'s complete CX transformation roadmap.`,
             why:  'This is the deliverable — a blueprint they can take back, share internally, and act on.' },
  }
  return map[phase as string | number] || map[1]
}

// ── Slim header ──────────────────────────────────────────────────

function SlimHeader() {
  const { phaseFlags, currentPhase, businessProfile } = useSessionStore()
  const pathname = usePathname()
  const router   = useRouter()
  const [tooltip, setTooltip] = useState(false)

  const urlPhase  = phaseFromPath(pathname)
  const activePh  = urlPhase ?? currentPhase
  const hwIdx     = phaseIndex(currentPhase)
  const company   = businessProfile?.company_name || ''
  const info      = getPhaseInfo(activePh, company)

  const isComplete   = (phase: Phase) => phaseFlags[`phase_${phase}`] ?? false
  const isActive     = (phase: Phase) => phase === urlPhase
  const isAccessible = (phase: Phase) => phaseIndex(phase) <= hwIdx + 1

  return (
    <div className="flex-shrink-0 border-b border-border bg-bg">
      <div className="flex items-center gap-0 px-6 py-2">

        {/* Pills */}
        <div className="flex items-center gap-0 flex-shrink-0">
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
                  onClick={() => !active && accessible && router.push(`/phase/${phase}`)}
                  disabled={!accessible}
                  className={cn(
                    'text-[10px] font-semibold px-2.5 py-1 rounded-full whitespace-nowrap transition-all',
                    active && 'bg-accent/10 text-accent border border-accent/30 cursor-default',
                    !active && complete && clickable &&
                      'bg-success/8 text-success border border-success/25 hover:bg-success/15 cursor-pointer',
                    !active && !complete && accessible &&
                      'text-text-muted border border-border cursor-pointer hover:border-border-strong',
                    !accessible && 'text-text-faint cursor-default opacity-40',
                  )}
                >
                  {complete && !active && <Check size={8} className="inline mr-1 -mt-px" />}
                  {active && <span className="mr-1 text-[8px]">●</span>}
                  {label}
                </button>
                {!isLast && <div className="w-3 h-px bg-border mx-0.5 flex-shrink-0" />}
              </div>
            )
          })}
        </div>

        {/* Divider */}
        <div className="w-px h-4 bg-border mx-4 flex-shrink-0" />

        {/* Context — inline truncated */}
        <div className="flex-1 min-w-0 flex items-center gap-2">
          <div className="text-xs text-text-dim truncate">{info.what}</div>
          <div className="relative flex-shrink-0">
            <button
              onMouseEnter={() => setTooltip(true)}
              onFocus={() => setTooltip(true)}
              onMouseLeave={() => setTooltip(false)}
              onBlur={() => setTooltip(false)}
              className="text-text-faint hover:text-accent transition-colors"
            >
              <Info size={12} />
            </button>
            {tooltip && (
              <div className="absolute left-0 top-full mt-1 z-50 w-64
                              bg-bg-card border border-border rounded-lg
                              shadow-lg px-3 py-2">
                <div className="text-[9px] font-bold uppercase tracking-wider
                                text-accent/60 mb-1">Why this matters</div>
                <div className="text-[11px] text-text-muted leading-relaxed">{info.why}</div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}

// ── AppShell ─────────────────────────────────────────────────────

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { sessionId, setSession } = useSessionStore()

  useEffect(() => {
    async function init() {
      if (sessionId) {
        try {
          const session = await Sessions.get(sessionId)
          setSession(session)
          return
        } catch { /* expired */ }
      }
      const session = await Sessions.create()
      setSession(session)
    }
    init()
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <aside className="w-60 flex-shrink-0 flex flex-col border-r border-border bg-bg overflow-y-auto">
        <Sidebar />
      </aside>
      <div className="flex-1 flex flex-col overflow-hidden">
        <SlimHeader />
        <main className="flex-1 overflow-y-auto px-6 pt-4 pb-24">
          {children}
        </main>
        <div className="flex-shrink-0 border-t border-border bg-bg/95 backdrop-blur-sm">
          <NavBar />
        </div>
      </div>
    </div>
  )
}