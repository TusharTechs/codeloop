// Mirrors the backend's WebSocket protocol (backend/src/codeloop/api/app.py, session.py).

export type LoopState = 'ORDERED' | 'UNACKNOWLEDGED' | 'ACKNOWLEDGED' | 'CONFLICT' | 'DONE' | 'CANCELLED'
export type Severity = 'info' | 'warning' | 'critical'
export type Rhythm = 'VF' | 'PVT' | 'PEA' | 'ASYSTOLE' | 'SINUS'

export interface LoopTransition {
  at_s: number
  state: LoopState
  event_id: string | null
  note: string
}

export interface Loop {
  id: string
  action: 'drug' | 'shock'
  drug: string | null
  ordered_value: number | null
  heard_value: number | null
  unit: string | null
  state: LoopState
  opened_at_s: number
  ordered_at_s: number
  closed_at_s: number | null
  ordered_by: string | null
  acknowledged_by: string | null
  without_order: boolean
  needs_confirmation: boolean
  history: LoopTransition[]
}

export interface Flag {
  id: string
  rule: string
  severity: Severity
  message: string
  at_s: number
  loop_id: string | null
  event_id: string | null
  resolved_at_s: number | null
}

export interface CodeEvent {
  id: string
  kind: string
  at_s: number
  utterance_id: string | null
  speaker: string | null
  action: 'drug' | 'shock' | null
  drug: string | null
  dose: number | null
  unit: string | null
  energy_j: number | null
  rhythm: Rhythm | null
  role: string | null
  name: string | null
  quote: string
  source: 'grammar' | 'llm' | 'both' | 'manual'
  value_confidence: number | null
  unconfirmed: boolean
}

export interface UtteranceMsg {
  id: string
  speaker: string | null
  role: string | null
  text: string
  start_s: number
  end_s: number
  language: string | null
  min_confidence: number
  echo: boolean
  latency_ms: number
}

export interface CodeState {
  status: 'not_started' | 'active' | 'ended' | 'rosc_pending_confirmation' | 'terminated_pending_confirmation'
  outcome: string | null
  clock_s: number
  cpr: { running: boolean; cycle: { elapsed_s: number; remaining_s: number } | null; cycles_completed: number }
  rhythm: { current: Rhythm | null; recorded_seconds_ago: number | null; shockable: boolean | null }
  shocks: { count: number; last_energy_j: string | null; last_seconds_ago: number | null }
  last_drugs: Record<string, { dose: string; unit: string | null; given_at_clock_s: number; seconds_ago: number; total_doses: number }>
  epinephrine_window: { state: 'none_given' | 'waiting' | 'open' | 'overdue'; seconds_since_last?: number; opens_in_s?: number }
  open_orders: { id: string; order: string; state: LoopState; seconds_open: number; heard_value: string | null }[]
  active_flags: { rule: string; severity: Severity; message: string }[]
  roles: Record<string, string>
  names: Record<string, string>
  code_id: string
  mode: 'live' | 'replay'
  scenario: string | null
  audio_clock_s: number
  policy: 'silent' | 'timers' | 'timers_and_loops'
  muted: boolean
  voice: string
  ears: string
  latency_ms: { p50: number | null; p90: number | null }
  quality: QualityMetric[]
}

export interface QualityMetric {
  key: string
  label: string
  value: number | null
  display: string
  target: string
  status: 'met' | 'missed' | 'info' | 'n/a'
  note: string
}

export interface SpokenLine {
  id: string
  text: string
  kind: 'prompt' | 'answer'
  at_s?: number
  interrupted?: boolean
  question?: string
}

export type ServerMsg =
  | { type: 'hello'; state: CodeState; loops: Loop[]; flags: Flag[]; events: CodeEvent[]; utterances: UtteranceMsg[]; spoken: SpokenLine[] }
  | { type: 'state'; state: CodeState }
  | ({ type: 'utterance' } & UtteranceMsg)
  | { type: 'partial'; text: string; speaker: string | null }
  | { type: 'event'; event: CodeEvent }
  | { type: 'loop'; loop: Loop }
  | { type: 'flag'; flag: Flag }
  | { type: 'flag_resolved'; flag: Flag }
  | { type: 'prompt'; prompt: { id: string; rule: string; category: string; text: string; at_s: number; priority: number } }
  | { type: 'answer'; id: string; question: string; topic: string; text: string }
  | { type: 'agent_speaking'; line_id: string; text: string }
  | { type: 'agent_said'; line_id: string; text: string; interrupted: boolean }
  | { type: 'agent_done'; line_id: string }
  | { type: 'agent_interrupted'; line_id: string }
  | { type: 'agent_error'; code: string; message: string }
  | { type: 'line_dropped'; id: string; reason: string }
  | { type: 'speaker_revision'; revisions: { turn_order: number; speaker: string }[] }
  | { type: 'replay_finished' }
  | { type: 'error'; message: string }
  | { type: 'closed'; summary: Record<string, unknown> }

export type Control =
  | { type: 'assign_role'; speaker: string; role: string }
  | { type: 'confirm_loop'; loop_id: string; value: number | null }
  | { type: 'manual_event'; kind: string; action?: 'drug' | 'shock'; drug?: string; dose?: number; unit?: string; energy_j?: number; rhythm?: Rhythm }
  | { type: 'confirm_end' }
  | { type: 'reject_end' }
  | { type: 'end_code'; outcome: 'rosc' | 'terminated' }
  | { type: 'set_policy'; policy: CodeState['policy'] }
  | { type: 'mute'; seconds: number }
  | { type: 'unmute' }
  | { type: 'ask'; text: string }
  | { type: 'stop' }

export interface Scenario {
  id: string
  title: string
  duration_s: number
  noise: string
  cast: Record<string, string>
}

export interface SecondListenItem {
  status: 'confirmed' | 'value_mismatch' | 'live_only' | 'second_only'
  what: string
  at_s: number
  live_quote: string | null
  second_quote: string | null
  live_value: number | null
  second_value: number | null
}

export interface SecondListen {
  status: 'running' | 'done' | 'failed'
  counts?: Record<SecondListenItem['status'], number>
  live_events?: number
  items?: SecondListenItem[]
  error?: string
}

export interface CodeRecord {
  code: { id: string; created_at: string; mode: string; scenario: string | null; status: string; outcome: string | null; ended_at: string | null }
  integrity: { chain_valid: boolean; first_bad_entry: number | null; entries: number; head_hash: string }
  summary: Record<string, number | string | null> | null
  duration: string | null
  duration_s: number | null
  administered: { clock: string; what: string; without_order: boolean; closed_loop: boolean }[]
  quality: QualityMetric[]
  second_listen: SecondListen | null
  timeline: { clock: string; at_s: number; what: string; kind: string; quote: string; speaker: string | null; role: string | null; source: string; confidence: number | null; unconfirmed: boolean }[]
  loops: Loop[]
  flags: Flag[]
  spoken: { id: string; text: string; rule: string; kind: string; at_s: number; waited_s: number }[]
  answers: { id: string; question: string; topic: string; text: string }[]
  controls: Record<string, unknown>[]
  needs_review: { loop: string; what: string; state: string; reason: string }[]
}
