'use client'

import { useState, useEffect } from 'react'
import { useSessionStore } from '@/store/session'
import { BusinessCase } from '@/lib/api'
import AppShell from '@/components/layout/AppShell'
import { Loader2, DollarSign, RotateCcw } from 'lucide-react'

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

// ── Input field components ───────────────────────────────────────

interface NumberFieldProps {
  label: string
  value: number
  onChange: (v: number) => void
  min?: number
  max?: number
  step?: number
  prefix?: string
  suffix?: string
  help?: string
  star?: boolean
}

function NumberField({ label, value, onChange, min = 0, max, step = 1, prefix, suffix, help, star }: NumberFieldProps) {
  const [localVal, setLocalVal] = useState(String(value))

  useEffect(() => {
    setLocalVal(String(value))
  }, [value])

  return (
    <div className="mb-3">
      <label className="block text-xs text-text-muted mb-1">
        {label}{star && <span className="text-warning ml-1">⭐</span>}
      </label>
      <div className="flex items-center gap-1">
        {prefix && <span className="text-xs text-text-dim">{prefix}</span>}
        <input
          type="number"
          value={localVal}
          min={min}
          max={max}
          step={step}
          onFocus={e => e.target.select()}
          onChange={e => setLocalVal(e.target.value)}
          onBlur={e => {
            const parsed = parseFloat(e.target.value)
            const clamped = isNaN(parsed) ? (min ?? 0) : Math.max(min ?? 0, max != null ? Math.min(max, parsed) : parsed)
            setLocalVal(String(clamped))
            onChange(clamped)
          }}
          className="w-full bg-bg-surface border border-border rounded px-2 py-1.5
                     text-sm text-text-primary focus:outline-none focus:border-accent
                     transition-colors"
        />
        {suffix && <span className="text-xs text-text-dim">{suffix}</span>}
      </div>
      {help && <div className="text-[10px] text-text-faint mt-0.5 leading-tight">{help}</div>}
    </div>
  )
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div className="text-[10px] font-bold uppercase tracking-widest text-accent
                    mb-3 mt-1 pb-1 border-b border-border">
      {label}
    </div>
  )
}

// ── Input form ───────────────────────────────────────────────────

interface InputFormProps {
  prefill: Record<string, any>
  onCalculate: (inputs: Record<string, any>) => void
  calculating: boolean
}

