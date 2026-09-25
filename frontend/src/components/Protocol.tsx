import type { CodeState } from '../types'
import { cap, drugName, mmss, num } from '../format'

const CYCLE = 120

export function CprRing({ state, drift }: { state: CodeState; drift: number }) {
  const cycle = state.cpr.cycle
  const remaining = cycle ? Math.max(0, cycle.remaining_s - drift) : null
  const frac = remaining == null ? 0 : remaining / CYCLE
  const r = 92
  const c = 2 * Math.PI * r
  const cls = remaining == null ? '' : remaining <= 0 ? 'due' : remaining <= 15 ? 'warn' : ''
  const color = remaining == null ? 'var(--grey)' : remaining <= 0 ? 'var(--red)' : remaining <= 15 ? 'var(--amber)' : 'var(--teal)'
  return (
    <div className={`ring ${cls}`} role="timer" aria-label="Time to rhythm check">
      <svg viewBox="0 0 210 210">
        <circle cx="105" cy="105" r={r} fill="none" stroke="var(--panel-3)" strokeWidth="14" />
        <circle
          cx="105"
          cy="105"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - frac)}
          style={{ transition: 'stroke-dashoffset 0.25s linear' }}
        />
      </svg>
      <div className="c">
        {state.status === 'not_started' ? (
          <span className="t">Waiting for CPR</span>
        ) : state.cpr.running && remaining != null ? (
          <>
            <span className="n">{remaining <= 0 ? 'NOW' : mmss(remaining)}</span>
            <span className="t">to rhythm check</span>
          </>
        ) : (
          <>
            <span className="n" style={{ color: 'var(--muted)' }}>
              ‖
            </span>
            <span className="t">{state.status === 'ended' ? 'Code ended' : 'CPR paused'}</span>
          </>
        )}
        <span className="t" style={{ marginTop: 4 }}>
          Cycles {state.cpr.cycles_completed}
        </span>
      </div>
    </div>
  )
}

export function EpiWindow({ state, drift }: { state: CodeState; drift: number }) {
  const w = state.epinephrine_window
  if (w.state === 'none_given') {
    return (
      <div className="epi">
        <div className="headline">No epinephrine yet</div>
        <div className="muted">Window starts at the first dose.</div>
      </div>
    )
  }
  const since = (w.seconds_since_last ?? 0) + (state.status === 'active' ? drift : 0)
  const st = since >= 300 ? 'overdue' : since >= 180 ? 'open' : 'waiting'
  const pct = Math.min(100, (since / 360) * 100)
  return (
    <div className={`epi ${st}`}>
      <div className="headline">
        {st === 'waiting' && <>Next window in <span className="mono">{mmss(180 - since)}</span></>}
        {st === 'open' && <>Window open</>}
        {st === 'overdue' && <>Overdue</>}
      </div>
      <div className="track">
        <div className="fill" style={{ width: `${pct}%` }} />
        <div className="mark" style={{ left: `${(180 / 360) * 100}%` }} />
        <div className="mark" style={{ left: `${(300 / 360) * 100}%` }} />
      </div>
      <div className="scale">
        <span>last dose</span>
        <span style={{ marginLeft: '28%' }}>3 min</span>
        <span>5 min</span>
        <span />
      </div>
      <div className="muted">
        Last dose <span className="mono">{mmss(since)}</span> ago
      </div>
    </div>
  )
}

const RHYTHM_LABEL: Record<string, string> = { VF: 'V-fib', PVT: 'pVT', PEA: 'PEA', ASYSTOLE: 'Asystole', SINUS: 'Organized' }

export function Vitals({ state, drift }: { state: CodeState; drift: number }) {
  const rh = state.rhythm.current
  const drugs = Object.entries(state.last_drugs)
  return (
    <>
      <div className="tiles">
        <div className={`tile ${rh ? (state.rhythm.shockable ? 'shockable' : 'nonshockable') : ''}`}>
          <span className="k">Rhythm</span>
          <span className="v">{rh ? RHYTHM_LABEL[rh] : '—'}</span>
          <span className="s">
            {rh ? `${state.rhythm.shockable ? 'shockable' : 'non-shockable'} · ${mmss((state.rhythm.recorded_seconds_ago ?? 0) + drift)} ago` : 'not recorded'}
          </span>
        </div>
        <div className="tile">
          <span className="k">Shocks</span>
          <span className="v">{state.shocks.count}</span>
          <span className="s">
            {state.shocks.count ? `last ${state.shocks.last_energy_j} J · ${mmss((state.shocks.last_seconds_ago ?? 0) + drift)} ago` : 'none'}
          </span>
        </div>
      </div>
      <div className="druglist">
        {drugs.length === 0 && <div className="empty">No drugs given yet.</div>}
        {drugs.map(([name, d]) => (
          <div key={name}>
            <span>
              <b>{cap(drugName(name))}</b> {num(d.dose)} {d.unit} {d.total_doses > 1 && <span className="muted">×{d.total_doses}</span>}
            </span>
            <span className="mono muted">{mmss(d.seconds_ago + drift)} ago</span>
          </div>
        ))}
      </div>
    </>
  )
}
