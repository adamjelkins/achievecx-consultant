/**
 * store/session.ts
 *
 * Global session state using Zustand.
 * Mirrors the backend SessionState model.
 * session_id persisted to localStorage.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ConversationState, FlowData, SessionResponse } from '@/lib/api'

// ── Phase types ──────────────────────────────────────────

export type Phase = 1 | 2 | 3 | '3r' | '3b' | 4

export interface PhaseFlags {
  [key: string]: boolean
  phase_1: boolean
  phase_2: boolean
  phase_3: boolean
  phase_3r: boolean
  phase_3b: boolean
  phase_4: boolean
}

// ── Store shape ──────────────────────────────────────────

interface SessionStore {
  // Identity
  sessionId: string | null

  // Phase
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

  // Computed
  canAdvanceTo: (phase: Phase) => boolean
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

      setPhase: (phase) => set({ currentPhase: phase }),

      setPhaseFlags: (flags) => set({ phaseFlags: flags }),

      setBusinessProfile: (profile) => set({
        businessProfile: profile,
        phaseFlags: { ...get().phaseFlags, phase_1: true },
      }),

      setDiscovery: (flows) => set({ discovery: flows }),

      setConversation: (state) => set({
        conversation: state,
        convAnswers: state.answers,
        discovery: state.discovery,
        ...(state.is_complete ? {
          phaseFlags: { ...get().phaseFlags, phase_2: true },
          currentPhase: 3 as Phase,
        } : {}),
      }),

      setAssessment: (data) => set({
        assessment: data,
        phaseFlags: { ...get().phaseFlags, phase_3: true },
        currentPhase: '3r',
      }),

      setRiskAssessment: (data) => set({
        riskAssessment: data,
        phaseFlags: { ...get().phaseFlags, phase_3r: true },
        currentPhase: '3b',
      }),

      setBusinessCase: (data) => set({
        businessCase: data,
        phaseFlags: { ...get().phaseFlags, phase_3b: true },
        currentPhase: 4,
      }),

      setBlueprint: (data) => set({
        blueprint: data,
        phaseFlags: { ...get().phaseFlags, phase_4: true },
      }),

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

      canAdvanceTo: (phase: Phase) => {
        const { phaseFlags } = get()
        const order: Phase[] = [1, 2, 3, '3r', '3b', 4]
        const idx = order.indexOf(phase)
        if (idx <= 0) return true
        const prior = order[idx - 1]
        const key = `phase_${prior}` as keyof PhaseFlags
        return phaseFlags[key]
      },
    }),
    {
      name: 'achievecx-session',
      partialize: (state) => ({
        sessionId:             state.sessionId,
        currentPhase:          state.currentPhase,
        phaseFlags:            state.phaseFlags,
        intakeComplete:        state.intakeComplete,
        savingsSignalDismissed: state.savingsSignalDismissed,
      }),
    }
  )
)