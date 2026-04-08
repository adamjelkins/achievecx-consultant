/**
 * store/session.ts
 *
 * Global session state using Zustand.
 * currentPhase = highwater mark (furthest phase reached).
 * Active UI phase is derived from URL, not this store.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ConversationState, FlowData, SessionResponse } from '@/lib/api'

// ── Phase types ──────────────────────────────────────────

export type Phase = 1 | 2 | 3 | '3r' | '3b' | 4

export const PHASE_ORDER: Phase[] = [1, 2, 3, '3r', '3b', 4]

export interface PhaseFlags {
  [key: string]: boolean
  phase_1: boolean
  phase_2: boolean
  phase_3: boolean
  phase_3r: boolean
  phase_3b: boolean
  phase_4: boolean
}

// ── Helpers ──────────────────────────────────────────────

export function phaseFromPath(pathname: string): Phase | null {
  if (!pathname.startsWith('/phase/')) return null
  const slug = pathname.replace('/phase/', '')
  const map: Record<string, Phase> = {
    '1': 1, '2': 2, '3': 3, '3r': '3r', '3b': '3b', '4': 4,
  }
  return map[slug] ?? null
}

export function phaseIndex(phase: Phase): number {
  return PHASE_ORDER.indexOf(phase)
}

// ── Store shape ──────────────────────────────────────────

interface SessionStore {
  // Identity
  sessionId: string | null

  // currentPhase = highwater mark (furthest phase reached)
  // UI active phase is derived from URL by components
  currentPhase: Phase
  phaseFlags: PhaseFlags
  intakeComplete: boolean

  // Business data
  businessProfile: Record<string, any>
  discovery: FlowData[]
  convAnswers: Record<string, any>
  assessment: Record<string, any> | null
  riskAssessment: Record<string, any> | null
  businessCase: Record<string, any> | null
  blueprint: Record<string, any> | null
  vendors: any[]

  // Conversation
  conversation: ConversationState | null

  // UI
  savingsSignalDismissed: boolean

  // Actions
  setSession: (resp: SessionResponse) => void
  setSessionId: (id: string) => void
  setPhase: (phase: Phase) => void
  setPhaseFlags: (flags: PhaseFlags) => void
  setBusinessProfile: (profile: Record<string, any>) => void
  setDiscovery: (flows: FlowData[]) => void
  setConversation: (state: ConversationState) => void
  setAssessment: (data: Record<string, any>) => void
  setRiskAssessment: (data: Record<string, any>) => void
  setBusinessCase: (data: Record<string, any>) => void
  setBlueprint: (data: Record<string, any>) => void
  setVendors: (data: any[]) => void
  dismissSavingsSignal: () => void
  reset: () => void
  isPhaseComplete: (phase: Phase) => boolean
  isPhaseAccessible: (phase: Phase) => boolean
}

const DEFAULT_FLAGS: PhaseFlags = {
  phase_1: false, phase_2: false, phase_3: false,
  phase_3r: false, phase_3b: false, phase_4: false,
}

// ── Store ────────────────────────────────────────────────

export const useSessionStore = create<SessionStore>()(
  persist(
    (set, get) => ({
      sessionId: null,
      currentPhase: 1,
      phaseFlags: DEFAULT_FLAGS,
      intakeComplete: false,
      businessProfile: {},
      discovery: [],
      convAnswers: {},
      assessment: null,
      riskAssessment: null,
      businessCase: null,
      blueprint: null,
      vendors: [],
      conversation: null,
      savingsSignalDismissed: false,

      setSession: (resp) => set({
        sessionId:      resp.session_id,
        currentPhase:   resp.current_phase as Phase,
        phaseFlags:     resp.phase_flags as PhaseFlags,
        intakeComplete: resp.intake_complete,
      }),

      setSessionId: (id) => set({ sessionId: id }),

      // Only advance highwater mark, never go backward
      setPhase: (phase) => set((state) => {
        const newIdx = phaseIndex(phase)
        const curIdx = phaseIndex(state.currentPhase)
        return newIdx > curIdx ? { currentPhase: phase } : {}
      }),

      setPhaseFlags: (flags) => set({ phaseFlags: flags }),

      setBusinessProfile: (profile) => set({
        businessProfile: profile,
        phaseFlags: { ...get().phaseFlags, phase_1: true },
      }),

      setDiscovery: (flows) => set({ discovery: flows }),

      setConversation: (state) => set((s) => ({
        conversation: state,
        convAnswers: state.answers,
        discovery: state.discovery,
        ...(state.is_complete ? {
          phaseFlags: { ...s.phaseFlags, phase_2: true },
          currentPhase: phaseIndex(3) > phaseIndex(s.currentPhase) ? 3 as Phase : s.currentPhase,
        } : {}),
      })),

      setAssessment: (data) => set((s) => ({
        assessment: data,
        phaseFlags: { ...s.phaseFlags, phase_3: true },
        currentPhase: phaseIndex('3r') > phaseIndex(s.currentPhase) ? '3r' : s.currentPhase,
      })),

      setRiskAssessment: (data) => set((s) => ({
        riskAssessment: data,
        phaseFlags: { ...s.phaseFlags, phase_3r: true },
        currentPhase: phaseIndex('3b') > phaseIndex(s.currentPhase) ? '3b' : s.currentPhase,
      })),

      setBusinessCase: (data) => set((s) => ({
        businessCase: data,
        phaseFlags: { ...s.phaseFlags, phase_3b: true },
        currentPhase: phaseIndex(4) > phaseIndex(s.currentPhase) ? 4 as Phase : s.currentPhase,
      })),

      setBlueprint: (data) => set((s) => ({
        blueprint: data,
        phaseFlags: { ...s.phaseFlags, phase_4: true },
      })),

      setVendors: (data) => set({ vendors: data }),

      dismissSavingsSignal: () => set({ savingsSignalDismissed: true }),

      reset: () => set({
        sessionId: null,
        currentPhase: 1,
        phaseFlags: DEFAULT_FLAGS,
        intakeComplete: false,
        businessProfile: {},
        discovery: [],
        convAnswers: {},
        assessment: null,
        riskAssessment: null,
        businessCase: null,
        blueprint: null,
        vendors: [],
        conversation: null,
        savingsSignalDismissed: false,
      }),

      isPhaseComplete: (phase: Phase) => {
        return get().phaseFlags[`phase_${phase}`] ?? false
      },

      isPhaseAccessible: (phase: Phase) => {
        const { phaseFlags, currentPhase } = get()
        // Phase is accessible if it's completed, or it's the next one after highwater
        const phaseIdx = phaseIndex(phase)
        const hwIdx = phaseIndex(currentPhase)
        return phaseIdx <= hwIdx + 1
      },
    }),
    {
      name: 'achievecx-session',
      partialize: (state) => ({
        sessionId:              state.sessionId,
        currentPhase:           state.currentPhase,
        phaseFlags:             state.phaseFlags,
        intakeComplete:         state.intakeComplete,
        savingsSignalDismissed: state.savingsSignalDismissed,
      }),
    }
  )
)