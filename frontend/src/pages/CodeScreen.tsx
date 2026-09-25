import { useEffect, useMemo, useRef, useState } from 'react'
import { MicCapture } from '../audio/mic'
import type { PcmPlayer } from '../audio/player'
import { Logo } from '../components/Logo'
import { LoopCard } from '../components/LoopCard'
import { Feed } from '../components/Feed'
import { Guide } from '../components/Guide'
import { CprRing, EpiWindow, Vitals } from '../components/Protocol'
import { QuickLog } from '../components/QuickLog'
import { QualityList } from '../components/Quality'
import { loopTitle, mmss, num } from '../format'
import type { CodeEvent, Loop } from '../types'
import { useCodeSocket } from '../useCodeSocket'

const OPEN_ORDER: Record<string, number> = { CONFLICT: 0, UNACKNOWLEDGED: 1, ORDERED: 2, ACKNOWLEDGED: 3 }

export function CodeScreen({ codeId, player }: { codeId: string; player: PcmPlayer }) {
  const { view, send, sendAudio, dismiss } = useCodeSocket(codeId, player)
  const [guideOn, setGuideOn] = useState<boolean | null>(null)
  const state = view.state
  const [, setTick] = useState(0)
  const stateAt = useRef(performance.now())
  const [micLevel, setMicLevel] = useState(0)
  const [micError, setMicError] = useState<string | null>(null)
  const [ending, setEnding] = useState(false)
  const [ask, setAsk] = useState('')
  const [voiceOn, setVoiceOn] = useState(false)

  useEffect(() => {
    stateAt.current = performance.now()
  }, [state])

  useEffect(() => {
    const id = window.setInterval(() => setTick((t) => t + 1), 250)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    player.onVoiceActivity = setVoiceOn
    return () => {
      player.onVoiceActivity = null
    }
  }, [player])

  // Live codes stream the room microphone to the server.
  const isLive = state?.mode === 'live'
  useEffect(() => {
    if (!isLive || view.closed) return
    const mic = new MicCapture()
    let alive = true
    mic
      .start(({ pcm, rms }) => {
        if (!alive) return
        sendAudio(pcm)
        setMicLevel(rms)
      })
      .catch((e: Error) => setMicError(e.message))
    return () => {
      alive = false
      mic.stop()
    }
  }, [isLive, view.closed, sendAudio])

  const running = state && (state.status === 'active' || state.status.endsWith('pending_confirmation'))
  const drift = running ? Math.min(2, (performance.now() - stateAt.current) / 1000) : 0
  const now = (state?.audio_clock_s ?? 0) + drift
  const events = useMemo(() => new Map<string, CodeEvent>(view.events.map((e) => [e.id, e])), [view.events])
  const loops = view.loopOrder.map((id) => view.loops[id])
  const open = loops.filter((l) => l.state in OPEN_ORDER).sort((a, b) => OPEN_ORDER[a.state] - OPEN_ORDER[b.state] || b.ordered_at_s - a.ordered_at_s)
  const done = loops.filter((l) => !(l.state in OPEN_ORDER)).reverse().slice(0, 10)
  const roles = state?.roles ?? {}
  const roleOf = (s: string | null) => (s ? roles[s] ?? null : null)
  const critical = Object.values(view.flags).filter((f) => f.resolved_at_s == null && f.severity === 'critical' && !f.loop_id)

  if (!state) {
    return (
      <div className="home">
        <div className="brand">
          <Logo /> <span className="name">CodeLoop</span>
        </div>
        <div className="muted">{view.error ?? (view.closed ? 'This code is no longer running.' : 'Connecting to the code…')}</div>
        {view.closed && <a href={`#/record/${codeId}`}>Open the Code Record</a>}
      </div>
    )
  }

  const pending = state.status.endsWith('pending_confirmation')
  const showGuide = guideOn ?? state.mode === 'replay'
  const statusLabel = state.status === 'ended' ? `Ended · ${state.outcome ?? ''}` : pending ? 'Confirm ROSC' : state.status === 'not_started' ? 'Listening' : 'Code time'

  return (
    <div className="code">
      <header className="topbar">
        <div className="left">
          <a href="#/" className="brand" style={{ textDecoration: 'none', color: 'inherit' }} aria-label="Home">
            <Logo size={32} />
          </a>
          <span className={`pill ${state.mode === 'live' ? 'bad' : 'info'}`}>
            <span className="dot" />
            {state.mode === 'live' ? 'LIVE' : 'REPLAY'}
          </span>
          <span className={`pill ${state.ears === 'live' && view.connected ? 'ok' : 'warn'}`} title="AssemblyAI Universal-3.5 Pro streaming">
            Ears {view.connected ? state.ears : 'offline'}
          </span>
          <span className={`pill ${voiceOn || state.voice === 'speaking' ? 'voice' : state.voice === 'ready' ? 'ok' : 'warn'}`} title="AssemblyAI Voice Agent API">
            {voiceOn || state.voice === 'speaking' ? (
              <span className="eq">
                <i />
                <i />
                <i />
              </span>
            ) : null}
            Voice {voiceOn ? 'speaking' : state.voice}
          </span>
          {state.latency_ms.p50 != null && (
            <span className="pill" title="Speech end to event on screen">
              <span className="mono">{(state.latency_ms.p50 / 1000).toFixed(1)}s</span> lag
            </span>
          )}
          {isLive && (
            <span className="pill" title="Microphone level">
              Mic <span className="meter"><i style={{ width: `${Math.min(100, micLevel * 400)}%` }} /></span>
            </span>
          )}
        </div>
        <div className="clock">
          <span className="v" aria-live="off">{mmss(state.status === 'not_started' ? 0 : state.clock_s + drift)}</span>
          <span className="l">{statusLabel}</span>
        </div>
        <div className="right noprint">
          <button
            className={`btn small ${showGuide ? '' : 'ghost'}`}
            onClick={() => setGuideOn(!showGuide)}
            aria-pressed={showGuide}
            title="Plain-language captions explaining each catch"
          >
            Guide {showGuide ? 'on' : 'off'}
          </button>
          {state.muted ? (
            <button className="btn warn small" onClick={() => send({ type: 'unmute' })}>
              Voice muted · unmute
            </button>
          ) : (
            <button className="btn small" onClick={() => send({ type: 'mute', seconds: 120 })} title="Silence CodeLoop for 2 minutes">
              Mute 2 min
            </button>
          )}
          <select
            className="btn small"
            value={state.policy}
            onChange={(e) => send({ type: 'set_policy', policy: e.target.value as typeof state.policy })}
            aria-label="What CodeLoop says out loud"
          >
            <option value="timers_and_loops">Speaks: timers + loops</option>
            <option value="timers">Speaks: timers only</option>
            <option value="silent">Screen only</option>
          </select>
          <a className="btn small" href={`#/record/${codeId}`} target="_blank" rel="noreferrer">
            Record
          </a>
          {!ending ? (
            <button className="btn danger small" onClick={() => setEnding(true)} disabled={state.status === 'ended'}>
              End code
            </button>
          ) : (
            <>
              <button className="btn primary small" onClick={() => { send({ type: 'end_code', outcome: 'rosc' }); setEnding(false) }}>
                ROSC
              </button>
              <button className="btn danger small" onClick={() => { send({ type: 'end_code', outcome: 'terminated' }); setEnding(false) }}>
                Terminated
              </button>
              <button className="btn ghost small" onClick={() => setEnding(false)}>
                Cancel
              </button>
            </>
          )}
        </div>
      </header>

      <div className="banners" aria-live="assertive">
        {pending && (
          <div className="banner warning">
            <span className="grow">{state.status.startsWith('rosc') ? 'ROSC called.' : 'Termination called.'} Timers are paused until someone confirms.</span>
            <button className="btn primary" onClick={() => send({ type: 'confirm_end' })}>
              Confirm and end code
            </button>
            <button className="btn" onClick={() => send({ type: 'reject_end' })}>
              Not yet, keep going
            </button>
          </div>
        )}
        {critical.map((f) => (
          <div key={f.id} className="banner critical">
            <span className="grow">{f.message}</span>
            <span className="mono">{mmss(f.at_s)}</span>
          </div>
        ))}
        {micError && <div className="banner critical">Microphone: {micError}</div>}
        {view.error && <div className="banner critical">{view.error}</div>}
        {!view.connected && !view.closed && <div className="banner warning">Reconnecting to the server… the code keeps running there.</div>}
        {view.closed && (
          <div className="banner info">
            <span className="grow">This code has ended.</span>
            <a className="btn primary" href={`#/record/${codeId}`}>
              Open the Code Record
            </a>
          </div>
        )}
        {view.replayFinished && !view.closed && state.mode === 'replay' && (
          <div className="banner info">
            <span className="grow">Replay finished. Review what CodeLoop captured.</span>
            <a className="btn" href={`#/record/${codeId}`} target="_blank" rel="noreferrer">
              Code Record
            </a>
          </div>
        )}
      </div>

      {showGuide && <Guide items={view.guide} dismiss={dismiss} />}

      <main className="grid">
        <section className="col" aria-label="Protocol">
          <div className="panel">
            <h3>CPR cycle</h3>
            <CprRing state={state} drift={drift} />
          </div>
          <div className="panel">
            <h3>Epinephrine</h3>
            <EpiWindow state={state} drift={drift} />
          </div>
          <div className="panel">
            <h3>Rhythm · shocks · drugs</h3>
            <Vitals state={state} drift={drift} />
          </div>
          <div className="panel">
            <h3>Quality vs AHA targets</h3>
            <QualityList metrics={state.quality ?? []} compact />
          </div>
        </section>

        <section className="col" aria-label="Orders">
          <div className="panel">
            <h3>
              Open orders <span className="pill">{open.length}</span>
            </h3>
            <div className="loops">
              {open.length === 0 && <div className="empty">No open orders. Every order CodeLoop hears appears here until it is read back and given.</div>}
              {open.map((l: Loop) => (
                <LoopCard key={l.id} loop={l} events={events} now={now} roleOf={roleOf} send={send} />
              ))}
            </div>
          </div>
          <div className="panel">
            <h3>Completed</h3>
            <div className="closed-list">
              {done.length === 0 && <div className="empty">Nothing given yet.</div>}
              {done.map((l) => {
                const t = loopTitle(l)
                const closedLoop = l.history.some((h) => h.state === 'ACKNOWLEDGED')
                return (
                  <div key={l.id}>
                    <span className="mono muted">{mmss(l.closed_at_s ?? l.ordered_at_s)}</span>
                    <span>
                      <b>{t.name}</b> {t.value} {t.unit}{' '}
                      {l.state === 'CANCELLED' && <span className="chip">cancelled</span>}
                      {l.needs_confirmation && <span className="chip warn">confirm value</span>}
                    </span>
                    <span style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      {l.history.some((h) => h.state === 'CONFLICT') && <span className="chip bad">dose conflict caught</span>}
                      {l.history.some((h) => h.state === 'UNACKNOWLEDGED') && <span className="chip warn">went unacknowledged</span>}
                      <span className={`chip ${l.without_order ? 'warn' : closedLoop ? 'ack' : ''}`}>
                        {l.without_order ? 'no order heard' : closedLoop ? 'closed loop' : l.state === 'DONE' ? 'no read-back' : ''}
                      </span>
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
          <div className="panel noprint">
            <h3>Tap to log</h3>
            <QuickLog state={state} send={send} />
          </div>
        </section>

        <section className="col" aria-label="What CodeLoop heard">
          <div className="panel">
            <h3>
              Heard in the room
              {Object.keys(state.names).length > 0 && (
                <span className="muted" style={{ textTransform: 'none', letterSpacing: 0 }}>
                  {Object.entries(state.names).map(([n, r]) => `${n[0].toUpperCase() + n.slice(1)}: ${r}`).join(' · ')}
                </span>
              )}
            </h3>
            <Feed feed={view.feed} partial={view.partial} roles={roles} send={send} />
            <form
              className="ask noprint"
              onSubmit={(e) => {
                e.preventDefault()
                if (ask.trim()) send({ type: 'ask', text: ask.trim() })
                setAsk('')
              }}
            >
              <input id="ask" value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="Ask CodeLoop: last epi? what's due?" aria-label="Ask CodeLoop" />
              <button className="btn" type="submit">
                Ask
              </button>
            </form>
            <div className="faint" style={{ fontSize: 13 }}>
              Or say “CodeLoop, …” out loud. Answers come from the record, never from a guess. Open orders: {state.open_orders.map((o) => `${o.order} ${num(o.seconds_open)}s`).join(', ') || 'none'}.
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
