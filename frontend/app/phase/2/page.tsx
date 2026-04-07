'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useSessionStore } from '@/store/session'
import { Conversation, type ConversationState, type ConversationStep, type ConversationMessage, type FlowData } from '@/lib/api'
import AppShell from '@/components/layout/AppShell'
import { Loader2, X, Check } from 'lucide-react'

// ── Color constants (matching Streamlit version) ──────────────

const COLORS = {
  bg:            '#0d0d0d',
  surface:       '#1e1e1e',
  surface2:      '#252525',
  border:        '#2a2a2a',
  border2:       '#383838',
  textPrimary:   '#ffffff',
  textSec:       '#e8e8e8',
  textMuted:     '#c0c0c0',
  textDim:       '#a0a0a0',
  accent:        '#818cf8',
  green:         '#4ade80',
  amber:         '#fbbf24',
  platformBg:    '#1a1a35',
  platformBorder:'#818cf8',
}

const HR_COLORS: Record<string, string> = {
  'None':          '#4ade80',
  'Escalation':    '#818cf8',
  'In-Loop':       '#fbbf24',
  'Post-Review':   '#a78bfa',
  'Collaborative': '#fbbf24',
}

const COMPLEXITY_COLORS: Record<string, string> = {
  'Low':    '#4ade80',
  'Medium': '#fbbf24',
  'High':   '#f87171',
}

const CHANNEL_ICONS: Record<string, string> = {
  'Phone': '📞', 'Web': '🌐', 'Chat': '💬', 'SMS': '📱',
  'Email': '✉', 'Mobile App': '📲', 'IVR': '📟',
  'Web / Self-service': '🌐', 'Live Chat': '💬',
}

const HUMAN_ICONS: Record<string, string> = {
  'None':          '✓',
  'Escalation':    '↗',
  'In-Loop':       '👤',
  'Post-Review':   '◎',
  'Collaborative': '🤝',
}

// ── Arrow helper ──────────────────────────────────────────────

function arrow(x1: number, y1: number, x2: number, y2: number, color: string, opacity = 0.7) {
  const ah = 7
  const angle = Math.atan2(y2 - y1, x2 - x1)
  const ax1 = x2 - ah * Math.cos(angle - 0.4)
  const ay1 = y2 - ah * Math.sin(angle - 0.4)
  const ax2 = x2 - ah * Math.cos(angle + 0.4)
  const ay2 = y2 - ah * Math.sin(angle + 0.4)
  return (
    <g key={`arrow-${x1}-${y1}-${x2}-${y2}`}>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={1.5} opacity={opacity} />
      <polygon
        points={`${x2.toFixed(1)},${y2.toFixed(1)} ${ax1.toFixed(1)},${ay1.toFixed(1)} ${ax2.toFixed(1)},${ay2.toFixed(1)}`}
        fill={color} opacity={opacity}
      />
    </g>
  )
}

// ── Platform Diagram ──────────────────────────────────────────

interface DiagramProps {
  flows: FlowData[]
  channels: string[]
  companyName: string
  selectedFlowId: string
  onSelectFlow: (id: string) => void
}