function InputForm({ prefill, onCalculate, calculating }: InputFormProps) {
  const [f, setF] = useState({
    annual_contacts:            prefill.annual_contacts ?? 25000,
    voice_pct:                  (prefill.voice_pct ?? 0.60) * 100,
    chat_pct:                   (prefill.chat_pct ?? 0.40) * 100,
    current_automation_pct:     (prefill.current_automation_pct ?? 0.00) * 100,
    agent_count:                prefill.agent_count ?? 50,
    hourly_agent_cost:          prefill.hourly_agent_cost ?? 17.00,
    burden_rate:                (prefill.burden_rate ?? 0.18) * 100,
    churn_rate:                 (prefill.churn_rate ?? 0.32) * 100,
    ramp_days:                  prefill.ramp_days ?? 90,
    extended_ramp_days:         prefill.extended_ramp_days ?? 60,
    recruitment_cost:           prefill.recruitment_cost ?? 4000,
    wfm_fte_count:              prefill.wfm_fte_count ?? 2,
    qa_fte_count:               prefill.qa_fte_count ?? 1,
    ccaas_cost_per_agent_month: prefill.ccaas_cost_per_agent_month ?? 100,
    other_tech_annual:          prefill.other_tech_annual ?? 0,
    target_automation_pct:      (prefill.target_automation_pct ?? 0.40) * 100,
    proposed_churn_rate:        (prefill.proposed_churn_rate ?? 0.21) * 100,
    implementation_cost:        prefill.implementation_cost ?? 1000000,
    cost_per_automated_contact: prefill.cost_per_automated_contact ?? 0.50,
    proposed_ccaas_per_agent_month: prefill.proposed_ccaas_per_agent_month ?? 150,
    proposed_ramp_days:         prefill.proposed_ramp_days ?? 60,
  })

  const upd = (key: string) => (v: number) => setF(prev => ({ ...prev, [key]: v }))

  const handleCalculate = () => {
    onCalculate({
      annual_contacts:                Math.round(f.annual_contacts),
      voice_pct:                      f.voice_pct / 100,
      chat_pct:                       f.chat_pct / 100,
      email_pct:                      Math.max(0, 1 - f.voice_pct / 100 - f.chat_pct / 100),
      current_automation_pct:         f.current_automation_pct / 100,
      agent_count:                    Math.round(f.agent_count),
      hourly_agent_cost:              f.hourly_agent_cost,
      burden_rate:                    f.burden_rate / 100,
      churn_rate:                     f.churn_rate / 100,
      ramp_days:                      Math.round(f.ramp_days),
      extended_ramp_days:             Math.round(f.extended_ramp_days),
      recruitment_cost:               f.recruitment_cost,
      wfm_fte_count:                  Math.round(f.wfm_fte_count),
      wfm_fte_salary:                 prefill.wfm_fte_salary ?? 55000,
      qa_fte_count:                   Math.round(f.qa_fte_count),
      qa_fte_salary:                  prefill.qa_fte_salary ?? 55000,
      ccaas_cost_per_agent_month:     f.ccaas_cost_per_agent_month,
      other_tech_annual:              f.other_tech_annual,
      target_automation_pct:          f.target_automation_pct / 100,
      proposed_churn_rate:            f.proposed_churn_rate / 100,
      proposed_ramp_days:             Math.round(f.proposed_ramp_days),
      proposed_extended_ramp_days:    prefill.proposed_extended_ramp_days ?? 30,
      proposed_recruitment_cost:      prefill.proposed_recruitment_cost ?? 2000,
      proposed_wfm_fte_count:         Math.max(1, Math.round(f.wfm_fte_count) - 1),
      proposed_qa_fte_count:          Math.max(1, Math.round(f.qa_fte_count) - 1),
      cost_per_automated_contact:     f.cost_per_automated_contact,
      proposed_ccaas_per_agent_month: f.proposed_ccaas_per_agent_month,
      wfm_wfo_addon:                  prefill.wfm_wfo_addon ?? 40,
      auto_qa_addon:                  prefill.auto_qa_addon ?? 40,
      sim_training_addon:             prefill.sim_training_addon ?? 30,
      ai_agent_assist_addon:          prefill.ai_agent_assist_addon ?? 40,
      implementation_cost:            f.implementation_cost,
      analysis_years:                 5,
    })
  }

  return (
    <div>
      <div className="text-sm text-text-muted mb-6">
        Pre-filled from your discovery conversation. Adjust any values that don't
        match your client's situation, then click Calculate.
      </div>

      {/* Contact Volume */}
      <SectionHeader label="Contact Volume" />
      <div className="grid grid-cols-2 gap-x-6">
        <NumberField label="Total Annual Contacts" value={f.annual_contacts}
          onChange={upd('annual_contacts')} min={0} max={10000000} step={1000}
          help="Total contacts across all channels per year." />
        <NumberField label="Current Self-Service %" value={f.current_automation_pct}
          onChange={upd('current_automation_pct')} min={0} max={80} step={5} suffix="%"
          help="Contacts currently resolved without a live agent." />
        <NumberField label="Voice Contact %" value={f.voice_pct}
          onChange={upd('voice_pct')} min={0} max={100} step={5} suffix="%"
          help="Percentage handled via phone. Typically most expensive." />
        <NumberField label="Chat / Digital %" value={f.chat_pct}
          onChange={upd('chat_pct')} min={0} max={100} step={5} suffix="%"
          help="Live chat, email, or other digital channels." />
      </div>

      <div className="h-px bg-border my-4" />

      {/* Current Staffing */}
      <SectionHeader label="Current Staffing & Costs" />
      <div className="grid grid-cols-3 gap-x-6">
        <NumberField label="Agent Headcount" value={f.agent_count}
          onChange={upd('agent_count')} min={1} max={10000} step={1} star
          help="Total agents today (in-house + BPO). Most important input." />
        <NumberField label="Annual Agent Churn %" value={f.churn_rate}
          onChange={upd('churn_rate')} min={0} max={100} step={1} suffix="%"
          help="Industry avg: 30–45%. Biggest hidden cost driver." />
        <NumberField label="Recruitment Cost per Agent ($)" value={f.recruitment_cost}
          onChange={upd('recruitment_cost')} min={0} max={50000} step={500} prefix="$"
          help="Fully loaded cost to recruit + train one replacement. Range: $3K–$8K." />
        <NumberField label="Hourly Agent Cost ($)" value={f.hourly_agent_cost}
          onChange={upd('hourly_agent_cost')} min={8} max={150} step={1} prefix="$"
          help="Before burden rate. US onshore: $15–22/hr. Offshore: $8–14/hr." />
        <NumberField label="Agent Ramp Time (Days)" value={f.ramp_days}
          onChange={upd('ramp_days')} min={0} max={365} step={5}
          help="Days in training before handling live contacts." />
        <NumberField label="Extended Ramp (Days)" value={f.extended_ramp_days}
          onChange={upd('extended_ramp_days')} min={0} max={365} step={5}
          help="Additional days at ~50% proficiency after initial training." />
        <NumberField label="Burden Rate %" value={f.burden_rate}
          onChange={upd('burden_rate')} min={0} max={50} step={1} suffix="%"
          help="Employer overhead: payroll taxes, benefits, PTO. Typically 15–25%." />
        <NumberField label="WFM / Analyst Headcount" value={f.wfm_fte_count}
          onChange={upd('wfm_fte_count')} min={0} max={50} step={1}
          help="Workforce Management or operations analyst FTEs." />
        <NumberField label="QA / QM Headcount" value={f.qa_fte_count}
          onChange={upd('qa_fte_count')} min={0} max={50} step={1}
          help="Quality Assurance or Quality Management FTEs." />
      </div>

      <div className="h-px bg-border my-4" />

      {/* Current Technology */}
      <SectionHeader label="Current Technology" />
      <div className="grid grid-cols-2 gap-x-6">
        <NumberField label="CCaaS Cost per Agent / Month ($)" value={f.ccaas_cost_per_agent_month}
          onChange={upd('ccaas_cost_per_agent_month')} min={0} max={500} step={10} prefix="$"
          help="Monthly per-seat cost. Enterprise (Genesys, NICE): $120–200. Mid-market: $90–130." />
        <NumberField label="Other Annual Tech Costs ($)" value={f.other_tech_annual}
          onChange={upd('other_tech_annual')} min={0} max={10000000} step={10000} prefix="$"
          help="Additional annual technology costs not in CCaaS licensing." />
      </div>

      <div className="h-px bg-border my-4" />

      {/* Proposed State */}
      <SectionHeader label="Proposed State (Post AI Implementation)" />
      <div className="grid grid-cols-3 gap-x-6">
        <NumberField label="Target Automation % (Self-Service)" value={f.target_automation_pct}
          onChange={upd('target_automation_pct')} min={0} max={80} step={5} suffix="%"
          help="Weighted containment target across confirmed flows. Adjust if client situation differs." />
        <NumberField label="Implementation Cost ($)" value={f.implementation_cost}
          onChange={upd('implementation_cost')} min={0} max={50000000} step={50000} prefix="$"
          help="Professional services, integration, training, change management. Range: $500K–$3M." />
        <NumberField label="New CCaaS Cost per Agent / Month ($)" value={f.proposed_ccaas_per_agent_month}
          onChange={upd('proposed_ccaas_per_agent_month')} min={0} max={500} step={10} prefix="$"
          help="Post-implementation CCaaS cost. Often higher due to AI features, offset by reduced headcount." />
        <NumberField label="Expected Churn Rate Post-AI %" value={f.proposed_churn_rate}
          onChange={upd('proposed_churn_rate')} min={0} max={100} step={1} suffix="%"
          help="Agent churn typically drops 8–15 points after AI deployment." />
        <NumberField label="Cost per Automated Contact ($)" value={f.cost_per_automated_contact}
          onChange={upd('cost_per_automated_contact')} min={0} max={10} step={0.05} prefix="$"
          help="Variable cost per AI-handled contact. Platform, API, compute. Range: $0.25–$1.00." />
        <NumberField label="Ramp Time Post-AI (Days)" value={f.proposed_ramp_days}
          onChange={upd('proposed_ramp_days')} min={0} max={365} step={5}
          help="Ramp time typically drops 30–40% with AI-assisted training." />
      </div>

      <div className="h-px bg-border my-6" />

      <button
        onClick={handleCalculate}
        disabled={calculating || f.agent_count < 1}
        className="flex items-center gap-2 bg-accent hover:bg-accent-hover
                   text-white font-semibold text-sm rounded-lg px-6 py-3
                   transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {calculating
          ? <><Loader2 size={16} className="animate-spin" />Calculating...</>
          : <><DollarSign size={16} />Calculate Business Case →</>
        }
      </button>
    </div>
  )
}

