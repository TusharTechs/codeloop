import { useEffect, useState } from 'react'
import { api } from '../api'
import { Logo } from '../components/Logo'
import type { CodeRecord } from '../types'

export function RecordPage({ codeId }: { codeId: string }) {
  const [rec, setRec] = useState<CodeRecord | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const load = () =>
      api
        .record(codeId)
        .then((r) => alive && setRec(r))
        .catch((e: Error) => alive && setError(e.message))
    void load()
    const id = window.setInterval(load, 5000) // a running code keeps adding to its record
    return () => {
      alive = false
      window.clearInterval(id)
    }
  }, [codeId])

  if (error) return <div className="record"><div className="notice bad">{error}</div></div>
  if (!rec) return <div className="record muted">Loading the Code Record…</div>

  const s = rec.summary ?? {}
  const loops = rec.loops
  const closed = loops.filter((l) => l.history.some((h) => h.state === 'ACKNOWLEDGED')).length
  const orders = loops.filter((l) => !l.without_order).length

  return (
    <div className="record">
      <div className="brand">
        <Logo />
        <span className="name">Code Record</span>
        <span className="pill" style={{ marginLeft: 'auto' }}>
          {rec.code.mode === 'replay' ? `Replay · ${rec.code.scenario}` : 'Live code'}
        </span>
        <button className="btn small noprint" onClick={() => window.print()}>
          Print
        </button>
      </div>

      <div className="muted">
        Started {new Date(rec.code.created_at).toLocaleString()} · code {rec.code.id} · {rec.code.status}
        {rec.code.outcome ? ` · outcome ${rec.code.outcome}` : ''}
      </div>

      <div className="tiles">
        <div className="tile"><span className="k">Duration</span><span className="v">{rec.duration ?? "—"}</span></div>
        <div className="tile"><span className="k">Shocks</span><span className="v">{String(s.shocks ?? rec.administered.filter((a) => a.what.startsWith('shock')).length)}</span></div>
        <div className="tile"><span className="k">Drugs given</span><span className="v">{rec.administered.filter((a) => !a.what.startsWith('shock')).length}</span></div>
        <div className="tile"><span className="k">Closed-loop orders</span><span className="v">{orders ? Math.round((closed / orders) * 100) : 0}%</span><span className="s">{closed} of {orders} read back</span></div>
        <div className="tile"><span className="k">Conflicts caught</span><span className="v" style={{ color: 'var(--red)' }}>{loops.filter((l) => l.history.some((h) => h.state === 'CONFLICT')).length}</span></div>
        <div className="tile"><span className="k">Spoken prompts</span><span className="v" style={{ color: 'var(--violet)' }}>{rec.spoken.length}</span></div>
      </div>

      <div className={`notice ${rec.integrity.chain_valid ? '' : 'bad'}`} style={rec.integrity.chain_valid ? { background: 'var(--teal-bg)', color: 'var(--teal)' } : undefined}>
        <b>{rec.integrity.chain_valid ? 'Record intact.' : `Record altered at entry ${rec.integrity.first_bad_entry}.`}</b>{' '}
        {rec.integrity.entries} audit entries, each hash-chained to the one before.
        <div className="hash">head {rec.integrity.head_hash}</div>
      </div>

      {rec.needs_review.length > 0 && (
        <section className="panel">
          <h3>Needs review before sign-off</h3>
          {rec.needs_review.map((n) => (
            <div key={n.loop}>
              <b>{n.what}</b> <span className="muted">· {n.state.toLowerCase()} · {n.reason}</span>
            </div>
          ))}
        </section>
      )}

      <section className="panel">
        <h3>Administered</h3>
        <div className="tablewrap">
          <table className="t">
            <thead><tr><th>Code time</th><th>What</th><th>Communication</th></tr></thead>
            <tbody>
              {rec.administered.map((a, i) => (
                <tr key={i}>
                  <td className="mono">{a.clock}</td>
                  <td><b>{a.what}</b></td>
                  <td>{a.without_order ? <span className="chip warn">no order heard</span> : a.closed_loop ? <span className="chip ack">closed loop</span> : <span className="chip">no read-back</span>}</td>
                </tr>
              ))}
              {rec.administered.length === 0 && <tr><td colSpan={3} className="muted">Nothing administered.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h3>Timeline, with the words each entry came from</h3>
        <div className="tablewrap">
          <table className="t">
            <thead><tr><th>Time</th><th>Event</th><th>Heard</th><th>Who</th><th>Source</th></tr></thead>
            <tbody>
              {rec.timeline.map((t, i) => (
                <tr key={i}>
                  <td className="mono">{t.clock}</td>
                  <td>{t.what} {t.unconfirmed && <span className="chip warn">unconfirmed</span>}</td>
                  <td className="muted">“{t.quote}”</td>
                  <td>{t.role ?? t.speaker ?? '—'}</td>
                  <td className="muted">{t.source}{t.confidence != null ? ` · ${Math.round(t.confidence * 100)}%` : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h3>What CodeLoop said</h3>
        {rec.spoken.length === 0 && <div className="empty">Nothing.</div>}
        {rec.spoken.map((p) => (
          <div key={p.id}>
            <span className="mono muted">{Math.floor(p.at_s / 60).toString().padStart(2, '0')}:{Math.floor(p.at_s % 60).toString().padStart(2, '0')}</span>{' '}
            <b>{p.text}</b> <span className="faint">· {p.rule.toLowerCase().replace(/_/g, ' ')}{p.waited_s > 0.1 ? ` · waited ${p.waited_s}s for a gap` : ''}</span>
          </div>
        ))}
      </section>

      <p className="faint" style={{ fontSize: 14 }}>
        Generated by CodeLoop from the audit log. Entries marked unconfirmed must be reviewed by the recorder before this
        record is filed. CodeLoop is not a medical device.
      </p>
    </div>
  )
}
