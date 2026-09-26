import { useState } from 'react'
import type { SessionView } from '../state'

type Step = { say: string[]; then: string; done: boolean }

/**
 * A short script for trying a live code alone. Every line works from a single voice: read-backs
 * use explicit words ("drawing up", "pushing", "is in") so they don't depend on who is speaking.
 * Each step ticks when CodeLoop's own state shows it happened.
 */
export function TryLive({ view }: { view: SessionView }) {
  const [open, setOpen] = useState(true)
  const state = view.state
  if (!state) return null
  const loops = Object.values(view.loops)
  const epi = loops.filter((l) => l.drug === 'epinephrine')
  const steps: Step[] = [
    {
      say: ['Code blue, starting CPR now.'],
      then: 'The clock and the two-minute CPR cycle start.',
      done: state.status !== 'not_started',
    },
    {
      say: ['Give one milligram of epinephrine.'],
      then: 'Now stay silent. The card turns amber at 10 s, and at 15 s CodeLoop says it was not acknowledged.',
      done: epi.some((l) => l.history.some((h) => h.state === 'UNACKNOWLEDGED')),
    },
    {
      say: ['Epi one milligram, drawing up now.', 'Epi one milligram is in.'],
      then: 'Read back, then given: the loop closes.',
      done: epi.some((l) => l.state === 'DONE' && l.history.some((h) => h.state === 'ACKNOWLEDGED')),
    },
    {
      say: ['Amiodarone three hundred milligrams.', 'Amio one fifty, pushing.'],
      then: 'The card turns red and CodeLoop says "Check dose". Talk over it with "No, three hundred" and it stops.',
      done: loops.some((l) => l.history.some((h) => h.state === 'CONFLICT')),
    },
    {
      say: ['CodeLoop, when was the last epi?'],
      then: 'CodeLoop answers from its own record.',
      done: view.feed.some((f) => f.kind === 'codeloop' && !!f.answerTo),
    },
    {
      say: ['Pulse check. We have ROSC.'],
      then: 'Timers pause until you tap Confirm. Then open the Code Record.',
      done: state.status.endsWith('pending_confirmation') || state.status === 'ended',
    },
  ]
  const count = steps.filter((s) => s.done).length
  const current = steps.findIndex((s) => !s.done)

  if (!open) {
    return (
      <button className="trylive-pill noprint" onClick={() => setOpen(true)}>
        Try-it script · {count}/{steps.length}
      </button>
    )
  }
  return (
    <aside className="trylive noprint" aria-label="Try it live">
      <div className="guide-head">
        <span className="upper">Try it live · say these lines</span>
        <button className="guide-x" onClick={() => setOpen(false)} aria-label="Hide the script">
          ×
        </button>
      </div>
      <ol>
        {steps.map((s, i) => (
          <li key={i} className={s.done ? 'done' : i === current ? 'current' : ''}>
            <span className="tick" aria-hidden>{s.done ? '✓' : i + 1}</span>
            <span>
              {s.say.map((line) => (
                <q key={line}>{line}</q>
              ))}
              {i === current && <span className="then">{s.then}</span>}
            </span>
          </li>
        ))}
      </ol>
      <div className="faint" style={{ fontSize: 13 }}>
        {count === steps.length ? 'All six behaviours shown.' : 'One voice is enough; a second person makes it feel real.'}
      </div>
    </aside>
  )
}
