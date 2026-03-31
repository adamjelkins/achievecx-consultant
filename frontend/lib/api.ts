/**
 * lib/api.ts
 * 
 * Typed API client for all FastAPI endpoints.
 * All functions return typed responses and throw on error.
 */

import axios from 'axios'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
})

// ── Types ──────────────────────────────────────────────

export interface SessionResponse {
  session_id: string
  current_phase: number | string
  intake_complete: boolean
  phase_flags: Record<string, boolean>
}

export interface InferenceRequest {
  session_id: string
  email: string
  first_name: string
  last_name: string
  company_name?: string
  phone?: string
}

export interface InferenceResponse {
  session_id: string
  business_profile: Record<string, any>
  suggested_flows: FlowData[]
  inference_seeded: boolean
}

export interface FlowData {
  flow_id: string
  flow_name: string
  category: string
  confirmed: boolean
  confidence: number
  cwr?: string
  cwr_label?: string
  cwr_color?: string
  ai_score?: number
}

export interface ConversationStep {
  id: string
  title: string
  question: string
  type: string
  options?: string[]
  schema_key?: string
  required?: boolean
}

export interface ConversationMessage {
  role: 'assistant' | 'user'
  content: string
  step_id?: string
  timestamp?: string
}

export interface ConversationState {
  session_id: string
  messages: ConversationMessage[]
  current_step: ConversationStep | null
  current_step_idx: number
  progress_pct: number
  is_complete: boolean
  answers: Record<string, any>
  discovery: FlowData[]
}

// ── Session ────────────────────────────────────────────

export const Sessions = {
  create: (): Promise<SessionResponse> =>
    api.post('/api/sessions/').then(r => r.data),

  get: (id: string): Promise<SessionResponse> =>
    api.get(`/api/sessions/${id}`).then(r => r.data),

  reset: (id: string): Promise<void> =>
    api.delete(`/api/sessions/${id}`).then(r => r.data),
}

// ── Inference ──────────────────────────────────────────

export const Inference = {
  run: (req: InferenceRequest): Promise<InferenceResponse> =>
    api.post('/api/inference/run', req).then(r => r.data),
}

// ── Conversation ───────────────────────────────────────

export const Conversation = {
  init: (sessionId: string): Promise<ConversationState> =>
    api.post(`/api/conversation/${sessionId}/init`).then(r => r.data),

  getState: (sessionId: string): Promise<ConversationState> =>
    api.get(`/api/conversation/${sessionId}/state`).then(r => r.data),

  answer: (req: {
    session_id: string
    step_id: string
    answer: any
    chip_selections?: string[]
    other_text?: string
  }): Promise<ConversationState> =>
    api.post('/api/conversation/answer', req).then(r => r.data),

  confirmFlow: (sessionId: string, flowId: string, confirmed: boolean): Promise<any> =>
    api.post(`/api/conversation/${sessionId}/confirm-flow`, null, {
      params: { flow_id: flowId, confirmed },
    }).then(r => r.data),
}

// ── Assessment ─────────────────────────────────────────

export const Assessment = {
  run: (sessionId: string): Promise<any> =>
    api.post(`/api/assessment/${sessionId}/run`).then(r => r.data),

  get: (sessionId: string): Promise<any> =>
    api.get(`/api/assessment/${sessionId}`).then(r => r.data),
}

// ── Risk ───────────────────────────────────────────────

export const Risk = {
  run: (sessionId: string): Promise<any> =>
    api.post(`/api/risk/${sessionId}/run`).then(r => r.data),

  get: (sessionId: string): Promise<any> =>
    api.get(`/api/risk/${sessionId}`).then(r => r.data),
}

// ── Business Case ──────────────────────────────────────

export const BusinessCase = {
  getPrefill: (sessionId: string): Promise<any> =>
    api.get(`/api/business-case/${sessionId}/prefill`).then(r => r.data),

  run: (sessionId: string, inputs?: Record<string, any>): Promise<any> =>
    api.post('/api/business-case/run', { session_id: sessionId, inputs }).then(r => r.data),

  get: (sessionId: string): Promise<any> =>
    api.get(`/api/business-case/${sessionId}`).then(r => r.data),
}

// ── Blueprint ──────────────────────────────────────────

export const Blueprint = {
  generate: (sessionId: string): Promise<any> =>
    api.post(`/api/blueprint/${sessionId}/generate`).then(r => r.data),

  get: (sessionId: string): Promise<any> =>
    api.get(`/api/blueprint/${sessionId}`).then(r => r.data),
}

// ── Vendors ────────────────────────────────────────────

export const Vendors = {
  score: (sessionId: string): Promise<any> =>
    api.post(`/api/vendors/${sessionId}/score`).then(r => r.data),

  get: (sessionId: string): Promise<any> =>
    api.get(`/api/vendors/${sessionId}`).then(r => r.data),
}
