import { useEffect, useState } from 'react'
import { api } from '../api'
import { Logo } from '../components/Logo'
import type { QualityMetric } from '../types'

type Code = Awaited<ReturnType<typeof api.codes>>[number]

function metric(c: Code, key: string): QualityMetric | undefined {
  const q = (c.summary as { quality?: QualityMetric[] } | null)?.quality
  return q?.find((m) => m.key === key)
}

function Cell({ m }: { m?: QualityMetric }) {
  if (!m) return <td className="faint">—</td>
  return (
    <td>
      <span className="mono">{m.display}</span>{' '}
      {m.status === 'met' && <span className="chip ack">met</span>}
      {m.status === 'missed' && <span className="chip bad">missed</span>}
    </td>
  )
}

/** Simulation-centre / resuscitation-committee view across codes. */
export function Dashboard() {
  const [codes, setCodes] = useState<Code[]>([])
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    api.codes().then(setCodes).catch((e: Error) => setError(e.message))
  }, [])
  const ended = codes.filter((c) => c.status === 'ended' && c.summary)
  const rates = ended.map((c) => metric(c, 'closed_loop_rate')?.value).filter((v): v is number => v != null)
  const conflicts = ended.reduce((n, c) => n + (Number(metric(c, 'dose_conflicts')?.value) || 0), 0)
  const unack = ended.reduce((n, c) => n + (Number(metric(c, 'orders_unacknowledged')?.value) || 0), 0)
  const shockMet = ended.filter((c) => metric(c, 'time_to_first_shock')?.status === 'met').length
  const shockAll = ended.filter((c) => metric(c, 'time_to_first_shock')).length

  return (
    <div className="record">
      <div className="brand">
        <Logo />
        <span className="name">Codes dashboard</span>
        <a className="btn small" href="#/" style={{ marginLeft: 'auto' }}>
          Home
        </a>
      </div>
      <p className="muted" style={{ margin: 0 }}>
        For simulation debriefs and resuscitation committees: how closed-loop communication and the key ACLS time targets
        went across every code CodeLoop recorded.
      </p>
      {error && <div className="notice bad">{error}</div>}
      <div className="dash-agg tiles">
        <div className="tile"><span className="k">Codes recorded</span><span className="v">{ended.length}</span></div>
        <div className="tile"><span className="k">Orders read back</span><span className="v">{rates.length ? Math.round((rates.reduce((a, b) => a + b, 0) / rates.length) * 100) : 0}%</span><span className="s">average per code</span></div>
        <div className="tile"><span className="k">Dose conflicts caught</span><span className="v" style={{ color: 'var(--red)' }}>{conflicts}</span></div>
        <div className="tile"><span className="k">Unacknowledged orders</span><span className="v" style={{ color: 'var(--amber)' }}>{unack}</span></div>
        <div className="tile"><span className="k">First shock ≤ 2 min</span><span className="v">{shockMet}/{shockAll}</span></div>
      </div>
      <div className="tablewrap">
        <table className="t">
          <thead>
            <tr><th>Code</th><th>Outcome</th><th>Read back</th><th>Unack.</th><th>Conflicts</th><th>First shock</th><th>First epi</th><th>CPR fraction</th></tr>
          </thead>
          <tbody>
            {ended.map((c) => (
              <tr key={c.id}>
                <td>
                  <a href={`#/record/${c.id}`}>{new Date(c.created_at).toLocaleString()}</a>
                  <div className="faint" style={{ fontSize: 13 }}>{c.mode === 'replay' ? c.scenario : 'live code'}</div>
                </td>
                <td>{c.outcome ?? '—'}</td>
                <Cell m={metric(c, 'closed_loop_rate')} />
                <Cell m={metric(c, 'orders_unacknowledged')} />
                <Cell m={metric(c, 'dose_conflicts')} />
                <Cell m={metric(c, 'time_to_first_shock')} />
                <Cell m={metric(c, 'time_to_first_epinephrine')} />
                <Cell m={metric(c, 'cpr_fraction')} />
              </tr>
            ))}
            {ended.length === 0 && <tr><td colSpan={8} className="muted">No finished codes yet. Replay the quick tour to see one.</td></tr>}
          </tbody>
        </table>
      </div>
      <p className="faint" style={{ fontSize: 14 }}>
        Targets: AHA adult ACLS and Get With The Guidelines-Resuscitation (first shock ≤ 2 min for VF/pVT, first epinephrine ≤ 5
        min for non-shockable rhythms, compression fraction ≥ 80%). CPR timing is estimated from spoken calls.
      </p>
    </div>
  )
}