function PlatformDiagram({ flows, channels, companyName, selectedFlowId, onSelectFlow }: DiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [WIDTH, setWidth] = useState(680)
  const [hoveredFlow, setHoveredFlow] = useState('')

  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        const w = Math.floor(e.contentRect.width)
        if (w > 200) setWidth(w)
      }
    })
    ro.observe(containerRef.current)
    setWidth(Math.floor(containerRef.current.offsetWidth) || 680)
    return () => ro.disconnect()
  }, [])

  const TOP_PAD = 28
  const ROW_H   = 52
  const DS_H    = 56
  const LEG_H   = 28
  const BOT_PAD = 8
  const SECTION_PAD = 12

  const confirmedFlows = flows.filter(f => f.confirmed === true || (f as any).confirmed === 'true')
  const displayChannels = channels.length > 0 ? channels : ['Phone', 'Web', 'Chat', 'SMS']

  const allDS = Array.from(new Set(confirmedFlows.flatMap(f => (f as any).data_sources || [])))
  const dataSources = allDS.length > 0 ? allDS : ['CRM', 'Knowledge Base', 'Billing System', 'Auth System']

  const nCh   = Math.max(displayChannels.length, 1)
  const nUc   = Math.max(confirmedFlows.length, 1)
  const nRows = Math.max(nCh, nUc)
  const contentH = nRows * ROW_H
  const totalH   = TOP_PAD + contentH + SECTION_PAD + DS_H + LEG_H + BOT_PAD

  // Column X positions
  const xCh  = Math.round(WIDTH * 0.03)
  const xPlt = Math.round(WIDTH * 0.30)
  const xUc  = Math.round(WIDTH * 0.52)
  const xOut = Math.round(WIDTH * 0.90)

  // Node sizes
  const chW = 100, chH = 34
  const ucW = 168, ucH = 44
  const pltW = 110, pltH = 88
  const outW = 76, outH = 32

  const pltY  = TOP_PAD + (contentH - pltH) / 2
  const pltCX = xPlt
  const pltCY = pltY + pltH / 2

  // AI score from flows
  const aiScore = confirmedFlows.length > 0
    ? Math.round(confirmedFlows.reduce((s, f) => s + ((f as any).ai_score || 0), 0) / confirmedFlows.length)
    : 0
  const scoreColor = aiScore >= 70 ? COLORS.green : aiScore >= 40 ? COLORS.accent : COLORS.amber
  const scoreLabel = aiScore >= 70 ? 'AI Ready' : aiScore >= 40 ? 'Developing' : 'Early Stage'

  // Channel positions
  const chSpacing = contentH / nCh
  const chPositions = displayChannels.map((ch, i) => ({
    ch, cx: xCh + chW / 2,
    cy: TOP_PAD + chSpacing * i + chSpacing / 2,
  }))

  // Use case positions
  const ucSpacing = contentH / nUc
  const ucPositions = confirmedFlows.map((flow, i) => ({
    flow, lx: xUc,
    cy: TOP_PAD + ucSpacing * i + ucSpacing / 2,
  }))

  // Outcome counts
  const cwrCounts: Record<string, number> = {}
  confirmedFlows.forEach(f => {
    const cwr = (f as any).cwr || 'Crawl'
    cwrCounts[cwr] = (cwrCounts[cwr] || 0) + 1
  })
  const outcomes = [
    { cwr: 'Run',   label: '✓ AI Automated', color: COLORS.green },
    { cwr: 'Walk',  label: '⚡ AI Assisted',  color: COLORS.amber },
    { cwr: 'Crawl', label: '🔧 Stay Manual',  color: '#9ca3af' },
  ].filter(o => cwrCounts[o.cwr])

  const outSpacing = contentH / Math.max(outcomes.length, 1)
  const outPositions = outcomes.map((o, i) => ({
    ...o, ocx: xOut,
    ocy: TOP_PAD + outSpacing * i + outSpacing / 2,
  }))
  const outMap: Record<string, { ocx: number; ocy: number }> = {}
  outPositions.forEach(o => { outMap[o.cwr] = { ocx: o.ocx, ocy: o.ocy } })

  const font = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

  return (
    <div ref={containerRef} style={{ width: '100%', overflow: 'hidden' }}>
      <svg
        viewBox={`0 0 ${WIDTH} ${totalH}`}
        width={WIDTH} height={totalH}
        style={{ background: COLORS.bg, borderRadius: 12, display: 'block', width: '100%', height: 'auto' }}
      >
        {/* Column labels */}
        {[
          [xCh + chW / 2, 'Channels'],
          [xPlt, 'AI Platform'],
          [xUc + ucW / 2, 'Use Cases'],
          [xOut, 'Outcomes'],
        ].map(([lx, label]) => (
          <text key={String(label)} x={Number(lx)} y={18} fontSize={9}
            fill={COLORS.textDim} fontWeight="700" textAnchor="middle" fontFamily={font}>
            {String(label)}
          </text>
        ))}

        {/* Channel nodes */}
        {chPositions.map(({ ch, cx, cy }) => (
          <g key={ch}>
            <rect x={xCh} y={cy - chH / 2} width={chW} height={chH} rx={6}
              fill={COLORS.surface} stroke={COLORS.border2} strokeWidth={1} />
            <text x={xCh + 12} y={cy + 1} fontSize={13} fill={COLORS.textSec}
              textAnchor="start" fontFamily={font}>{CHANNEL_ICONS[ch] || '◆'}</text>
            <text x={xCh + 27} y={cy + 4} fontSize={10} fill={COLORS.textPrimary}
              fontWeight="500" textAnchor="start" fontFamily={font}>{ch}</text>
          </g>
        ))}

        {/* Channel → Platform arrows */}
        {chPositions.map(({ ch, cy }) =>
          arrow(xCh + chW, cy, xPlt - pltW / 2, pltCY, '#606060', 0.8)
        )}

        {/* Platform node */}
        <rect x={xPlt - pltW / 2} y={pltY} width={pltW} height={pltH} rx={10}
          fill={COLORS.platformBg} stroke={COLORS.platformBorder} strokeWidth={2} />
        <text x={pltCX} y={pltY + 16} fontSize={9} fill={COLORS.textMuted}
          fontWeight="500" textAnchor="middle" fontFamily={font}>
          {companyName.length > 14 ? companyName.slice(0, 13) + '…' : companyName}
        </text>
        <line x1={xPlt - pltW / 2 + 8} y1={pltY + 22}
          x2={xPlt + pltW / 2 - 8} y2={pltY + 22}
          stroke={COLORS.platformBorder} strokeWidth={0.5} opacity={0.4} />
        {aiScore > 0 ? (
          <>
            <text x={pltCX} y={pltY + 52} fontSize={26} fill={scoreColor}
              fontWeight="700" textAnchor="middle" fontFamily={font}>{aiScore}</text>
            <text x={pltCX} y={pltY + 66} fontSize={9} fill={scoreColor}
              fontWeight="500" textAnchor="middle" fontFamily={font}>{scoreLabel}</text>
            <text x={pltCX} y={pltY + pltH - 8} fontSize={8} fill={COLORS.textDim}
              textAnchor="middle" fontFamily={font}>Agentic AI Platform</text>
          </>
        ) : (
          <>
            <text x={pltCX} y={pltY + 50} fontSize={12} fill={COLORS.textSec}
              fontWeight="700" textAnchor="middle" fontFamily={font}>Agentic AI</text>
            <text x={pltCX} y={pltY + 65} fontSize={12} fill={COLORS.textSec}
              fontWeight="700" textAnchor="middle" fontFamily={font}>Platform</text>
          </>
        )}

        {/* Platform → Use case arrows */}
        {ucPositions.map(({ flow, lx, cy }) =>
          arrow(xPlt + pltW / 2, pltCY, lx, cy, '#606060', 0.7)
        )}

        {/* Empty state inside platform */}
        {confirmedFlows.length === 0 && (
          <text x={xUc + ucW / 2} y={TOP_PAD + contentH / 2}
            textAnchor="middle" fill={COLORS.textDim} fontSize={10} fontFamily={font}>
            Complete the conversation to see flows
          </text>
        )}

        {/* Use case nodes */}
        {ucPositions.map(({ flow, lx, cy }) => {
          const isSelected = flow.flow_id === selectedFlowId
          const isHovered  = flow.flow_id === hoveredFlow
          const cwrColor   = (flow as any).cwr_color || COLORS.accent
          const hrColor    = HR_COLORS[(flow as any).human_role] || COLORS.accent
          const illuminated = (flow as any).ai_score > 0 || (flow as any).cwr !== 'Crawl'
          const nodeOpacity = illuminated ? 1 : 0.5
          const showGlow    = isSelected || isHovered
          const borderColor = (isSelected || isHovered) ? cwrColor : COLORS.border2
          const fillColor   = isSelected ? COLORS.surface2 : isHovered ? '#202020' : COLORS.surface
          const sw          = (isSelected || isHovered) ? 2 : 1

          return (
            <g key={flow.flow_id}
              style={{ cursor: 'pointer', opacity: nodeOpacity }}
              onClick={() => onSelectFlow(flow.flow_id)}
              onMouseEnter={() => setHoveredFlow(flow.flow_id)}
              onMouseLeave={() => setHoveredFlow('')}>
              {showGlow && (
                <rect x={lx - 3} y={cy - ucH / 2 - 3} width={ucW + 6} height={ucH + 6}
                  rx={9} fill={cwrColor} opacity={isSelected ? 0.12 : 0.07} />
              )}
              <rect x={lx} y={cy - ucH / 2} width={ucW} height={ucH} rx={6}
                fill={fillColor} stroke={borderColor} strokeWidth={sw} />
              <rect x={lx} y={cy - ucH / 2} width={4} height={ucH} rx={1} fill={cwrColor} />
              <text x={lx + 10} y={cy - 5} fontSize={10} fill={COLORS.textPrimary}
                fontWeight="600" textAnchor="start" fontFamily={font}>
                {flow.flow_name.length > 21 ? flow.flow_name.slice(0, 19) + '…' : flow.flow_name}
              </text>
              <text x={lx + 10} y={cy + 10} fontSize={9}
                fill={isSelected ? cwrColor : '#9ca3af'}
                fontWeight="700" textAnchor="start" fontFamily={font}>
                {(flow as any).contain_display || ''}
              </text>
              {/* Human role badge */}
              <rect x={lx + ucW - 22} y={cy - 8} width={18} height={18} rx={4}
                fill={hrColor} opacity={0.15} />
              <text x={lx + ucW - 13} y={cy + 5} fontSize={9}
                fill={hrColor} textAnchor="middle" fontFamily={font}>
                {HUMAN_ICONS[(flow as any).human_role] || '↗'}
              </text>
            </g>
          )
        })}

        {/* Use case → Outcome arrows */}
        {ucPositions.map(({ flow, lx, cy }) => {
          const cwr = (flow as any).cwr || 'Crawl'
          const out = outMap[cwr]
          const cwrColor = (flow as any).cwr_color || COLORS.accent
          if (!out) return null
          return arrow(lx + ucW, cy, xOut - outW / 2, out.ocy, cwrColor, 0.5)
        })}

        {/* Outcome nodes */}
        {outPositions.map(({ cwr, label, color, ocx, ocy }) => (
          <g key={cwr}>
            <rect x={ocx - outW / 2} y={ocy - outH / 2} width={outW} height={outH} rx={6}
              fill={COLORS.surface2} stroke={color} strokeWidth={1.5} />
            <text x={ocx} y={ocy - 4} fontSize={10} fill={color}
              fontWeight="700" textAnchor="middle" fontFamily={font}>{label}</text>
            <text x={ocx} y={ocy + 9} fontSize={9} fill={COLORS.textSec}
              textAnchor="middle" fontFamily={font}>
              {cwrCounts[cwr]} flow{cwrCounts[cwr] !== 1 ? 's' : ''}
            </text>
          </g>
        ))}

        {/* Data sources strip */}
        {(() => {
          const dsY = TOP_PAD + contentH + SECTION_PAD
          let dsX = 108
          return (
            <g>
              <rect x={6} y={dsY} width={WIDTH - 12} height={DS_H - 8} rx={8}
                fill="#181818" stroke={COLORS.border2} strokeWidth={1} />
              <text x={18} y={dsY + 14} fontSize={9} fill={COLORS.textSec}
                fontWeight="700" textAnchor="start" fontFamily={font}>Data Sources:</text>
              {/* Dotted line from platform down */}
              <line x1={pltCX} y1={pltY + pltH} x2={pltCX} y2={dsY}
                stroke={COLORS.platformBorder} strokeWidth={1} strokeDasharray="4 3" opacity={0.4} />
              {dataSources.map((ds, i) => {
                const chipW = ds.length * 6.5 + 16
                if (dsX + chipW > WIDTH - 12) return null
                const el = (
                  <g key={ds}>
                    <rect x={dsX} y={dsY + 6} width={chipW} height={22} rx={4}
                      fill={COLORS.surface} stroke={COLORS.border2} strokeWidth={1} />
                    <text x={dsX + chipW / 2} y={dsY + 21} fontSize={9}
                      fill={COLORS.textPrimary} textAnchor="middle" fontFamily={font}>{ds}</text>
                  </g>
                )
                dsX += chipW + 5
                return el
              })}
            </g>
          )
        })()}

        {/* Hover tooltip */}
        {hoveredFlow && !selectedFlowId && (() => {
          const hf = confirmedFlows.find(f => f.flow_id === hoveredFlow)
          const hp = ucPositions.find(p => p.flow.flow_id === hoveredFlow)
          if (!hf || !hp) return null
          const tx = hp.lx + ucW + 8
          const ty = hp.cy - 28
          const tw = 140, th = 56
          const txC = Math.min(tx, WIDTH - tw - 4)
          const cwrColor = (hf as any).cwr_color || COLORS.accent
          return (
            <g style={{ pointerEvents: 'none' }}>
              <rect x={txC} y={ty} width={tw} height={th} rx={6}
                fill="#1a1a1a" stroke={cwrColor} strokeWidth={1} opacity={0.97} />
              <text x={txC + 8} y={ty + 14} fontSize={10} fill="#ffffff"
                fontWeight="600" fontFamily={font}>
                {hf.flow_name.length > 18 ? hf.flow_name.slice(0, 16) + '…' : hf.flow_name}
              </text>
              <text x={txC + 8} y={ty + 27} fontSize={9} fill={cwrColor} fontFamily={font}>
                {(hf as any).cwr_label} · {(hf as any).contain_display}
              </text>
              <text x={txC + 8} y={ty + 40} fontSize={9} fill={COLORS.textDim} fontFamily={font}>
                {(hf as any).human_role}
              </text>
            </g>
          )
        })()}

        {/* Legend */}
        {(() => {
          const legY = TOP_PAD + contentH + SECTION_PAD + DS_H
          return (
            <g>
              {[
                { label: 'AI Automated', color: COLORS.green, x: 14 },
                { label: 'AI Assisted',  color: COLORS.amber, x: 140 },
                { label: 'Stay Manual',  color: '#9ca3af',    x: 258 },
              ].map(({ label, color, x }) => (
                <g key={label}>
                  <rect x={x} y={legY} width={9} height={9} rx={2} fill={color} />
                  <text x={x + 13} y={legY + 9} fontSize={9} fill={COLORS.textSec} fontFamily={font}>
                    {label}
                  </text>
                </g>
              ))}
            </g>
          )
        })()}

      </svg>
    </div>
  )
}

