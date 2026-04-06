'use client'

import { useSessionStore, type Phase } from '@/store/session'

interface PhaseInfo {
  title: string
  what: string
  why: string
}

function getPhaseInfo(phase: Phase, company: string): PhaseInfo {
  const co = company || 'your client'

  const map: Record<string | number, PhaseInfo> = {
    1: {
      title: 'Business Profile',
      what:  `We're researching ${co} to identify their likely customer interaction flows.`,
      why:   'Starting with a pre-built hypothesis saves hours of prep and gets to the value conversation faster.',
    },
    2: {
      title: 'Flow Confirmation',
      what:  `We're mapping ${co}'s customer interaction flows and building their CX platform diagram.`,
      why:   'Confirmed flows become the foundation of the AI assessment, risk model, and financial case.',
    },
    3: {
      title: 'AI Maturity Assessment',
      what:  `We're scoring each of ${co}'s flows for AI readiness — what can be automated, assisted, or left manual.`,
      why:   'This tells the client exactly where AI creates value and in what sequence to pursue it.',
    },
    '3r': {
      title: 'Implementation Risk',
      what:  `We're assessing the implementation risk for ${co}'s AI transformation — and the risk of doing nothing.`,
      why:   'Clients need to understand both sides of risk. Inaction has a cost too.',
    },
    '3b': {
      title: 'Business Case',
      what:  `We're modeling the financial impact of AI-enabled CX for ${co}.`,
      why:   'A credible dollar figure changes the conversation from "interesting idea" to "when do we start."',
    },
    4: {
      title: 'CX Blueprint',
      what:  `We're assembling ${co}'s complete CX transformation roadmap.`,
      why:   'This is the deliverable — a blueprint they can take back, share internally, and act on.',
    },
  }

  return map[phase as string | number] || map[1]
}

export default function PhaseContext() {
  const { currentPhase, businessProfile } = useSessionStore()
  const company = businessProfile?.company_name || ''
  const info = getPhaseInfo(currentPhase, company)

  return (
    <div className="flex-shrink-0 px-6 py-3 border-b border-border bg-bg-card/50">
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-dim mb-0.5">
            {info.title}
          </div>
          <div className="text-sm text-text-secondary leading-snug">
            {info.what}
          </div>
        </div>
        <div className="flex-shrink-0 max-w-xs hidden lg:block">
          <div className="text-[10px] font-bold uppercase tracking-wider text-accent/60 mb-0.5">
            Why this matters
          </div>
          <div className="text-xs text-text-muted leading-snug">
            {info.why}
          </div>
        </div>
      </div>
    </div>
  )
}