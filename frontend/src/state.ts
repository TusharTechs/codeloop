import type { CodeEvent, CodeState, Flag, Loop, ServerMsg, UtteranceMsg } from './types'

export type FeedItem =
  | { kind: 'utterance'; id: string; utt: UtteranceMsg; events: CodeEvent[] }
  | { kind: 'codeloop'; id: string; text: string; status: 'queued' | 'speaking' | 'done' | 'interrupted' | 'dropped'; answerTo?: string }

export interface GuideItem {
  id: string
  title: string
  body: string
  tone: 'teal' | 'amber' | 'red' | 'violet' | 'blue'
  at: number // performance.now() when shown
}

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
  guide: GuideItem[]
  guideSeen: string[]
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
  guide: [],
  guideSeen: [],
}

export type Action =
  | { type: 'socket'; connected: boolean }
  | { type: 'msg'; msg: ServerMsg }
  | { type: 'dismiss'; id: string }

const MAX_FEED = 400

function upsertLoop(v: SessionView, loop: Loop): SessionView {
  const exists = loop.id in v.loops
  return { ...v, loops: { ...v.loops, [loop.id]: loop }, loopOrder: exists ? v.loopOrder : [...v.loopOrder, loop.id] }
}

function setLine(feed: FeedItem[], id: string, patch: Partial<Extract<FeedItem, { kind: 'codeloop' }>>): FeedItem[] {
  return feed.map((f) => (f.kind === 'codeloop' && f.id === id ? { ...f, ...patch } : f))
}

// Plain-language explanations for someone watching a replay: what CodeLoop just did, and why.
const FLAG_GUIDE: Record<string, Omit<GuideItem, 'id' | 'at'>> = {
  LOOP_UNACKNOWLEDGED: {
    title: 'Nobody confirmed that order',
    body: 'An order was spoken, but no one read it back for 10 seconds. CodeLoop turned the card amber and will say it out loud at 15 seconds if the room stays silent.',
    tone: 'amber',
  },
  LOOP_CONFLICT: {
    title: 'The read-back dose does not match',
    body: 'The read-back differs from the order. CodeLoop turned the card red and asks the team to check the dose. The loop only closes once the values agree.',
    tone: 'red',
  },
  RHYTHM_NONSHOCKABLE_CHARGE: {
    title: 'Shock ordered on a non-shockable rhythm',
    body: 'The last rhythm on record is not shockable. CodeLoop points that out; the team leader decides. It never recommends treatment.',
    tone: 'red',
  },
  ROSC_NEEDS_CONFIRMATION: {
    title: 'ROSC heard: a human must confirm',
    body: 'One misheard word must never end a resuscitation, so CodeLoop only pauses its timers until someone taps Confirm.',
    tone: 'blue',
  },
  EPI_OVERDUE: {
    title: 'Epinephrine is overdue',
    body: 'Five minutes since the last dose. CodeLoop keeps the ACLS clock so nobody has to watch it.',
    tone: 'amber',
  },
}

function addGuide(v: SessionView, key: string, item: Omit<GuideItem, 'id' | 'at'>): SessionView {
  if (v.guideSeen.includes(key)) return v
  const g: GuideItem = { ...item, id: `${key}-${v.guideSeen.length}`, at: performance.now() }
  return { ...v, guide: [...v.guide, g].slice(-4), guideSeen: [...v.guideSeen, key] }
}

function guideFor(v: SessionView, m: ServerMsg): SessionView {
  switch (m.type) {
    case 'flag': {
      const item = FLAG_GUIDE[m.flag.rule]
      return item ? addGuide(v, m.flag.rule, item) : v
    }
    case 'loop': {
      const l = m.loop
      if (l.state === 'DONE' && l.history.some((h) => h.state === 'ACKNOWLEDGED') && !l.history.some((h) => h.state === 'CONFLICT'))
        return addGuide(v, 'first-closed-loop', {
          title: 'A closed loop',
          body: 'Ordered, read back, given, each step logged with the exact words and speaker. AssemblyAI Universal-3.5 Pro streaming, with speaker labels and Medical Mode, hears the whole room.',
          tone: 'teal',
        })
      if (l.state === 'DONE' && l.history.some((h) => h.state === 'CONFLICT'))
        return addGuide(v, 'conflict-resolved', {
          title: 'Conflict resolved, and remembered',
          body: 'The team agreed on the dose and it was given. The record keeps the whole story: ordered, the wrong read-back, the correction, given.',
          tone: 'teal',
        })
      return v
    }
    case 'agent_interrupted':
      return addGuide(v, 'barge-in', {
        title: 'A clinician spoke over CodeLoop, so it stopped',
        body: 'The AssemblyAI Voice Agent API detects a real interruption and stops CodeLoop mid-word. Humans always take precedence in the room.',
        tone: 'violet',
      })
    case 'answer':
      return addGuide(v, 'answer', {
        title: 'Answered from the record',
        body: `“${m.question}” gets its answer from CodeLoop's own record, never from a guess. Hindi–English questions work too.`,
        tone: 'violet',
      })
    case 'prompt':
      if (m.prompt.rule === 'CPR_CYCLE_DUE')
        return addGuide(v, 'cycle', {
          title: 'Two-minute CPR cycle',
          body: 'CodeLoop keeps the ACLS clock and calls the rhythm check out loud, waiting for a gap in the room before speaking.',
          tone: 'blue',
        })
      return v
    case 'utterance':
      if (m.echo)
        return addGuide(v, 'echo', {
          title: "CodeLoop ignored its own voice",
          body: 'The room mic picked up CodeLoop speaking. It recognised its own words and did not log them as the team.',
          tone: 'blue',
        })
      return v
    default:
      return v
  }
}

export function reduce(v: SessionView, a: Action): SessionView {
  if (a.type === 'socket') return { ...v, connected: a.connected }
  if (a.type === 'dismiss') return { ...v, guide: v.guide.filter((g) => g.id !== a.id) }
  return guideFor(reduceMsg(v, a.msg), a.msg)
}

function reduceMsg(v: SessionView, m: ServerMsg): SessionView {
  switch (m.type) {
    case 'hello': {
      const loops: Record<string, Loop> = {}
      for (const l of m.loops) loops[l.id] = l
      const flags: Record<string, Flag> = {}
      for (const f of m.flags) flags[f.id] = f
      const byUtt = new Map<string, CodeEvent[]>()
      for (const e of m.events) if (e.utterance_id) byUtt.set(e.utterance_id, [...(byUtt.get(e.utterance_id) ?? []), e])
      const feed: FeedItem[] = m.utterances.map((u) => ({ kind: 'utterance', id: u.id, utt: u, events: byUtt.get(u.id) ?? [] }))
      return { ...v, state: m.state, loops, loopOrder: m.loops.map((l) => l.id), flags, events: m.events, feed, error: null, guide: [], guideSeen: [] }
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