// ── Detail Panel ──────────────────────────────────────────────

function DetailPanel({ flow, onClose }: { flow: FlowData; onClose: () => void }) {
  const f = flow as any
  return (
    <div style={{
      background: COLORS.surface,
      borderLeft: `1px solid ${COLORS.border2}`,
      width: 280,
      flexShrink: 0,
      overflowY: 'auto',
      padding: '16px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.textPrimary, lineHeight: 1.3 }}>
          {flow.flow_name}
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: COLORS.textDim, padding: 2 }}>
          <X size={14} />
        </button>
      </div>

      {/* CWR badge */}
      {f.cwr_label && (
        <div style={{
          display: 'inline-block',
          background: f.cwr_color + '22',
          border: `1px solid ${f.cwr_color}44`,
          borderRadius: 4,
          padding: '2px 8px',
          fontSize: 10,
          fontWeight: 700,
          color: f.cwr_color,
          marginBottom: 12,
          letterSpacing: '0.06em',
        }}>
          {f.cwr_label}
        </div>
      )}

      {f.rationale && (
        <div style={{ fontSize: 11, color: COLORS.textMuted, lineHeight: 1.6, marginBottom: 12 }}>
          {f.rationale}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>

        {f.human_role && (
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, color: COLORS.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 3 }}>Human Role</div>
            <div style={{ fontSize: 11, color: HR_COLORS[f.human_role] || COLORS.textSec }}>{f.human_role}</div>
            {f.human_detail && <div style={{ fontSize: 10, color: COLORS.textDim, marginTop: 2 }}>{f.human_detail}</div>}
          </div>
        )}

        {f.complexity && (
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, color: COLORS.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 3 }}>Complexity</div>
            <div style={{ fontSize: 11, color: COMPLEXITY_COLORS[f.complexity] || COLORS.textSec }}>{f.complexity}</div>
          </div>
        )}

        {f.entry_channels?.length > 0 && (
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, color: COLORS.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Channels</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {f.entry_channels.map((ch: string) => (
                <span key={ch} style={{ background: COLORS.surface2, border: `1px solid ${COLORS.border}`, borderRadius: 3, padding: '1px 6px', fontSize: 10, color: COLORS.textMuted }}>
                  {CHANNEL_ICONS[ch] || ''} {ch}
                </span>
              ))}
            </div>
          </div>
        )}

        {f.data_sources?.length > 0 && (
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, color: COLORS.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Data Sources</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {f.data_sources.map((ds: string) => (
                <span key={ds} style={{ background: COLORS.surface2, border: `1px solid ${COLORS.border}`, borderRadius: 3, padding: '1px 6px', fontSize: 10, color: COLORS.textMuted }}>{ds}</span>
              ))}
            </div>
          </div>
        )}

        {f.contain_display && (
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, color: COLORS.textDim, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 3 }}>Containment Target</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.green }}>{f.contain_display}</div>
            {f.contain_label && <div style={{ fontSize: 10, color: COLORS.textDim }}>{f.contain_label}</div>}
          </div>
        )}

      </div>
    </div>
  )
}

