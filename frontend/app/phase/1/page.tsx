'use client'

import { useSessionStore } from '@/store/session'
import AppShell from '@/components/layout/AppShell'

function ProfileField({ label, value }: { label: string; value?: string | number }) {
  if (!value) return null
  return (
    <div className="flex flex-col gap-0.5">
      <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint">{label}</div>
      <div className="text-sm text-text-secondary">{value}</div>
    </div>
  )
}

function Tag({ label }: { label: string }) {
  return (
    <span className="text-[10px] bg-accent/8 border border-accent/20 text-accent
                     rounded px-1.5 py-0.5">
      {label}
    </span>
  )
}

export default function Phase1Page() {
  const { businessProfile, discovery, convAnswers } = useSessionStore()

  const bp       = businessProfile || {}
  const answers  = convAnswers || {}
  const flows    = (discovery || []).filter((f: any) => f.confirmed)

  const channels   = answers.channels || []
  const regions    = answers.regions || []
  const volume     = answers.volume || ''
  const automation = answers.automation || ''
  const crm        = answers.crm || bp.crm || ''
  const platform   = answers.cc_platform || bp.cc_platform || ''
  const goal       = answers.goal || ''
  const timeline   = answers.timeline || ''
  const painPoint  = answers.pain_point || ''

  const confidence = bp.confidence
  const confPct    = confidence ? Math.round(confidence * 100) : null

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto pt-4 pb-8 space-y-6">

        {/* Company header */}
        <div className="flex items-start gap-4">
          {bp.domain && (
            <img
              src={`https://www.google.com/s2/favicons?domain=${bp.domain}&sz=64`}
              width={40} height={40}
              className="rounded-lg flex-shrink-0 mt-1"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          )}
          <div>
            <div className="text-xl font-bold text-text-primary tracking-tight">
              {bp.company_name || 'Unknown Company'}
            </div>
            <div className="text-sm text-text-muted mt-0.5">
              {[bp.industry, bp.company_type, bp.domain].filter(Boolean).join(' · ')}
            </div>
            {confPct && (
              <div className="flex items-center gap-2 mt-2">
                <div className="h-1 w-32 bg-border rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${confPct}%`,
                      background: confPct >= 80 ? '#4ade80' : confPct >= 50 ? '#818cf8' : '#fbbf24',
                    }}
                  />
                </div>
                <span className="text-[10px] text-text-dim">{confPct}% profile confidence</span>
              </div>
            )}
          </div>
        </div>

        {/* Description */}
        {bp.description && (
          <div className="rounded-lg border border-border bg-bg-card px-4 py-3">
            <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-1.5">
              Company Overview
            </div>
            <div className="text-sm text-text-muted leading-relaxed">{bp.description}</div>
          </div>
        )}

        {/* Two-column grid */}
        <div className="grid grid-cols-2 gap-4">

          {/* Business context */}
          <div className="rounded-lg border border-border bg-bg-card p-4 space-y-3">
            <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint">
              Business Context
            </div>
            <ProfileField label="Industry"      value={bp.industry} />
            <ProfileField label="Size Estimate" value={bp.size_estimate} />
            <ProfileField label="Monthly Volume" value={volume} />
            <ProfileField label="Primary Pain Point" value={painPoint} />
            <ProfileField label="Primary Goal"  value={goal} />
            <ProfileField label="Timeline"      value={timeline} />
            <ProfileField label="AI Automation Today" value={automation} />
          </div>

          {/* Technology */}
          <div className="rounded-lg border border-border bg-bg-card p-4 space-y-3">
            <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint">
              Technology Stack
            </div>
            <ProfileField label="CRM"             value={crm} />
            <ProfileField label="Contact Center"  value={platform} />

            {channels.length > 0 && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-1.5">
                  Customer Channels
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(Array.isArray(channels) ? channels : [channels]).map((ch: string) => (
                    <Tag key={ch} label={ch} />
                  ))}
                </div>
              </div>
            )}

            {regions.length > 0 && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-1.5">
                  Regions Served
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(Array.isArray(regions) ? regions : [regions]).map((r: string) => (
                    <Tag key={r} label={r} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Confirmed flows */}
        {flows.length > 0 && (
          <div className="rounded-lg border border-border bg-bg-card p-4">
            <div className="text-[10px] font-bold uppercase tracking-wider text-text-faint mb-3">
              Confirmed Use Cases ({flows.length})
            </div>
            <div className="flex flex-wrap gap-2">
              {flows.map((f: any) => (
                <span key={f.flow_id}
                  className="text-xs text-text-secondary bg-bg border border-border
                             rounded-lg px-2.5 py-1.5">
                  {f.flow_name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Source + timestamp */}
        <div className="text-[10px] text-text-faint">
          {bp.source && <span>Source: {bp.source}</span>}
          {bp.inferred_at && (
            <span className="ml-3">
              Researched: {new Date(bp.inferred_at).toLocaleDateString()}
            </span>
          )}
        </div>

      </div>
    </AppShell>
  )
}