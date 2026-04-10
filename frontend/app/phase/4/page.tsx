'use client'

import { useState, useEffect } from 'react'
import { useSessionStore } from '@/store/session'
import { Blueprint } from '@/lib/api'
import AppShell from '@/components/layout/AppShell'
import { Loader2, FileText, ExternalLink, Download } from 'lucide-react'

// ── Helpers ──────────────────────────────────────────────────────

function fmt(n: number | null | undefined, decimals = 0): string {
  if (n == null || isNaN(n)) return '—'
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (Math.abs(n) >= 1_000)     return `$${Math.round(n / 1_000)}K`
  return `$${n.toFixed(decimals)}`
}

function fmtMonths(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return '—'
  return `${Math.round(n)} months`
}

const CWR_COLORS: Record<string, string> = {
  Run: '#4ade80', Walk: '#fbbf24', Crawl: '#9ca3af',
}
const CWR_DISPLAY: Record<string, string> = {
  Run: '✓ AI Automated', Walk: '⚡ AI Assisted', Crawl: '🔧 Stay Manual',
}

// ── Stat card ────────────────────────────────────────────────────

function StatCard({ value, label, color = '#f1f5f9' }: { value: string | number; label: string; color?: string }) {
  return (
    <div className="rounded-lg border border-border bg-bg-card p-4">
      <div className="text-2xl font-bold tracking-tight leading-none mb-1" style={{ color }}>
        {value}
      </div>
      <div className="text-[10px] text-text-dim">{label}</div>
    </div>
  )
}

// ── Tab: Summary ─────────────────────────────────────────────────