// ── Conversation Pane ─────────────────────────────────────────

interface ConvPaneProps {
  messages: ConversationMessage[]
  currentStep: ConversationStep | null
  onAnswer: (stepId: string, value: string | string[], chips: string[], other: string) => void
  progressPct: number
  currentStepIdx: number
  isComplete: boolean
  preSelectedChips?: string[]
}

function ConversationPane({ messages, currentStep, onAnswer, progressPct, currentStepIdx, isComplete, preSelectedChips = [] }: ConvPaneProps) {
  const chatRef = useRef<HTMLDivElement>(null)
  const [selectedChips, setSelectedChips] = useState<string[]>([])
  const [otherText, setOtherText] = useState('')
  const [textInput, setTextInput] = useState('')
  const prevStepIdx = useRef(currentStepIdx)

  useEffect(() => {
    // Pre-select confirmed flows on the first step
    if (currentStep?.id === 'flow_confirmation' && preSelectedChips.length > 0) {
      setSelectedChips(preSelectedChips)
    } else {
      setSelectedChips([])
    }
    setOtherText('')
    setTextInput('')
    prevStepIdx.current = currentStepIdx
  }, [currentStep?.id, currentStepIdx])

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages])

  const toggleChip = (opt: string) => {
    if (isSingle) {
      // Single select — submit immediately
      onAnswer(currentStep!.id, opt, [opt], '')
    } else if (isChipText && opt !== '+ Other') {
      // chip_or_text single selection (not Other)
      onAnswer(currentStep!.id, opt, [opt], '')
    } else if (isMulti || isChipText) {
      // Multi select — toggle
      setSelectedChips(prev =>
        prev.includes(opt) ? prev.filter(c => c !== opt) : [...prev, opt]
      )
    }
  }

  const submitChips = () => {
    if (!currentStep) return
    const val = otherText ? [...selectedChips, otherText] : selectedChips
    onAnswer(currentStep.id, val, selectedChips, otherText)
  }

  const submitText = () => {
    if (!currentStep || !textInput.trim()) return
    onAnswer(currentStep.id, textInput.trim(), [], '')
  }

  const isMulti    = currentStep?.type === 'chip_multi'
  const isSingle   = currentStep?.type === 'chip_single'
  const isChipText = currentStep?.type === 'chip_or_text'
  const hasChips   = (currentStep?.options?.length ?? 0) > 0
  const canSubmitChips = selectedChips.length > 0 || otherText.trim().length > 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

      {/* Progress bar */}
      <div style={{ padding: '8px 16px', borderBottom: `1px solid ${COLORS.border}`, flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ fontSize: 10, color: COLORS.textDim }}>Discovery Progress</span>
          <span style={{ fontSize: 10, fontWeight: 600, color: COLORS.accent }}>{progressPct}%</span>
        </div>
        <div style={{ height: 3, background: COLORS.border, borderRadius: 2 }}>
          <div style={{ height: '100%', background: COLORS.accent, borderRadius: 2, width: `${progressPct}%`, transition: 'width 0.4s ease' }} />
        </div>
      </div>

      {/* Messages — fixed height, scrollable */}
      <div ref={chatRef} style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              maxWidth: '85%',
              padding: '8px 12px',
              borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
              background: msg.role === 'user' ? COLORS.accent : COLORS.surface,
              border: msg.role === 'assistant' ? `1px solid ${COLORS.border}` : 'none',
              fontSize: 12,
              color: COLORS.textSec,
              lineHeight: 1.5,
            }}>
              {msg.content}
            </div>
          </div>
        ))}

        {isComplete && (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 20, padding: '6px 14px' }}>
              <Check size={12} color={COLORS.green} />
              <span style={{ fontSize: 11, color: COLORS.green }}>Discovery complete</span>
            </div>
          </div>
        )}
      </div>

      {/* Input area — fixed at bottom */}
      {!isComplete && currentStep && (
        <div style={{ flexShrink: 0, borderTop: `1px solid ${COLORS.border}`, padding: '10px 16px' }}>
          {hasChips ? (
            <div>
              {/* Pre-selection hint for flow_confirmation */}
              {currentStep?.id === 'flow_confirmation' && preSelectedChips.length > 0 && (
                <div style={{
                  fontSize: 10,
                  color: COLORS.accent,
                  marginBottom: 8,
                  padding: '4px 8px',
                  background: COLORS.accent + '11',
                  borderRadius: 4,
                  border: `1px solid ${COLORS.accent}33`,
                }}>
                  ✓ Pre-selected based on research — deselect any that don't apply, add any that do
                </div>
              )}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: (isMulti || isChipText) ? 8 : 0 }}>
                {currentStep.options!.map(opt => (
                  <button
                    key={opt}
                    onClick={() => toggleChip(opt)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 16,
                      border: `1px solid ${selectedChips.includes(opt) ? COLORS.accent : COLORS.border}`,
                      background: selectedChips.includes(opt) ? COLORS.accent + '22' : COLORS.surface,
                      color: selectedChips.includes(opt) ? COLORS.accent : COLORS.textMuted,
                      fontSize: 11,
                      cursor: 'pointer',
                      transition: 'all 0.15s',
                    }}
                  >
                    {opt}
                  </button>
                ))}
                {isChipText && (
                  <button
                    onClick={() => setOtherText(t => t === '' ? ' ' : '')}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 16,
                      border: `1px solid ${otherText ? COLORS.accent : COLORS.border}`,
                      background: otherText ? COLORS.accent + '22' : COLORS.surface,
                      color: otherText ? COLORS.accent : COLORS.textDim,
                      fontSize: 11,
                      cursor: 'pointer',
                    }}
                  >
                    + Other
                  </button>
                )}
                {isMulti && (
                  <button
                    onClick={() => setOtherText(t => t === '' ? ' ' : '')}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 16,
                      border: `1px solid ${otherText ? COLORS.accent : COLORS.border}`,
                      background: otherText ? COLORS.accent + '22' : COLORS.surface,
                      color: otherText ? COLORS.accent : COLORS.textDim,
                      fontSize: 11,
                      cursor: 'pointer',
                    }}
                  >
                    + Other
                  </button>
                )}
              </div>
              {(isMulti || isChipText) && otherText !== '' && (
                <input
                  type="text"
                  value={otherText === ' ' ? '' : otherText}
                  onChange={e => setOtherText(e.target.value)}
                  placeholder="Specify other..."
                  style={{
                    width: '100%',
                    background: COLORS.surface,
                    border: `1px solid ${COLORS.border}`,
                    borderRadius: 6,
                    padding: '6px 10px',
                    fontSize: 11,
                    color: COLORS.textSec,
                    marginBottom: 8,
                    outline: 'none',
                  }}
                />
              )}
              {(isMulti || isChipText) && (
                <button
                  onClick={submitChips}
                  disabled={!canSubmitChips}
                  style={{
                    width: '100%',
                    padding: '7px',
                    background: canSubmitChips ? COLORS.accent : COLORS.surface,
                    border: `1px solid ${canSubmitChips ? COLORS.accent : COLORS.border}`,
                    borderRadius: 6,
                    color: canSubmitChips ? '#fff' : COLORS.textDim,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: canSubmitChips ? 'pointer' : 'not-allowed',
                    transition: 'all 0.15s',
                  }}
                >
                  Continue →
                </button>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="text"
                value={textInput}
                onChange={e => setTextInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && submitText()}
                placeholder="Type your answer..."
                style={{
                  flex: 1,
                  background: COLORS.surface,
                  border: `1px solid ${COLORS.border}`,
                  borderRadius: 6,
                  padding: '7px 10px',
                  fontSize: 12,
                  color: COLORS.textSec,
                  outline: 'none',
                }}
              />
              <button
                onClick={submitText}
                disabled={!textInput.trim()}
                style={{
                  padding: '7px 14px',
                  background: COLORS.accent,
                  border: 'none',
                  borderRadius: 6,
                  color: '#fff',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Phase 2 Page ─────────────────────────────────────────

export default function Phase2Page() {
  const router = useRouter()
  const {
    sessionId,
    businessProfile,
    discovery,
    setConversation,
    setDiscovery,
    setPhase,
    phaseFlags,
  } = useSessionStore()

  const [convState, setConvState] = useState<ConversationState | null>(null)
  const [selectedFlowId, setSelectedFlowId] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const company = businessProfile?.company_name || ''

  // Load or init conversation on mount
  useEffect(() => {
    if (!sessionId) return

    async function init() {
      try {
        // Try to get existing state first
        const state = await Conversation.getState(sessionId!)
        if (state.messages.length === 0) {
          // Init with opening message
          const initiated = await Conversation.init(sessionId!)
          setConvState(initiated)
          setConversation(initiated)
        } else {
          setConvState(state)
          setConversation(state)
        }
      } catch (e) {
        console.error('Failed to load conversation:', e)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [sessionId])

  const handleAnswer = useCallback(async (
    stepId: string,
    value: string | string[],
    chips: string[],
    other: string
  ) => {
    if (!sessionId || submitting) return
    setSubmitting(true)
    try {
      const updated = await Conversation.answer({
        session_id:      sessionId,
        step_id:         stepId,
        answer:          value,
        chip_selections: chips,
        other_text:      other,
      })
      setConvState(updated)
      setConversation(updated)
      // Explicitly advance phase when conversation completes
      if (updated.is_complete) {
        setPhase(3)
      }
    } catch (e) {
      console.error('Failed to record answer:', e)
    } finally {
      setSubmitting(false)
    }
  }, [sessionId, submitting])

  const handleSelectFlow = useCallback((flowId: string) => {
    setSelectedFlowId(prev => prev === flowId ? '' : flowId)
  }, [])

  const flows = (convState?.discovery && convState.discovery.length > 0)
    ? convState.discovery
    : (discovery && discovery.length > 0)
    ? discovery
    : []
  const messages    = convState?.messages || []
  const progressPct = convState?.progress_pct || 0
  const isComplete  = convState?.is_complete || phaseFlags.phase_2 || false
  const stepIdx     = convState?.current_step_idx || 0
  const channels    = (convState?.answers?.channels || []) as string[]

  // currentStep: use API value, or fall back to step 0 if conversation just started
  const FIRST_STEP = {
    id: 'flow_confirmation',
    title: 'Use Cases',
    question: 'Which of these customer interaction types apply to your business?',
    type: 'multi_select',
    options: ['Billing Inquiry', 'Technical Support', 'Outage Reporting',
              'Account Changes', 'New Service Activation', 'Retention / Win-back',
              'Payments', 'Order Status', 'Appointment Scheduling', 'FAQ / General Inquiries'],
  }
  const currentStep = convState?.current_step ||
    (!isComplete && messages.length > 0 ? FIRST_STEP : null)

  const selectedFlow = flows.find(f => f.flow_id === selectedFlowId) || null

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <Loader2 size={20} className="animate-spin text-accent" />
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 180px)', // leave room for stepper + nav
        gap: 0,
        overflow: 'hidden',
      }}>

        {/* Top: conversation pane — fixed height */}
        <div style={{
          height: 320,
          flexShrink: 0,
          border: `1px solid ${COLORS.border}`,
          borderRadius: '8px 8px 0 0',
          overflow: 'hidden',
          background: COLORS.bg,
          position: 'relative',
        }}>
          {submitting && (
            <div style={{ position: 'absolute', top: 8, right: 12, zIndex: 10 }}>
              <Loader2 size={14} style={{ color: COLORS.accent, animation: 'spin 1s linear infinite' }} />
            </div>
          )}
          <ConversationPane
            messages={messages}
            currentStep={currentStep}
            onAnswer={handleAnswer}
            progressPct={progressPct}
            currentStepIdx={stepIdx}
            isComplete={isComplete}
            preSelectedChips={flows.filter(f => f.confirmed).map(f => f.flow_name)}
          />
        </div>

        {/* Bottom: diagram + detail panel */}
        <div style={{
          flex: 1,
          display: 'flex',
          overflow: 'hidden',
          border: `1px solid ${COLORS.border}`,
          borderTop: 'none',
          borderRadius: '0 0 8px 8px',
        }}>
          {/* Diagram */}
          <div style={{ flex: 1, overflow: 'auto', padding: 12, background: COLORS.bg }}>
            <PlatformDiagram
              flows={flows}
              channels={channels}
              companyName={company}
              selectedFlowId={selectedFlowId}
              onSelectFlow={handleSelectFlow}
            />
          </div>

          {/* Detail panel — slides in when flow selected */}
          {selectedFlow && (
            <DetailPanel
              flow={selectedFlow}
              onClose={() => setSelectedFlowId('')}
            />
          )}
        </div>

      </div>
    </AppShell>
  )
}