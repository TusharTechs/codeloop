import { useEffect, useState } from 'react'
import { ApiError, api, getToken, setToken } from '../api'
import type { PcmPlayer } from '../audio/player'
import { Logo } from '../components/Logo'
import { mmss } from '../format'
import type { Scenario } from '../types'

type Health = Awaited<ReturnType<typeof api.health>>
type Recent = Awaited<ReturnType<typeof api.codes>>

export function Home({ player }: { player: PcmPlayer }) {
  const [health, setHealth] = useState<Health | null>(null)
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [recent, setRecent] = useState<Recent>([])
  const [needToken, setNeedToken] = useState(false)
  const [token, setTok] = useState(getToken())
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      setHealth(await api.health())
      setScenarios(await api.scenarios())
      setRecent(await api.codes())
      setNeedToken(false)
      setError(null)
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) setNeedToken(true)
      else setError(e instanceof Error ? e.message : String(e))
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const tour = scenarios.find((s) => s.id.startsWith('demo_tour'))

  const start = async (mode: 'live' | 'replay', scenario?: string) => {
    setBusy(scenario ?? mode)
    setError(null)
    try {
      await player.resume() // unlock audio inside this click
      if (mode === 'live') {
        // Ask for the microphone now so the prompt appears while the user is looking.
        const s = await navigator.mediaDevices.getUserMedia({ audio: true })
        s.getTracks().forEach((t) => t.stop())
      }
      const code = await api.start(mode, scenario)
      location.hash = `#/code/${code.id}`
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="home">
      <div className="brand">
        <Logo />
        <span className="name">CodeLoop</span>
        {health && (
          <span className={`pill ${health.assemblyai_key ? 'ok' : 'bad'}`} style={{ marginLeft: 'auto' }}>
            <span className="dot" />
            {health.assemblyai_key ? 'AssemblyAI connected' : 'No AssemblyAI key on the server'}
          </span>
        )}
      </div>

      <section className="hero">
        <h1>
          Every order heard. <em>Every loop closed.</em>
        </h1>
        <p>
          CodeLoop is the recorder at a cardiac arrest. It listens to the whole resuscitation team, logs every drug,
          shock and rhythm with the exact words it heard, runs the ACLS clock out loud, and speaks up when an order was
          never confirmed back.
        </p>
        {!needToken && tour && (
          <div className="hero-cta">
            <button className="btn primary big" onClick={() => start('replay', tour.id)} disabled={!!busy || !health?.assemblyai_key}>
              {busy === tour.id ? 'Starting…' : `Start here · ${Math.round(tour.duration_s / 10) * 10}-second guided tour`}
            </button>
            <span className="faint">A mock code through live AssemblyAI, with captions. Turn your sound on.</span>
          </div>
        )}
        <div className="stat-strip">
          <span>
            In filmed resuscitations only <b>26%</b> of spoken orders were closed-loop; those were done <b>3.6×</b> sooner.
          </span>
          <span>
            Hospital records agree with observers on epinephrine timing at <b>κ 0.27</b>.
          </span>
        </div>
      </section>

      {needToken && (
        <form
          className="card"
          onSubmit={(e) => {
            e.preventDefault()
            setToken(token)
            void load()
          }}
        >
          <h2>Access code</h2>
          <p>This CodeLoop server is private. Enter the access code you were given.</p>
          <div className="field">
            <input id="token" value={token} onChange={(e) => setTok(e.target.value)} type="password" autoComplete="off" aria-label="Access code" />
          </div>
          <button className="btn primary" type="submit">
            Continue
          </button>
        </form>
      )}
      {error && <div className="notice bad">{error}</div>}

      {!needToken && (
        <section className="launch">
          <div className="card">
            <h2>Run a live code</h2>
            <p>
              Put this tablet on the crash cart and start. CodeLoop listens through the microphone. Trying it alone? The live
              screen shows six lines to say, and ticks each one off as CodeLoop reacts.
            </p>
            <button className="btn primary big" onClick={() => start('live')} disabled={!!busy || !health?.assemblyai_key}>
              {busy === 'live' ? 'Starting…' : 'Start live code'}
            </button>
            <p className="faint" style={{ fontSize: 14 }}>
              Use headphones or a separate speaker only if the room is very quiet; CodeLoop filters out its own voice.
            </p>
          </div>
          <div className="card">
            <h2>Replay a mock code</h2>
            <p>A recorded mock code streams through the real pipeline (live AssemblyAI, real engine) at real-time speed. Turn your sound on.</p>
            {scenarios.map((s) => (
              <div className="scenario" key={s.id}>
                <span className="t">
                  {s.id.startsWith('demo_tour') && <span className="pill ok" style={{ marginRight: 8 }}>Start here</span>}
                  {s.title}
                </span>
                <span className="s">
                  {mmss(s.duration_s)} · {Object.values(s.cast).join(', ')} · {s.noise === 'ward' ? 'alarms and compressions in the background' : s.noise}
                </span>
                <button className="btn primary" onClick={() => start('replay', s.id)} disabled={!!busy || !health?.assemblyai_key}>
                  {busy === s.id ? 'Starting…' : 'Replay'}
                </button>
              </div>
            ))}
            {scenarios.length === 0 && <div className="empty">No mock codes installed on this server.</div>}
          </div>
        </section>
      )}

      <section className="flow" aria-label="How CodeLoop works">
        <div>
          <span className="upper faint">1 · Hears</span>
          <span className="k">The whole room</span>
          <span className="d">AssemblyAI Universal-3.5 Pro streaming with speaker labels, Medical Mode and ACLS keyterms, English and Hindi.</span>
        </div>
        <div>
          <span className="upper faint">2 · Understands</span>
          <span className="k">Orders and read-backs</span>
          <span className="d">A deterministic grammar turns speech into events. Every event quotes the exact words it came from.</span>
        </div>
        <div>
          <span className="upper faint">3 · Tracks</span>
          <span className="k">Every loop</span>
          <span className="d">Ordered → read back → given. Silence past 10 s or a different dose read back is caught at once.</span>
        </div>
        <div>
          <span className="upper faint">4 · Speaks</span>
          <span className="k">Only when it matters</span>
          <span className="d">AssemblyAI Voice Agent API voices fixed prompts and stops the instant a clinician talks over it.</span>
        </div>
      </section>

      {recent.length > 0 && (
        <section className="recent" aria-label="Recent codes">
          <h2 style={{ margin: 0, fontSize: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            Recent codes
            <a className="btn small" href="#/codes">Codes dashboard</a>
          </h2>
          {recent.slice(0, 8).map((c) => (
            <a key={c.id} href={c.status === 'active' ? `#/code/${c.id}` : `#/record/${c.id}`}>
              <span className="mono muted">{new Date(c.created_at).toLocaleString()}</span>
              <span>
                {c.mode === 'replay' ? `Replay · ${c.scenario}` : 'Live code'} {c.outcome ? `· ${c.outcome}` : ''}
              </span>
              <span className={`pill ${c.status === 'active' ? 'bad' : ''}`}>{c.status === 'active' ? 'running' : 'record'}</span>
            </a>
          ))}
        </section>
      )}

      <p className="faint" style={{ fontSize: 14, margin: 0 }}>
        CodeLoop records and keeps time. It never recommends treatment; the team leader decides. Not a medical device;
        for simulation and training.
      </p>
    </div>
  )
}
