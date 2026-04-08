'use client'

import { useState, useEffect } from 'react'
import { useSessionStore } from '@/store/session'
import { Risk } from '@/lib/api'
import AppShell from '@/components/layout/AppShell'
import { Loader2, Shield } from 'lucide-react'

const RISK_COLORS: Record<string, string> = {
  Low:      '#4ade80',
  Moderate: '#fbbf24',
  High:     '#f87171',
  Critical: '#ef4444',
}

const DIM_LABELS: Record<string, string> = {
  integration:  'Integration Complexity',
  timeline:     'Timeline Pressure',
  automation:   'Automation Baseline',
  volume:       'Contact Volume',
  flow_complexity: 'Flow Complexity',
}

function RiskBar({ score, color }: { score: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-bg-surface2 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
      <div className="text-xs font-semibold w-6 text-right" style={{ color }}>
        {score}
      </div>
    </div>
  )
}

function InactionCard({ item }: { item: any }) {
  const colors: Record<string, string> = {
    'Technology Obsolescence':   '#f87171',
    'Competitive Displacement':  '#fb923c',
    'Customer Experience Drift': '#fbbf24',
    'Cost Trajectory':           '#a78bfa',
  }
  const color = colors[item.dimension] || '#818cf8'

  return (
    <div className="rounded-lg border p-4"
      style={{ borderColor: color + '33', borderTop: `2px solid ${color}`, background: '#0f0f0f' }}>
      <div className="text-[9px] font-bold uppercase tracking-wider mb-1.5" style={{ color }}>
        {item.dimension}
      </div>
      <div className="text-sm font-semibold text-text-primary mb-2 leading-snug">
        {item.headline}
      </div>
      <div className="text-xs text-text-muted leading-relaxed">
        {item.body}
      </div>
    </div>
  )
}