// ── Results view ─────────────────────────────────────────────────

function Results({ data, onReset }: { data: any; onReset: () => void }) {
  const summary  = data?.summary || {}
  const base     = data?.base || {}
  const current  = base?.current || {}
  const proposed = base?.proposed || {}
  const drivers  = base?.savings_by_driver || {}

  const churnSavings = summary.churn_savings || 0
  const laborSavings = summary.labor_savings || 0

  const driverColors: Record<string, string> = {
    'Labor reduction':    '#818cf8',
    'Churn reduction':    '#4ade80',
    'Overhead reduction': '#fbbf24',
    'Tech delta':         '#52525b',
  }

  const maxDriver = Math.max(...Object.values(drivers as Record<string, number>).map(Math.abs), 1)

  return (
    <div className="space-y-6 pb-8">

      {/* Churn insight banner */}
      {churnSavings > laborSavings && churnSavings > 0 && (
        <div className="rounded-lg border border-success/20 bg-success/5 px-4 py-3">
          <div className="text-xs font-semibold text-success mb-1">
            ⚡ Biggest Savings Opportunity: Churn Reduction
          </div>
          <div className="text-sm text-text-muted leading-relaxed">
            {fmt(churnSavings)} in annual churn savings —&nbsp;
            {(churnSavings / Math.max(laborSavings, 1)).toFixed(1)}x more than
            direct labor reduction. Most clients have never modeled this cost.
          </div>
        </div>
      )}

      {/* Environment comparison */}
      <div>
        <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
          Environment Comparison (Base Case)
        </div>
        <div className="grid grid-cols-2 gap-4">
          {[
            { title: 'Current',  env: current,  color: '#52525b', impl: 0 },
            { title: 'Proposed', env: proposed, color: '#818cf8', impl: base?.impl_cost || 0 },
          ].map(({ title, env, color, impl }) => (
            <div key={title} className="rounded-lg p-4"
              style={{
                borderTop:    `2px solid ${color}`,
                borderRight:  `1px solid ${color}33`,
                borderBottom: `1px solid ${color}33`,
                borderLeft:   `1px solid ${color}33`,
                background: '#0f0f0f',
                borderRadius: 8,
              }}>
              <div className="text-[10px] font-bold uppercase tracking-wider mb-3"
                style={{ color }}>{title} Environment</div>
              {([
                ['Agents',       String(env.agent_count || '—'),                '#c0c0c0'],
                ['Self-Service', `${(env.self_service || 0).toLocaleString()}`, '#c0c0c0'],
                ['Labor Cost',   fmt(env.labor_cost),                           '#c0c0c0'],
                ['Churn Cost',   fmt(env.churn_cost),                           '#fbbf24'],
                ['Tech Stack',   fmt(env.tech_cost),                            '#c0c0c0'],
                ['WFM / QA',     fmt(env.overhead_cost),                        '#c0c0c0'],
                ...(impl ? [['Implementation', fmt(impl), '#71717a']] : []),
              ] as [string,string,string][]).map(([lbl, val, vc]) => (
                <div key={lbl} className="flex justify-between mb-1.5">
                  <span className="text-[11px] text-text-dim">{lbl}</span>
                  <span className="text-xs font-medium" style={{ color: vc as string }}>{val}</span>
                </div>
              ))}
              <div className="h-px bg-border my-2" />
              <div className="flex justify-between">
                <span className="text-[11px] text-text-dim">Total CX Cost</span>
                <span className="text-sm font-bold" style={{ color }}>{fmt(env.total_cost)}</span>
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[11px] text-text-dim">Cost / Contact</span>
                <span className="text-xs text-text-secondary">{fmt(env.cost_per_contact, 2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Three scenarios */}
      <div>
        <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
          ROI Scenarios
        </div>
        <div className="grid grid-cols-3 gap-4">
          {(['conservative', 'base', 'optimistic'] as const).map(scenarioKey => {
            const s = data[scenarioKey] || {}
            const nc = (s.annual_savings || 0) >= 0 ? '#4ade80' : '#f87171'
            const sc = s.scenario_color || '#818cf8'
            return (
              <div key={scenarioKey} className="rounded-lg p-4"
                style={{
                  borderTop:    `2px solid ${sc}`,
                  borderRight:  `1px solid ${sc}33`,
                  borderBottom: `1px solid ${sc}33`,
                  borderLeft:   `1px solid ${sc}33`,
                  background: '#0f0f0f',
                  borderRadius: 8,
                }}>
                <div className="text-[10px] font-bold uppercase tracking-wider mb-1"
                  style={{ color: s.scenario_color }}>{s.scenario_label}</div>
                <div className="text-[10px] text-text-faint mb-3 leading-tight">
                  {s.scenario_desc}
                </div>
                <div className="text-xl font-bold mb-0.5" style={{ color: nc }}>
                  {fmt(s.annual_savings)}
                </div>
                <div className="text-[10px] text-text-dim mb-3">Annual Savings</div>
                <div className="text-sm font-semibold text-text-secondary mb-0.5">
                  {fmtMonths(s.payback_months)}
                </div>
                <div className="text-[10px] text-text-dim mb-3">Payback Period</div>
                <div className="h-px bg-border mb-3" />
                <div className="flex justify-between mb-1">
                  <span className="text-[10px] text-text-dim">3-Year NPV</span>
                  <span className="text-xs font-semibold text-text-secondary">
                    {fmt(s.npv?.[3])}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[10px] text-text-dim">5-Year NPV</span>
                  <span className="text-xs font-semibold text-text-secondary">
                    {fmt(s.npv?.[5])}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Savings by driver */}
      <div>
        <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
          Savings by Driver (Base Case)
        </div>
        <div className="space-y-3">
          {Object.entries(drivers as Record<string, number>)
            .sort(([,a], [,b]) => b - a)
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
                    <div className="h-full rounded-full transition-all"
                      style={{ width: `${barPct}%`, background: color }} />
                  </div>
                </div>
              )
            })}
        </div>
      </div>

      {/* Adjust inputs */}
      <button onClick={onReset}
        className="flex items-center gap-2 text-xs text-text-dim border border-border
                   rounded-lg px-3 py-2 hover:text-text-muted hover:border-border-strong
                   transition-all">
        <RotateCcw size={12} />
        Adjust Inputs
      </button>

    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────

export default function Phase3bPage() {
  const { sessionId, businessCase, setBusinessCase } = useSessionStore()

  const [calculating, setCalculating] = useState(false)
  const [error, setError]             = useState('')
  const [prefill, setPrefill]         = useState<any>(null)
  const [results, setResults]         = useState<any>(businessCase && Object.keys(businessCase).length > 0 ? businessCase : null)

  useEffect(() => {
    if (!sessionId) return
    // Load prefill from API
    BusinessCase.getPrefill(sessionId).then(p => setPrefill(p)).catch(() => {})
  }, [sessionId])

  useEffect(() => {
    if (businessCase && Object.keys(businessCase).length > 0) {
      setResults(businessCase)
    }
  }, [businessCase])

  const handleCalculate = async (inputs: Record<string, any>) => {
    if (!sessionId) return
    setCalculating(true)
    setError('')
    try {
      const result = await BusinessCase.run(sessionId, inputs)
      setBusinessCase(result)
      setResults(result)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Calculation failed — please try again.')
    } finally {
      setCalculating(false)
    }
  }

  const handleReset = () => {
    setResults(null)
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto pt-4">
        {error && (
          <div className="text-sm text-danger bg-danger/10 border border-danger/20
                          rounded-lg px-4 py-2 mb-4">
            {error}
          </div>
        )}

        {results ? (
          <Results data={results} onReset={handleReset} />
        ) : prefill ? (
          <InputForm prefill={prefill} onCalculate={handleCalculate} calculating={calculating} />
        ) : (
          <div className="flex items-center justify-center h-32">
            <Loader2 size={20} className="animate-spin text-accent" />
          </div>
        )}
      </div>
    </AppShell>
  )
}