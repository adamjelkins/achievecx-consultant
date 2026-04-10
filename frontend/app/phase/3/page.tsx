'use client'

import { useState, useEffect } from 'react'
import { useSessionStore } from '@/store/session'
import { Assessment } from '@/lib/api'
import AppShell from '@/components/layout/AppShell'
import { Loader2, Zap, ArrowRight, Wrench } from 'lucide-react'

// ── Colors ──────────────────────────────────────────────────────

const CWR_COLORS: Record<string, string> = {
  Run:   '#4ade80',
  Walk:  '#fbbf24',
  Crawl: '#9ca3af',
}

const CWR_LABELS: Record<string, string> = {
  Run:   '✓ AI Automated',
  Walk:  '⚡ AI Assisted',
  Crawl: '🔧 Stay Manual',
}

const CWR_ICONS = {
  Run:   <Zap size={14} color="#4ade80" />,
  Walk:  <ArrowRight size={14} color="#fbbf24" />,
  Crawl: <Wrench size={14} color="#9ca3af" />,
}

// ── Score gauge ──────────────────────────────────────────────────

function ScoreGauge({ score, label, color }: { score: number; label: string; color: string }) {
  const circumference = 2 * Math.PI * 54
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-36 h-36">
        <svg width="144" height="144" viewBox="0 0 144 144">
          <circle cx="72" cy="72" r="54" fill="none" stroke="#1f1f1f" strokeWidth="10" />
          <circle
            cx="72" cy="72" r="54"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 72 72)"
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-4xl font-bold tracking-tight" style={{ color }}>{score}</div>
          <div className="text-[10px] text-text-dim uppercase tracking-wider mt-0.5">AI Score</div>
        </div>
      </div>
      <div className="text-sm font-semibold" style={{ color }}>{label}</div>
      <div className="text-xs text-text-muted text-center max-w-xs">
        Overall AI readiness across all confirmed use cases
      </div>
    </div>
  )
}

// ── Shared tag + field components ────────────────────────────────

const Tag = ({ label, color }: { label: string; color?: string }) => (
  <span style={{
    background: (color || '#818cf8') + '18',
    border: `1px solid ${(color || '#818cf8')}33`,
    borderRadius: 3, padding: '1px 6px',
    fontSize: 10, color: color || '#a0a0a0',
    display: 'inline-block',
  }}>{label}</span>
)

