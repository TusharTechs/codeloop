import type { CodeEvent, Control, Loop } from '../types'
import { loopTitle, mmss, num } from '../format'

interface Props {
  loop: Loop
  events: Map<string, CodeEvent>
  now: number
  roleOf: (speaker: string | null) => string | null
  send: (c: Control) => void
}

function quoteFor(loop: Loop, states: string[], events: Map<string, CodeEvent>): CodeEvent | null {
  for (let i = loop.history.length - 1; i >= 0; i--) {
    const h = loop.history[i]
    if (states.includes(h.state) && h.event_id && events.has(h.event_id)) return events.get(h.event_id)!
  }
  return null
}

export function LoopCard({ loop, events, now, roleOf, send }: Props) {
  const t = loopTitle(loop)
  const orderEv = quoteFor(loop, ['ORDERED'], events)
  const ackEv = quoteFor(loop, ['ACKNOWLEDGED'], events)
  const conflictEv = quoteFor(loop, ['CONFLICT'], events)
  const doneEv = quoteFor(loop, ['DONE'], events)
  const hadAck = loop.history.some((h) => h.state === 'ACKNOWLEDGED')
  const age = now - loop.ordered_at_s
  const who = (e: CodeEvent | null) => {
    if (!e) return ''
    if (e.source === 'manual') return ' — on screen'
    const r = roleOf(e.speaker)
    return e.speaker ? ` — ${r ?? e.speaker}` : ''
  }
  const unit = loop.action === 'shock' ? 'J' : loop.unit ?? ''

  const readBackClass =
    loop.state === 'CONFLICT' ? 'bad' : loop.state === 'UNACKNOWLEDGED' ? 'miss' : hadAck || loop.state === 'DONE' ? 'on' : ''
  const readBackText =
    loop.state === 'CONFLICT'
      ? `“${conflictEv?.quote ?? ''}”${who(conflictEv)}`
      : ackEv
        ? `“${ackEv.quote}”${who(ackEv)}`
        : loop.state === 'UNACKNOWLEDGED'
          ? 'Nobody confirmed it'
          : loop.state === 'DONE'
            ? 'Completed without a read-back'
            : 'Waiting…'

  return (
    <article className={`loop ${loop.state}`} aria-label={`${t.name} ${t.value} ${t.unit} ${loop.state}`}>
      <div className="head">
        <div className="what">
          {t.name} <span className="mono">{t.value}</span>
          <span className="unit">{t.unit}</span>
        </div>
        <div className="age">
          {loop.state === 'DONE' || loop.state === 'CANCELLED' ? loop.state.toLowerCase() : `${mmss(age)} open`}
        </div>
      </div>
      <div className="steps">
        <div className={`step ${loop.without_order ? 'miss' : 'on'}`}>
          <span className="k">Ordered</span>
          <span className="q">{loop.without_order ? 'No order heard' : orderEv ? `“${orderEv.quote}”${who(orderEv)}` : '—'}</span>
        </div>
        <div className={`step ${readBackClass}`}>
          <span className="k">{loop.state === 'CONFLICT' ? 'Read back differs' : 'Read back'}</span>
          <span className="q">{readBackText}</span>
        </div>
        <div className={`step ${loop.state === 'DONE' ? 'on' : ''}`}>
          <span className="k">{loop.action === 'shock' ? 'Delivered' : 'Given'}</span>
          <span className="q">{doneEv ? `“${doneEv.quote}”${who(doneEv)}` : loop.state === 'CANCELLED' ? 'Cancelled' : '—'}</span>
        </div>
      </div>
      {loop.state === 'CONFLICT' && (
        <div className="actions">
          <span className="note">
            Ordered {num(loop.ordered_value)} {unit} · read back {num(loop.heard_value)} {unit}
          </span>
          <button className="btn danger small" onClick={() => send({ type: 'confirm_loop', loop_id: loop.id, value: loop.ordered_value })}>
            Confirm {num(loop.ordered_value)} {unit}
          </button>
          <button className="btn small" onClick={() => send({ type: 'confirm_loop', loop_id: loop.id, value: loop.heard_value })}>
            Confirm {num(loop.heard_value)} {unit}
          </button>
        </div>
      )}
      {loop.state === 'UNACKNOWLEDGED' && <div className="note">Ordered {mmss(age)} ago. Not acknowledged.</div>}
      {loop.needs_confirmation && loop.state !== 'CONFLICT' && (
        <div className="actions">
          <span className="chip warn">Low transcription confidence</span>
          <button className="btn warn small" onClick={() => send({ type: 'confirm_loop', loop_id: loop.id, value: loop.ordered_value })}>
            Confirm {num(loop.ordered_value)} {unit}
          </button>
        </div>
      )}
    </article>
  )
}
