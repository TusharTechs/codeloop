import { useEffect, useRef, useState } from 'react'
import type { Control } from '../types'
import type { FeedItem } from '../state'
import { ROLES, eventChip, mmss } from '../format'

interface Props {
  feed: FeedItem[]
  partial: { text: string; speaker: string | null } | null
  roles: Record<string, string>
  send: (c: Control) => void
}

export function Feed({ feed, partial, roles, send }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const [stick, setStick] = useState(true)
  const [menuFor, setMenuFor] = useState<string | null>(null)

  useEffect(() => {
    const el = box.current
    if (el && stick) el.scrollTop = el.scrollHeight
  }, [feed, partial, stick])

  return (
    <div
      className="feed"
      ref={box}
      onScroll={(e) => {
        const el = e.currentTarget
        setStick(el.scrollHeight - el.scrollTop - el.clientHeight < 60)
      }}
      aria-live="polite"
    >
      {feed.length === 0 && <div className="empty">Listening. What the team says appears here.</div>}
      {feed.map((f) =>
        f.kind === 'utterance' ? (
          <div key={f.id} className={`utt ${f.utt.echo ? 'echo' : ''}`}>
            <button
              className={`who ${f.utt.speaker ? roles[f.utt.speaker] ?? '' : ''}`}
              title="Assign a role to this voice"
              onClick={() => setMenuFor(menuFor === f.id ? null : f.id)}
            >
              {f.utt.speaker ? roles[f.utt.speaker] ?? f.utt.speaker : '?'}
            </button>
            <div className="text">
              {f.utt.text}
              <span className="faint mono" style={{ fontSize: 12, marginLeft: 8 }}>
                {mmss(f.utt.end_s)}
              </span>
            </div>
            {menuFor === f.id && f.utt.speaker && (
              <div className="rolemenu">
                {ROLES.map((r) => (
                  <button
                    key={r}
                    className="btn small"
                    onClick={() => {
                      send({ type: 'assign_role', speaker: f.utt.speaker!, role: r })
                      setMenuFor(null)
                    }}
                  >
                    Voice {f.utt.speaker} is {r}
                  </button>
                ))}
              </div>
            )}
            {(f.events.length > 0 || f.utt.echo || f.utt.min_confidence < 0.6) && (
              <div className="meta">
                {f.utt.echo && <span className="chip">CodeLoop's own voice: ignored</span>}
                {f.events.map((e) => {
                  const c = eventChip(e)
                  return c ? (
                    <span key={e.id} className={`chip ${c.tone}`} title={e.unconfirmed ? 'Needs confirmation' : e.source}>
                      {c.label}
                      {e.unconfirmed ? ' ?' : ''}
                    </span>
                  ) : null
                })}
                {!f.utt.echo && f.utt.min_confidence < 0.6 && <span className="chip warn">low confidence</span>}
              </div>
            )}
          </div>
        ) : (
          <div key={f.id} className={`cl ${f.status}`}>
            <span className="badge">{f.status === 'speaking' ? <span className="eq" aria-label="speaking"><i /><i /><i /></span> : 'CodeLoop'}</span>
            <span className="text">{f.text}</span>
            {(f.answerTo || f.status === 'interrupted' || f.status === 'dropped' || f.status === 'queued') && (
              <span className="q">
                {f.answerTo && <>Answering “{f.answerTo}”. </>}
                {f.status === 'interrupted' && 'Stopped: a clinician spoke over it.'}
                {f.status === 'dropped' && 'Not spoken: no longer current.'}
                {f.status === 'queued' && 'Waiting for a gap in the room…'}
              </span>
            )}
          </div>
        ),
      )}
      <div className="partial">{partial?.text ? `… ${partial.text}` : ''}</div>
    </div>
  )
}