export default function Phase3rPage() {
  const { sessionId, riskAssessment, setRiskAssessment } = useSessionStore()

  const [running, setRunning]     = useState(false)
  const [error, setError]         = useState('')
  const [localData, setLocalData] = useState<any>(riskAssessment)

  useEffect(() => {
    if (riskAssessment && Object.keys(riskAssessment).length > 0) {
      setLocalData(riskAssessment)
    }
  }, [riskAssessment])

  const runRisk = async () => {
    if (!sessionId) return
    setRunning(true)
    setError('')
    try {
      const result = await Risk.run(sessionId)
      setRiskAssessment(result)
      setLocalData(result)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Risk assessment failed — please try again.')
    } finally {
      setRunning(false)
    }
  }

  const data           = localData
  const score          = data?.program_score || 0
  const label          = data?.program_label || ''
  const color          = data?.program_color || '#fbbf24'
  const icon           = data?.program_icon || '⚠️'
  const dimensions     = data?.dimension_scores || {}
  const narrative      = data?.narrative || ''
  const inactionRisks  = data?.inaction_risks || []
  const mitigations    = data?.mitigations || []
  const flowRisks      = data?.top_risk_flows || []

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">

        {!data ? (
          // ── Not yet run ──
          <div className="flex flex-col items-center justify-center py-16 gap-6">
            <div className="text-center">
              <div className="text-lg font-semibold text-text-primary mb-2">
                Ready to run the Risk Assessment
              </div>
              <div className="text-sm text-text-muted max-w-md">
                We'll assess implementation risk across 5 dimensions — and model
                the cost of doing nothing.
              </div>
            </div>

            {error && (
              <div className="text-sm text-danger bg-danger/10 border border-danger/20
                              rounded-lg px-4 py-2">
                {error}
              </div>
            )}

            <button
              onClick={runRisk}
              disabled={running}
              className="flex items-center gap-2 bg-accent hover:bg-accent-hover
                         text-white font-semibold text-sm rounded-lg px-6 py-3
                         transition-all disabled:opacity-50"
            >
              {running ? (
                <><Loader2 size={16} className="animate-spin" />Running Risk Assessment...</>
              ) : (
                <><Shield size={16} />Run Risk Assessment</>
              )}
            </button>
          </div>

        ) : (
          // ── Results ──
          <div className="space-y-6 pb-8">

            {/* Score + narrative */}
            <div className="flex items-center gap-6 pt-4">
              <div className="flex flex-col items-center gap-1 flex-shrink-0">
                <div className="text-5xl font-bold tracking-tight" style={{ color }}>
                  {score}
                </div>
                <div className="text-xs font-semibold" style={{ color }}>{icon} {label}</div>
                <div className="text-[10px] text-text-dim">Implementation Risk</div>
              </div>

              {narrative && (
                <div className="flex-1 rounded-lg border-l-2 px-4 py-3 bg-bg-card"
                  style={{ borderColor: color }}>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-text-dim mb-1">
                    Why This Risk Level
                  </div>
                  <div className="text-sm text-text-secondary leading-relaxed">
                    {narrative}
                  </div>
                </div>
              )}
            </div>

            {/* Inaction risks — shown early for impact */}
            {inactionRisks.length > 0 && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-1">
                  Risk of Inaction
                </div>
                <div className="text-[11px] text-text-dim mb-3">
                  The cost of staying the same.
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {inactionRisks.map((item: any, i: number) => (
                    <InactionCard key={i} item={item} />
                  ))}
                </div>
              </div>
            )}

            {/* Risk dimensions */}
            {Object.keys(dimensions).length > 0 && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
                  Risk Dimensions
                </div>
                <div className="space-y-3">
                  {Object.entries(dimensions).map(([key, dim]: [string, any]) => (
                    <div key={key} className="bg-bg-card rounded-lg border border-border p-3">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="text-xs font-medium text-text-secondary">
                          {DIM_LABELS[key] || key}
                        </div>
                        <div className="text-[10px] font-semibold"
                          style={{ color: RISK_COLORS[dim.label] || color }}>
                          {dim.label}
                        </div>
                      </div>
                      <RiskBar
                        score={dim.score || 0}
                        color={RISK_COLORS[dim.label] || color}
                      />
                      {dim.reason && (
                        <div className="text-[10px] text-text-dim mt-1.5">{dim.reason}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mitigations */}
            {mitigations.length > 0 && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
                  Recommended Mitigations
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {mitigations.map((mit: any, i: number) => {
                    const text = typeof mit === 'string' ? mit : mit?.description || String(mit)
                    return (
                      <div key={i}
                        className="bg-bg-card border border-border rounded-lg p-3
                                   flex items-start gap-2.5">
                        <span className="text-accent text-sm flex-shrink-0 mt-0.5">›</span>
                        <div className="text-xs text-text-secondary leading-relaxed">{text}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Top risk flows */}
            {flowRisks.length > 0 && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
                  Highest Risk Use Cases
                </div>
                <div className="space-y-2">
                  {flowRisks.map((flow: any, i: number) => (
                    <div key={i}
                      className="flex items-center gap-3 bg-bg-card border border-border
                                 rounded-lg px-4 py-2.5">
                      <div className="text-sm font-semibold text-danger w-6 flex-shrink-0">
                        {flow.risk_score}
                      </div>
                      <div className="flex-1 text-sm text-text-secondary">
                        {flow.flow_name}
                      </div>
                      {flow.factors?.slice(0, 1).map((f: string, j: number) => (
                        <div key={j} className="text-[10px] text-text-dim">{f}</div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Re-run */}
            <div className="flex justify-end">
              <button
                onClick={runRisk}
                disabled={running}
                className="flex items-center gap-2 text-xs text-text-dim
                           border border-border rounded-lg px-3 py-2
                           hover:text-text-muted hover:border-border-strong
                           transition-all disabled:opacity-50"
              >
                {running ? <Loader2 size={12} className="animate-spin" /> : <Shield size={12} />}
                Re-run Risk Assessment
              </button>
            </div>

          </div>
        )}
      </div>
    </AppShell>
  )
}