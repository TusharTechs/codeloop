import type { CodeEvent, CodeState, Flag, Loop, ServerMsg, UtteranceMsg } from './types'

export type FeedItem =
  | { kind: 'utterance'; id: string; utt: UtteranceMsg; events: CodeEvent[] }
  | { kind: 'codeloop'; id: string; text: string; status: 'queued' | 'speaking' | 'done' | 'interrupted' | 'dropped'; answerTo?: string }

export interface SessionView {
  connected: boolean
  state: CodeState | null
  loops: Record<string, Loop>
  loopOrder: string[]
  flags: Record<string, Flag>
  events: CodeEvent[]
  feed: FeedItem[]
  partial: { text: string; speaker: string | null } | null
  speakingLine: string | null
  replayFinished: boolean
  closed: boolean
  error: string | null
}

export const initialView: SessionView = {
  connected: false,
  state: null,
  loops: {},
  loopOrder: [],
  flags: {},
  events: [],
  feed: [],
  partial: null,
  speakingLine: null,
  replayFinished: false,
  closed: false,
  error: null,
}

export type Action = { type: 'socket'; connected: boolean } | { type: 'msg'; msg: ServerMsg }

const MAX_FEED = 400

function upsertLoop(v: SessionView, loop: Loop): SessionView {
  const exists = loop.id in v.loops
  return { ...v, loops: { ...v.loops, [loop.id]: loop }, loopOrder: exists ? v.loopOrder : [...v.loopOrder, loop.id] }
}

function setLine(feed: FeedItem[], id: string, patch: Partial<Extract<FeedItem, { kind: 'codeloop' }>>): FeedItem[] {
  return feed.map((f) => (f.kind === 'codeloop' && f.id === id ? { ...f, ...patch } : f))
}

export function reduce(v: SessionView, a: Action): SessionView {
  if (a.type === 'socket') return { ...v, connected: a.connected }
  const m = a.msg
  switch (m.type) {
    case 'hello': {
      const loops: Record<string, Loop> = {}
      for (const l of m.loops) loops[l.id] = l
      const flags: Record<string, Flag> = {}
      for (const f of m.flags) flags[f.id] = f
      const byUtt = new Map<string, CodeEvent[]>()
      for (const e of m.events) if (e.utterance_id) byUtt.set(e.utterance_id, [...(byUtt.get(e.utterance_id) ?? []), e])
      const feed: FeedItem[] = m.utterances.map((u) => ({ kind: 'utterance', id: u.id, utt: u, events: byUtt.get(u.id) ?? [] }))
      return { ...v, state: m.state, loops, loopOrder: m.loops.map((l) => l.id), flags, events: m.events, feed, error: null }
    }
    case 'state':
      return { ...v, state: m.state }
    case 'partial':
      return { ...v, partial: m.text ? { text: m.text, speaker: m.speaker } : null }
    case 'utterance': {
      const { type: _t, ...utt } = m
      void _t
      const item: FeedItem = { kind: 'utterance', id: utt.id, utt, events: [] }
      return { ...v, partial: null, feed: [...v.feed, item].slice(-MAX_FEED) }
    }
    case 'event': {
      const e = m.event
      const feed = v.feed.map((f) => (f.kind === 'utterance' && f.id === e.utterance_id ? { ...f, events: [...f.events, e] } : f))
      return { ...v, events: [...v.events, e], feed }
    }
    case 'loop':
      return upsertLoop(v, m.loop)
    case 'flag':
    case 'flag_resolved':
      return { ...v, flags: { ...v.flags, [m.flag.id]: m.flag } }
    case 'prompt':
      return { ...v, feed: [...v.feed, { kind: 'codeloop' as const, id: m.prompt.id, text: m.prompt.text, status: 'queued' as const }].slice(-MAX_FEED) }
    case 'answer':
      return { ...v, feed: [...v.feed, { kind: 'codeloop' as const, id: m.id, text: m.text, status: 'queued' as const, answerTo: m.question }].slice(-MAX_FEED) }
    case 'agent_speaking':
      return { ...v, speakingLine: m.line_id, feed: setLine(v.feed, m.line_id, { status: 'speaking' }) }
    case 'agent_done':
      return { ...v, speakingLine: v.speakingLine === m.line_id ? null : v.speakingLine, feed: setLine(v.feed, m.line_id, { status: 'done' }) }
    case 'agent_interrupted':
      return { ...v, speakingLine: null, feed: setLine(v.feed, m.line_id, { status: 'interrupted' }) }
    case 'line_dropped':
      return { ...v, feed: setLine(v.feed, m.id, { status: 'dropped' }) }
    case 'replay_finished':
      return { ...v, replayFinished: true }
    case 'error':
      return { ...v, error: m.message }
    case 'agent_error':
      return { ...v, error: `CodeLoop's voice: ${m.message}` }
    case 'closed':
      return { ...v, closed: true }
    default:
      return v
  }
}