const FieldLabel = ({ label }: { label: string }) => (
  <div style={{ fontSize: 9, fontWeight: 700, color: '#606060',
    textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>{label}</div>
)

// ── Flow card ────────────────────────────────────────────────────

function FlowCard({ flow }: { flow: any }) {
  const [expanded, setExpanded] = useState(false)
  const cwr   = flow.crawl_walk_run || 'Crawl'
  const color = CWR_COLORS[cwr] || '#9ca3af'
  const label = CWR_LABELS[cwr] || cwr
  const score = flow.ai_score || 0

  return (
    <div
      className="rounded-lg cursor-pointer transition-all"
      style={{
        background: expanded ? '#141414' : '#0f0f0f',
        borderTop:    `1px solid ${expanded ? color + '44' : '#2a2a2a'}`,
        borderRight:  `1px solid ${expanded ? color + '44' : '#2a2a2a'}`,
        borderBottom: `1px solid ${expanded ? color + '44' : '#2a2a2a'}`,
        borderLeft:   `3px solid ${color}`,
        borderRadius: 8,
      }}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header row */}
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="flex-shrink-0 w-8 text-right">
          <div className="text-sm font-bold" style={{ color }}>{score}</div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-text-primary truncate">{flow.flow_name}</div>
          <div className="text-xs mt-0.5" style={{ color }}>{label}</div>
        </div>
        {flow.contain_display && (
          <div className="flex-shrink-0 text-right">
            <div className="text-sm font-bold text-success">{flow.contain_display}</div>
            <div className="text-[10px] text-text-dim">containment</div>
          </div>
        )}
        <div className="flex-shrink-0 text-text-faint text-xs">{expanded ? '▲' : '▼'}</div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-border/50 pt-3 space-y-3">
          {/* Rationale */}
          {flow.rationale && (
            <div className="text-xs text-text-muted leading-relaxed">{flow.rationale}</div>
          )}

          {/* Metrics row */}
          <div className="flex gap-4 flex-wrap">
            {flow.complexity && (
              <div>
                <FieldLabel label="Complexity" />
                <div className="text-xs text-text-secondary">{flow.complexity}</div>
              </div>
            )}
            {flow.human_role && (
              <div>
                <FieldLabel label="Human Role" />
                <div className="text-xs text-text-secondary">{flow.human_role}</div>
              </div>
            )}
            {flow.authentication && (
              <div className="flex-1 min-w-0">
                <FieldLabel label="Authentication" />
                <div className="text-xs text-text-dim">{flow.authentication}</div>
              </div>
            )}
          </div>

          {/* Human role detail */}
          {flow.human_detail && (
            <div>
              <FieldLabel label="Agent Responsibility" />
              <div className="text-xs text-text-dim leading-relaxed">{flow.human_detail}</div>
            </div>
          )}

          {/* Intents */}
          {flow.intents?.length > 0 && (
            <div>
              <FieldLabel label="Common Intents" />
              <div className="flex flex-wrap gap-1.5">
                {flow.intents.map((intent: string) => <Tag key={intent} label={intent} color={color} />)}
              </div>
            </div>
          )}

          {/* Channels + Data Sources side by side */}
          <div className="flex gap-6 flex-wrap">
            {flow.entry_channels?.length > 0 && (
              <div>
                <FieldLabel label="Channels" />
                <div className="flex flex-wrap gap-1.5">
                  {flow.entry_channels.map((ch: string) => <Tag key={ch} label={ch} />)}
                </div>
              </div>
            )}
            {flow.data_sources?.length > 0 && (
              <div>
                <FieldLabel label="Data Sources" />
                <div className="flex flex-wrap gap-1.5">
                  {flow.data_sources.map((ds: string) => <Tag key={ds} label={ds} />)}
                </div>
              </div>
            )}
            {flow.output_actions?.length > 0 && (
              <div>
                <FieldLabel label="Output Actions" />
                <div className="flex flex-wrap gap-1.5">
                  {flow.output_actions.map((a: string) => <Tag key={a} label={a} color="#fbbf24" />)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────

export default function Phase3Page() {
  const { sessionId, assessment, setAssessment, setPhase } = useSessionStore()

  const [running, setRunning]   = useState(false)
  const [error, setError]       = useState('')
  const [localData, setLocalData] = useState<any>(assessment)

  // If already run, show results
  useEffect(() => {
    if (assessment && Object.keys(assessment).length > 0) {
      setLocalData(assessment)
    }
  }, [assessment])

  const runAssessment = async () => {
    if (!sessionId) return
    setRunning(true)
    setError('')
    try {
      const result = await Assessment.run(sessionId)
      setAssessment(result)
      setLocalData(result)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Assessment failed — please try again.')
    } finally {
      setRunning(false)
    }
  }

  const data         = localData
  const score        = data?.business_ai_score || 0
  const label        = data?.score_label || ''
  const color        = data?.score_color || '#818cf8'
  const scoredFlows  = data?.scored_flows || []
  const quickWins    = data?.quick_wins || []
  const runFlows     = data?.run_flows || []
  const walkFlows    = data?.walk_flows || []
  const crawlFlows   = data?.crawl_flows || []

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">

        {!data ? (
          // ── Not yet run ──
          <div className="flex flex-col items-center justify-center py-16 gap-6">
            <div className="text-center">
              <div className="text-lg font-semibold text-text-primary mb-2">
                Ready to run the AI Maturity Assessment
              </div>
              <div className="text-sm text-text-muted max-w-md">
                We'll score each confirmed use case for AI readiness across
                automation potential, integration complexity, and business impact.
              </div>
            </div>

            {error && (
              <div className="text-sm text-danger bg-danger/10 border border-danger/20
                              rounded-lg px-4 py-2">
                {error}
              </div>
            )}

            <button
              onClick={runAssessment}
              disabled={running}
              className="flex items-center gap-2 bg-accent hover:bg-accent-hover
                         text-white font-semibold text-sm rounded-lg px-6 py-3
                         transition-all disabled:opacity-50"
            >
              {running ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Running Assessment...
                </>
              ) : (
                <>
                  <Zap size={16} />
                  Run AI Assessment
                </>
              )}
            </button>

            {running && (
              <div className="text-xs text-text-dim animate-pulse">
                Scoring {scoredFlows.length > 0 ? scoredFlows.length : 'all'} use cases
                across 3 dimensions — this takes about 15 seconds...
              </div>
            )}
          </div>

        ) : (
          // ── Results ──
          <div className="space-y-8 pb-8">

            {/* Score header */}
            <div className="flex items-center gap-8 pt-4">
              <ScoreGauge score={score} label={label} color={color} />
              <div className="flex-1">
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'AI Automated', flows: runFlows,   color: '#4ade80' },
                    { label: 'AI Assisted',  flows: walkFlows,  color: '#fbbf24' },
                    { label: 'Stay Manual',  flows: crawlFlows, color: '#9ca3af' },
                  ].map(({ label, flows, color }) => (
                    <div key={label}
                      className="rounded-lg border p-3 text-center"
                      style={{ borderColor: color + '33', background: color + '08' }}>
                      <div className="text-2xl font-bold" style={{ color }}>
                        {flows.length}
                      </div>
                      <div className="text-xs mt-0.5" style={{ color }}>{label}</div>
                    </div>
                  ))}
                </div>

                {quickWins.length > 0 && (
                  <div className="mt-3 rounded-lg border border-success/25
                                  bg-success/5 px-3 py-2">
                    <div className="text-[10px] font-bold uppercase tracking-wider
                                    text-success mb-1">
                      ⚡ {quickWins.length} Quick Win{quickWins.length !== 1 ? 's' : ''} Identified
                    </div>
                    <div className="text-xs text-text-muted">
                      {quickWins.map((f: any) => f.flow_name).join(' · ')}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Flow cards — sorted by score */}
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider
                              text-text-faint mb-3">
                Use Case Breakdown — sorted by AI readiness
              </div>
              <div className="space-y-2">
                {scoredFlows.map((flow: any) => (
                  <FlowCard key={flow.flow_id} flow={flow} />
                ))}
              </div>
            </div>

            {/* Re-run button */}
            <div className="flex justify-end">
              <button
                onClick={runAssessment}
                disabled={running}
                className="flex items-center gap-2 text-xs text-text-dim
                           border border-border rounded-lg px-3 py-2
                           hover:text-text-muted hover:border-border-strong
                           transition-all disabled:opacity-50"
              >
                {running ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
                Re-run Assessment
              </button>
            </div>

          </div>
        )}
      </div>
    </AppShell>
  )
}