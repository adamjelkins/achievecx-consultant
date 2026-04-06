'use client'

import { useSessionStore } from '@/store/session'
import { formatCurrency } from '@/lib/utils'
import { X, TrendingUp } from 'lucide-react'

export default function Sidebar() {
  const {
    businessProfile,
    convAnswers,
    businessCase,
    savingsSignalDismissed,
    dismissSavingsSignal,
    phaseFlags,
    discovery,
  } = useSessionStore()

  const company    = businessProfile?.company_name || ''
  const industry   = businessProfile?.industry || ''
  const domain     = businessProfile?.domain || ''
  const confirmedFlows = discovery.filter(f => f.confirmed)

  // ── Savings signal ──────────────────────────────────
  const savingsInfo = getSavingsInfo(industry, convAnswers, businessCase)

  return (
    <div className="flex flex-col h-full px-4 py-5 gap-4">

      {/* Wordmark */}
      <div className="flex-shrink-0">
        <div className="text-base font-bold tracking-tight text-white">
          AchieveCX
        </div>
        <div className="text-[10px] text-text-faint">AI Consultant</div>
      </div>

      {/* Savings signal */}
      {savingsInfo && !savingsSignalDismissed && (
        <div className={`flex-shrink-0 rounded-lg border-l-2 p-3 relative
          ${savingsInfo.color === 'green'
            ? 'bg-success/5 border-success'
            : savingsInfo.color === 'purple'
            ? 'bg-accent/8 border-accent'
            : 'bg-warning/5 border-warning'}`}
        >
          <button
            onClick={dismissSavingsSignal}
            className="absolute top-2 right-2 text-text-faint hover:text-text-muted"
          >
            <X size={12} />
          </button>
          <div className="flex items-center gap-1.5 mb-1">
            <TrendingUp size={11} className={
              savingsInfo.color === 'green' ? 'text-success' :
              savingsInfo.color === 'purple' ? 'text-accent' : 'text-warning'
            } />
            <span className="text-[9px] font-bold uppercase tracking-wider text-text-faint">
              {savingsInfo.label}
            </span>
          </div>
          <div className={`text-lg font-bold tracking-tight leading-none
            ${savingsInfo.color === 'green' ? 'text-success' :
              savingsInfo.color === 'purple' ? 'text-accent' : 'text-warning'}`}>
            {savingsInfo.range}
          </div>
          <div className={`text-[10px] font-semibold uppercase tracking-wider mt-0.5
            ${savingsInfo.color === 'green' ? 'text-success/70' :
              savingsInfo.color === 'purple' ? 'text-accent/70' : 'text-warning/70'}`}>
            per year
          </div>
          <div className="text-[10px] text-text-faint mt-1 leading-tight">
            {savingsInfo.caveat}
          </div>
        </div>
      )}

      {/* Business card */}
      {company && (
        <div className="flex-shrink-0">
          <div className="text-[9px] font-bold uppercase tracking-wider text-text-faint mb-1.5">
            Current Session
          </div>
          <div className="text-sm font-semibold text-white">{company}</div>
          {industry && (
            <div className="text-xs text-text-muted">{industry}</div>
          )}
          {domain && (
            <div className="text-[10px] text-text-faint">{domain}</div>
          )}
        </div>
      )}

      {/* Progress */}
      {company && (
        <div className="flex-shrink-0">
          <div className="text-[9px] font-bold uppercase tracking-wider text-text-faint mb-2">
            Session Progress
          </div>
          <div className="space-y-1.5">
            {[
              { key: 'phase_1', label: 'Business Profile' },
              { key: 'phase_2', label: 'Flow Confirmation' },
              { key: 'phase_3', label: 'AI Assessment' },
              { key: 'phase_3r', label: 'Risk Assessment' },
              { key: 'phase_3b', label: 'Business Case' },
              { key: 'phase_4', label: 'CX Blueprint' },
            ].map(({ key, label }) => {
              const done = phaseFlags[key as keyof typeof phaseFlags]
              return (
                <div key={key} className="flex items-center gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0
                    ${done ? 'bg-success' : 'bg-border'}`} />
                  <span className={`text-[11px] ${done ? 'text-text-secondary' : 'text-text-faint'}`}>
                    {label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Confirmed flows */}
      {confirmedFlows.length > 0 && (
        <div className="flex-shrink-0">
          <div className="text-[9px] font-bold uppercase tracking-wider text-text-faint mb-2">
            Confirmed Use Cases ({confirmedFlows.length})
          </div>
          <div className="space-y-1">
            {confirmedFlows.slice(0, 6).map(f => (
              <div key={f.flow_id} className="text-[11px] text-text-muted truncate">
                · {f.flow_name}
              </div>
            ))}
            {confirmedFlows.length > 6 && (
              <div className="text-[10px] text-text-faint">
                +{confirmedFlows.length - 6} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Footer */}
      <div className="flex-shrink-0 text-[10px] text-text-faint border-t border-border pt-3">
        AchieveCX · AI Consultant
      </div>

    </div>
  )
}

// ── Savings signal logic ─────────────────────────────

const BENCHMARKS: Record<string, { small: [number,number], mid: [number,number], large: [number,number] }> = {
  'Telecom':               { small:[200000,800000],   mid:[800000,3000000],   large:[3000000,12000000] },
  'Financial Services':    { small:[300000,1200000],  mid:[1200000,4500000],  large:[4500000,18000000] },
  'Healthcare':            { small:[150000,600000],   mid:[600000,2500000],   large:[2500000,10000000] },
  'Insurance':             { small:[250000,900000],   mid:[900000,3500000],   large:[3500000,14000000] },
  'Retail':                { small:[100000,400000],   mid:[400000,1500000],   large:[1500000,6000000]  },
  'Technology':            { small:[200000,700000],   mid:[700000,2800000],   large:[2800000,11000000] },
  'Hospitality':           { small:[80000,300000],    mid:[300000,1200000],   large:[1200000,4500000]  },
  'Logistics':             { small:[150000,500000],   mid:[500000,2000000],   large:[2000000,8000000]  },
  'Education':             { small:[50000,200000],    mid:[200000,800000],    large:[800000,3000000]   },
  'Manufacturing':         { small:[120000,450000],   mid:[450000,1800000],   large:[1800000,7000000]  },
  'Professional Services': { small:[150000,550000],   mid:[550000,2200000],   large:[2200000,9000000]  },
}

const DEFAULT_BENCH = { small:[100000,500000], mid:[500000,2000000], large:[2000000,8000000] }

const VOL_TIER: Record<string, 'small'|'mid'|'large'> = {
  'Under 1,000':      'small',
  '1,000 – 10,000':  'small',
  '10,000 – 50,000': 'mid',
  '50,000+':          'large',
}

function fmt(n: number) {
  if (n >= 1_000_000) return `$${(n/1_000_000).toFixed(1)}M`
  return `$${Math.round(n/1_000)}K`
}

function getSavingsInfo(
  industry: string,
  answers: Record<string,any>,
  businessCase: Record<string,any> | null
) {
  if (!industry) return null

  const bench = BENCHMARKS[industry] || DEFAULT_BENCH

  // Stage 3: real business case
  if (businessCase?.summary) {
    const base = businessCase.summary.base_annual_savings
    if (base > 0) {
      const [lo,,hi] = businessCase.summary.annual_savings_range || [0,0,0]
      return {
        label: 'Modeled Annual Savings',
        range: `${fmt(lo)} – ${fmt(hi)}`,
        caveat: `${fmt(base)} base case · based on your inputs`,
        color: 'green',
      }
    }
  }

  // Stage 2: volume known
  const vol = answers?.volume
  const tier = vol ? VOL_TIER[vol] : null
  if (tier) {
    const [lo, hi] = bench[tier]
    return {
      label: 'Estimated Annual Savings',
      range: `${fmt(lo)} – ${fmt(hi)}`,
      caveat: `${industry} benchmark · adjusted for your volume`,
      color: 'purple',
    }
  }

  // Stage 1: industry only
  const [loS] = bench.small
  const [,hiL] = bench.large
  return {
    label: 'Typical Annual Savings',
    range: `${fmt(loS)} – ${fmt(hiL)}`,
    caveat: `${industry} industry benchmark · narrows as we learn more`,
    color: 'amber',
  }
}