function TabSummary({ bp }: { bp: any }) {
  const score = bp.business_ai_score || 0
  const color = bp.score_color || '#818cf8'

  return (
    <div className="space-y-6">
      {bp.executive_summary && (
        <div className="rounded-lg border border-border bg-bg-card p-5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
            Executive Summary
          </div>
          <div className="text-sm text-text-muted leading-relaxed italic">
            {bp.executive_summary}
          </div>
        </div>
      )}

      <div className="grid grid-cols-4 gap-3">
        <StatCard value={score} label={`AI Score · ${bp.score_label || ''}`} color={color} />
        <StatCard value={bp.confirmed_flow_count || 0} label="Confirmed Flows" />
        <StatCard value={bp.quick_win_count || 0} label="Quick Wins" />
        <StatCard value={bp.industry || '—'} label="Industry" />
      </div>

      {/* Profile summary */}
      <div className="rounded-lg border border-border bg-bg-card p-4">
        <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
          Client Profile
        </div>
        <div className="grid grid-cols-3 gap-3">
          {[
            ['Company',   bp.company_name],
            ['Domain',    bp.domain],
            ['Industry',  bp.industry],
            ['CRM',       bp.crm],
            ['Platform',  bp.cc_platform],
            ['Channels',  Array.isArray(bp.channels) ? bp.channels.join(', ') : bp.channels],
            ['Regions',   Array.isArray(bp.regions) ? bp.regions.join(', ') : bp.regions],
            ['Goal',      bp.primary_goal],
            ['Timeline',  bp.timeline],
          ].filter(([, v]) => v).map(([label, value]) => (
            <div key={label as string}>
              <div className="text-[10px] text-text-dim mb-0.5">{label}</div>
              <div className="text-xs text-text-secondary">{value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Tab: Business Case ───────────────────────────────────────────

function TabBusinessCase({ bp }: { bp: any }) {
  const bc = bp.business_case || {}
  if (!bc.has_data) {
    return (
      <div className="text-sm text-text-muted py-8 text-center">
        No business case data — run the Business Case calculator in Phase 5.
      </div>
    )
  }

  const drivers = bc.savings_by_driver || {}
  const maxDriver = Math.max(...Object.values(drivers as Record<string, number>).map(Math.abs), 1)
  const driverColors: Record<string, string> = {
    'Labor reduction':    '#818cf8',
    'Churn reduction':    '#4ade80',
    'Overhead reduction': '#fbbf24',
    'Tech delta':         '#52525b',
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-3">
        <StatCard value={fmt(bc.annual_savings)} label="Annual Savings (Base)" color="#4ade80" />
        <StatCard value={fmtMonths(bc.payback_months)} label="Payback Period" />
        <StatCard value={fmt(bc.npv_5yr)} label="5-Year NPV" color="#4ade80" />
      </div>

      {/* Conservative / Optimistic range */}
      <div className="rounded-lg border border-border bg-bg-card p-4">
        <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
          Savings Range
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-[10px] text-text-dim mb-1">Conservative</div>
            <div className="text-lg font-bold text-warning">{fmt(bc.conservative_savings)}</div>
          </div>
          <div>
            <div className="text-[10px] text-text-dim mb-1">Base Case</div>
            <div className="text-lg font-bold text-accent">{fmt(bc.annual_savings)}</div>
          </div>
          <div>
            <div className="text-[10px] text-text-dim mb-1">Optimistic</div>
            <div className="text-lg font-bold text-success">{fmt(bc.optimistic_savings)}</div>
          </div>
        </div>
      </div>

      {/* Environment comparison */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { title: 'Current',  agents: bc.current_agents,  total: bc.current_total,  cpc: bc.current_cpc,  color: '#52525b' },
          { title: 'Proposed', agents: bc.proposed_agents, total: bc.proposed_total, cpc: bc.proposed_cpc, color: '#818cf8' },
        ].map(({ title, agents, total, cpc, color }) => (
          <div key={title} className="rounded-lg p-4"
            style={{ borderTop: `2px solid ${color}`, border: `1px solid ${color}33`, background: '#0f0f0f', borderRadius: 8 }}>
            <div className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color }}>{title}</div>
            <div className="flex justify-between mb-1">
              <span className="text-[11px] text-text-dim">Agents</span>
              <span className="text-xs text-text-secondary">{agents || '—'}</span>
            </div>
            <div className="flex justify-between mb-1">
              <span className="text-[11px] text-text-dim">Total Cost</span>
              <span className="text-xs font-semibold" style={{ color }}>{fmt(total)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[11px] text-text-dim">Cost / Contact</span>
              <span className="text-xs text-text-secondary">{fmt(cpc, 2)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Savings by driver */}
      <div className="rounded-lg border border-border bg-bg-card p-4">
        <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
          Savings by Driver
        </div>
        <div className="space-y-3">
          {Object.entries(drivers as Record<string, number>)
            .sort(([, a], [, b]) => b - a)
            .map(([driver, amount]) => {
              const barPct = Math.max(0, (Math.abs(amount) / maxDriver) * 100)
              const color  = driverColors[driver] || '#818cf8'
              const ac     = amount >= 0 ? '#4ade80' : '#f87171'
              return (
                <div key={driver}>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-text-muted">{driver}</span>
                    <span className="text-xs font-semibold" style={{ color: ac }}>
                      {amount >= 0 ? '+' : ''}{fmt(amount)}
                    </span>
                  </div>
                  <div className="h-1.5 bg-bg-surface2 rounded-full">
                    <div className="h-full rounded-full" style={{ width: `${barPct}%`, background: color }} />
                  </div>
                </div>
              )
            })}
        </div>
      </div>
    </div>
  )
}

// ── Tab: Risk ────────────────────────────────────────────────────

function TabRisk({ bp }: { bp: any }) {
  const risk = bp.risk_assessment || {}
  if (!risk.has_data) {
    return (
      <div className="text-sm text-text-muted py-8 text-center">
        No risk data — run the Risk Assessment in Phase 4.
      </div>
    )
  }

  const color = risk.program_color || '#fbbf24'
  const dims  = risk.dimension_scores || {}
  const RISK_COLORS: Record<string, string> = {
    Low: '#4ade80', Moderate: '#fbbf24', High: '#f87171', Critical: '#ef4444',
  }
  const DIM_LABELS: Record<string, string> = {
    integration: 'Integration Complexity', timeline: 'Timeline Pressure',
    automation: 'Automation Baseline', volume: 'Contact Volume',
    flow_complexity: 'Flow Complexity',
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-6">
        <div className="text-center flex-shrink-0">
          <div className="text-5xl font-bold" style={{ color }}>{risk.program_score}</div>
          <div className="text-xs font-semibold mt-1" style={{ color }}>
            {risk.program_icon} {risk.program_label}
          </div>
          <div className="text-[10px] text-text-dim mt-0.5">Implementation Risk</div>
        </div>
        <div className="flex-1 space-y-2">
          {Object.entries(dims).map(([key, dim]: [string, any]) => (
            <div key={key}>
              <div className="flex justify-between mb-0.5">
                <span className="text-[11px] text-text-muted">{DIM_LABELS[key] || key}</span>
                <span className="text-[10px] font-semibold"
                  style={{ color: RISK_COLORS[dim.label] || color }}>{dim.label}</span>
              </div>
              <div className="h-1.5 bg-bg-surface2 rounded-full">
                <div className="h-full rounded-full"
                  style={{ width: `${dim.score || 0}%`, background: RISK_COLORS[dim.label] || color }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {risk.top_risk_flows?.length > 0 && (
        <div className="rounded-lg border border-border bg-bg-card p-4">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
            Highest Risk Use Cases
          </div>
          <div className="space-y-2">
            {risk.top_risk_flows.map((f: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <div className="text-sm font-bold text-danger w-6">{f.risk_score}</div>
                <div className="text-sm text-text-secondary">{f.flow_name}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {risk.mitigations?.length > 0 && (
        <div className="rounded-lg border border-border bg-bg-card p-4">
          <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
            Mitigations
          </div>
          <div className="space-y-2">
            {risk.mitigations.map((m: any, i: number) => (
              <div key={i} className="flex gap-2 text-xs text-text-muted">
                <span className="text-accent flex-shrink-0">→</span>
                <span>{typeof m === 'string' ? m : m?.description || String(m)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Tab: Vendors ─────────────────────────────────────────────────

function TabVendors({ bp }: { bp: any }) {
  const vendors = bp.vendor_shortlist || []
  if (!vendors.length) {
    return (
      <div className="text-sm text-text-muted py-8 text-center">
        No vendor data available.
      </div>
    )
  }

  const rankColors: Record<number, string> = { 1: '#4ade80', 2: '#818cf8', 3: '#fbbf24' }

  return (
    <div className="space-y-4">
      <div className="text-sm text-text-muted">
        Top vendors matched to your confirmed flows, industry, platform, and AI opportunity score.
        Rankings are based on fit — not commercial relationships.
      </div>
      {vendors.map((v: any) => {
        const scoreColor = v.fit_score >= 75 ? '#4ade80' : v.fit_score >= 55 ? '#818cf8' : '#fbbf24'
        const borderColor = v.featured ? '#818cf8' : (v.rank === 1 ? '#4ade80' : '#2a2a2a')
        const rankColor = rankColors[v.rank] || '#52525b'

        return (
          <div key={v.vendor_id} className="rounded-lg p-4"
            style={{
              borderLeft: `3px solid ${borderColor}`,
              border: `1px solid ${borderColor}33`,
              borderRadius: 8,
              background: '#0f0f0f',
            }}>
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                {v.logo_domain && (
                  <img
                    src={`https://www.google.com/s2/favicons?domain=${v.logo_domain}&sz=32`}
                    width={18} height={18}
                    className="rounded flex-shrink-0"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                )}
                <div className="text-sm font-semibold text-text-primary">{v.name}</div>
                {v.featured && (
                  <span className="text-[10px] font-semibold text-accent
                                   bg-accent/10 border border-accent/20 rounded px-1.5 py-0.5">
                    {v.feat_label || 'Featured'}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <div className="text-right">
                  <div className="text-sm font-bold" style={{ color: scoreColor }}>{v.fit_score}</div>
                  <div className="text-[10px] text-text-dim">fit score</div>
                </div>
                <div className="text-sm font-bold" style={{ color: rankColor }}>#{v.rank}</div>
              </div>
            </div>

            <div className="text-xs text-text-dim mb-2">{v.tier?.replace(/-/g, ' ')}</div>
            <div className="text-xs text-text-muted leading-relaxed mb-3">{v.description}</div>

            {v.fit_reasons?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {v.fit_reasons.map((r: string, i: number) => (
                  <span key={i} className="text-[10px] bg-bg-surface border border-border
                                           rounded px-1.5 py-0.5 text-text-dim">
                    {r}
                  </span>
                ))}
              </div>
            )}

            {v.website && (
              <a href={v.website} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1 text-[10px] text-accent hover:underline">
                <ExternalLink size={10} />
                {v.website.replace('https://', '')}
              </a>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Tab: Roadmap ─────────────────────────────────────────────────

function TabRoadmap({ bp }: { bp: any }) {
  const sections = [
    { title: 'NOW — Quick Wins',       flows: bp.quick_wins  || [], color: '#4ade80', icon: '🟢' },
    { title: 'NEXT — AI-Assisted',     flows: bp.walk_flows  || [], color: '#fbbf24', icon: '⚡' },
    { title: 'LATER — Foundation First', flows: bp.crawl_flows || [], color: '#9ca3af', icon: '🔧' },
  ]

  return (
    <div className="space-y-2">
      {sections.map(({ title, flows, color, icon }) => {
        if (!flows.length) return null
        return (
          <div key={title}>
            <div className="flex items-center gap-2 my-4">
              <span>{icon}</span>
              <span className="text-xs font-semibold" style={{ color }}>{title}</span>
              <div className="flex-1 h-px bg-border" />
            </div>
            <div className="space-y-2">
              {flows.map((flow: any, i: number) => (
                <div key={i} className="rounded-lg p-3"
                  style={{
                    borderLeft: `2px solid ${color}`,
                    border: `1px solid ${color}22`,
                    borderRadius: 8,
                    background: '#0f0f0f',
                  }}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm font-semibold text-text-primary">
                      {flow.flow_name}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold" style={{ color: CWR_COLORS[flow.crawl_walk_run] || color }}>
                        {flow.ai_score}
                      </span>
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                        style={{ color, background: color + '18', border: `1px solid ${color}33` }}>
                        {CWR_DISPLAY[flow.crawl_walk_run] || flow.crawl_walk_run}
                      </span>
                    </div>
                  </div>
                  {flow.rationale && (
                    <div className="text-xs text-text-dim leading-relaxed">{flow.rationale}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Tab: Flow Designs ─────────────────────────────────────────────

function TabFlowDesigns({ bp }: { bp: any }) {
  const [selected, setSelected] = useState<number>(0)
  const flows = bp.flow_cards || []

  if (!flows.length) {
    return <div className="text-sm text-text-muted py-8 text-center">No flow data available.</div>
  }

  const flow = flows[selected]
  const color = CWR_COLORS[flow?.crawl_walk_run] || '#818cf8'

  const Tag = ({ label, c }: { label: string; c?: string }) => (
    <span className="text-[10px] rounded px-1.5 py-0.5" style={{
      background: (c || color) + '18',
      border: `1px solid ${(c || color)}33`,
      color: c || color,
    }}>{label}</span>
  )

  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div>
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-1.5">{label}</div>
      {children}
    </div>
  )

  return (
    <div className="flex gap-4" style={{ minHeight: 400 }}>
      {/* Flow list — CWR colored */}
      <div className="w-48 flex-shrink-0 space-y-1">
        {flows.map((f: any, i: number) => {
          const fc = CWR_COLORS[f.crawl_walk_run] || '#818cf8'
          const isSelected = selected === i
          return (
            <button key={i} onClick={() => setSelected(i)}
              className="w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-center gap-2"
              style={{
                background: isSelected ? fc + '15' : 'transparent',
                border: `1px solid ${isSelected ? fc + '44' : 'transparent'}`,
                borderLeft: `3px solid ${isSelected ? fc : 'transparent'}`,
                color: isSelected ? fc : '#a0a0a0',
              }}>
              <span className="truncate">{f.flow_name}</span>
            </button>
          )
        })}
      </div>

      {/* Flow detail */}
      {flow && (
        <div className="flex-1 rounded-lg border border-border bg-bg-card p-5 space-y-4 overflow-y-auto">
          {/* Header */}
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <div className="text-base font-semibold text-text-primary">{flow.flow_name}</div>
              {flow.category && (
                <span className="text-[10px] text-text-dim bg-bg-surface border border-border rounded px-1.5 py-0.5">{flow.category}</span>
              )}
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded"
                style={{ color, background: color + '18', border: `1px solid ${color}33` }}>
                {CWR_DISPLAY[flow.crawl_walk_run] || flow.crawl_walk_run}
              </span>
            </div>
            {flow.rationale && (
              <div className="text-sm text-text-muted leading-relaxed">{flow.rationale}</div>
            )}
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-4 gap-3">
            {flow.ai_score != null && (
              <div className="bg-bg rounded-lg border border-border p-3 text-center">
                <div className="text-lg font-bold" style={{ color }}>{flow.ai_score}</div>
                <div className="text-[10px] text-text-dim">AI Score</div>
              </div>
            )}
            {flow.contain_display && (
              <div className="bg-bg rounded-lg border border-border p-3 text-center">
                <div className="text-lg font-bold text-success">{flow.contain_display}</div>
                <div className="text-[10px] text-text-dim">Containment</div>
              </div>
            )}
            {flow.complexity && (
              <div className="bg-bg rounded-lg border border-border p-3 text-center">
                <div className="text-sm font-semibold text-text-secondary">{flow.complexity}</div>
                <div className="text-[10px] text-text-dim">Complexity</div>
              </div>
            )}
            {flow.human_role && (
              <div className="bg-bg rounded-lg border border-border p-3 text-center">
                <div className="text-sm font-semibold text-text-secondary">{flow.human_role}</div>
                <div className="text-[10px] text-text-dim">Human Role</div>
              </div>
            )}
          </div>

          {/* Human role detail */}
          {flow.human_detail && (
            <Field label="Agent Responsibility">
              <div className="text-xs text-text-muted leading-relaxed">{flow.human_detail}</div>
            </Field>
          )}

          {/* Intents */}
          {flow.intents?.length > 0 && (
            <Field label="Common Intents">
              <div className="flex flex-wrap gap-1.5">
                {flow.intents.map((intent: string) => <Tag key={intent} label={intent} />)}
              </div>
            </Field>
          )}

          {/* Channels, Data Sources, Output Actions */}
          <div className="grid grid-cols-3 gap-4">
            {flow.entry_channels?.length > 0 && (
              <Field label="Channels">
                <div className="flex flex-wrap gap-1.5">
                  {flow.entry_channels.map((ch: string) => (
                    <span key={ch} className="text-[10px] bg-bg-surface border border-border rounded px-1.5 py-0.5 text-text-muted">{ch}</span>
                  ))}
                </div>
              </Field>
            )}
            {flow.data_sources?.length > 0 && (
              <Field label="Data Sources">
                <div className="flex flex-wrap gap-1.5">
                  {flow.data_sources.map((ds: string) => (
                    <span key={ds} className="text-[10px] bg-bg-surface border border-border rounded px-1.5 py-0.5 text-text-muted">{ds}</span>
                  ))}
                </div>
              </Field>
            )}
            {flow.output_actions?.length > 0 && (
              <Field label="Output Actions">
                <div className="flex flex-wrap gap-1.5">
                  {flow.output_actions.map((a: string) => <Tag key={a} label={a} c="#fbbf24" />)}
                </div>
              </Field>
            )}
          </div>

          {/* Authentication */}
          {flow.authentication && (
            <Field label="Authentication">
              <div className="text-xs text-text-muted">{flow.authentication}</div>
            </Field>
          )}
        </div>
      )}
    </div>
  )
}

// ── Tab: Next Steps ───────────────────────────────────────────────

function TabNextSteps({ bp }: { bp: any }) {
  const steps = bp.next_steps || []
  if (!steps.length) {
    return <div className="text-sm text-text-muted py-8 text-center">No next steps generated.</div>
  }

  return (
    <div className="space-y-3">
      {steps.map((step: any, i: number) => (
        <div key={i} className="rounded-lg border border-border bg-bg-card p-4 flex gap-4">
          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-accent/15 border border-accent/30
                          flex items-center justify-center text-xs font-bold text-accent">
            {i + 1}
          </div>
          <div className="flex-1">
            {step.title && (
              <div className="text-sm font-semibold text-text-primary mb-1">{step.title}</div>
            )}
            <div className="text-xs text-text-muted leading-relaxed">
              {typeof step === 'string' ? step : step.body || step.description || JSON.stringify(step)}
            </div>
            {step.timeline && (
              <div className="text-[10px] text-accent mt-1.5">{step.timeline}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────

const TABS = [
  { id: 'summary',    label: 'Summary' },
  { id: 'roadmap',   label: 'Roadmap' },
  { id: 'flows',     label: 'Flow Designs' },
  { id: 'bc',        label: 'Business Case' },
  { id: 'risk',      label: 'Risk' },
  { id: 'vendors',   label: 'Vendors' },
  { id: 'nextsteps', label: 'Next Steps' },
]

export default function Phase4Page() {
  const { sessionId, blueprint, setBlueprint } = useSessionStore()

  const [running, setRunning]     = useState(false)
  const [error, setError]         = useState('')
  const [localData, setLocalData] = useState<any>(
    blueprint && Object.keys(blueprint).length > 0 ? blueprint : null
  )
  const [activeTab, setActiveTab] = useState('summary')
  const [pdfTheme, setPdfTheme]   = useState<'light' | 'dark'>('light')

  useEffect(() => {
    if (blueprint && Object.keys(blueprint).length > 0) {
      setLocalData(blueprint)
    }
  }, [blueprint])

  const generate = async () => {
    if (!sessionId) return
    setRunning(true)
    setError('')
    try {
      const result = await Blueprint.generate(sessionId)
      setBlueprint(result)
      setLocalData(result)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Blueprint generation failed — please try again.')
    } finally {
      setRunning(false)
    }
  }

  if (!localData) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center py-16 gap-6">
          <div className="text-center">
            <div className="text-lg font-semibold text-text-primary mb-2">
              Ready to generate the CX Blueprint
            </div>
            <div className="text-sm text-text-muted max-w-md">
              We'll synthesize everything — flows, assessment, risk, business case, and vendors —
              into a complete AI CX blueprint with executive summary, roadmap, and next steps.
            </div>
          </div>

          {error && (
            <div className="text-sm text-danger bg-danger/10 border border-danger/20
                            rounded-lg px-4 py-2">
              {error}
            </div>
          )}

          <button
            onClick={generate}
            disabled={running}
            className="flex items-center gap-2 bg-accent hover:bg-accent-hover
                       text-white font-semibold text-sm rounded-lg px-6 py-3
                       transition-all disabled:opacity-50"
          >
            {running
              ? <><Loader2 size={16} className="animate-spin" />Generating Blueprint...</>
              : <><FileText size={16} />Generate Blueprint</>
            }
          </button>

          {running && (
            <div className="text-xs text-text-dim animate-pulse">
              Synthesizing all session data — this takes about 20 seconds...
            </div>
          )}
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto pb-8">

        {/* Tab bar */}
        <div className="flex gap-1 mb-6 border-b border-border overflow-x-auto">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="px-4 py-2 text-xs font-semibold whitespace-nowrap transition-all
                         border-b-2 -mb-px"
              style={{
                color: activeTab === tab.id ? '#818cf8' : '#a0a0a0',
                borderBottomColor: activeTab === tab.id ? '#818cf8' : 'transparent',
              }}
            >
              {tab.label}
            </button>
          ))}
          <div className="flex-1" />
          {/* PDF download */}
          <div className="flex items-center gap-2 flex-shrink-0 py-1">
            <select
              value={pdfTheme}
              onChange={e => setPdfTheme(e.target.value as 'light' | 'dark')}
              className="text-[10px] text-text-dim bg-transparent border border-border
                         rounded px-1.5 py-1 focus:outline-none cursor-pointer"
            >
              <option value="light">Light PDF</option>
              <option value="dark">Dark PDF</option>
            </select>
            <button
              onClick={() => Blueprint.downloadPdf(sessionId!, pdfTheme)}
              className="flex items-center gap-1.5 text-[10px] font-semibold
                         text-accent border border-accent/30 bg-accent/5
                         rounded px-2.5 py-1.5 hover:bg-accent/10 transition-all"
            >
              <Download size={10} />
              Download PDF
            </button>
            <button
              onClick={generate}
              disabled={running}
              className="flex items-center gap-1 text-[10px] text-text-dim px-2 py-1.5
                         hover:text-text-muted transition-all disabled:opacity-50"
            >
              {running ? <Loader2 size={10} className="animate-spin" /> : '↺'}
              Regenerate
            </button>
          </div>
        </div>

        {/* Tab content */}
        {activeTab === 'summary'    && <TabSummary bp={localData} />}
        {activeTab === 'roadmap'    && <TabRoadmap bp={localData} />}
        {activeTab === 'flows'      && <TabFlowDesigns bp={localData} />}
        {activeTab === 'bc'         && <TabBusinessCase bp={localData} />}
        {activeTab === 'risk'       && <TabRisk bp={localData} />}
        {activeTab === 'vendors'    && <TabVendors bp={localData} />}
        {activeTab === 'nextsteps'  && <TabNextSteps bp={localData} />}

      </div>
    </AppShell>
  )
}