import { useEffect, useRef, useState } from 'react'
import { getToken } from '../api'
import { MicCapture } from '../audio/mic'
import type { PcmPlayer } from '../audio/player'
import { Logo } from '../components/Logo'

type Line = { who: 'codeloop' | 'team' | 'tool' | 'note'; text: string; kind?: string }

/** Hands-free spoken debrief with CodeLoop after a mock code (AssemblyAI Voice Agent API). */
export function Debrief({ codeId, player }: { codeId: string; player: PcmPlayer }) {
  const [lines, setLines] = useState<Line[]>([])
  const [facts, setFacts] = useState<string[]>([])
  const [status, setStatus] = useState<'idle' | 'connecting' | 'live' | 'done' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<string | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const mic = useRef<MicCapture | null>(null)

  const stop = () => {
    mic.current?.stop()
    mic.current = null
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify({ type: 'end' }))
    ws.current?.close()
    ws.current = null
    player.flush('voice')
  }

  useEffect(() => () => stop(), []) // eslint-disable-line react-hooks/exhaustive-deps

  const start = async () => {
    setStatus('connecting')
    setError(null)
    setLines([])
    setSummary(null)
    const m = new MicCapture()
    try {
      await player.resume()
      await m.start(({ pcm }) => {
        if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(pcm)
      })
    } catch (e) {
      m.stop()
      const denied = e instanceof DOMException && (e.name === 'NotAllowedError' || e.name === 'SecurityError')
      setError(denied ? 'CodeLoop needs microphone access for the spoken debrief. Allow the microphone and try again.' : e instanceof Error ? e.message : String(e))
      setStatus('error')
      return
    }
    mic.current = m
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const token = getToken()
    const sock = new WebSocket(`${proto}://${location.host}/ws/debrief/${codeId}${token ? `?token=${encodeURIComponent(token)}` : ''}`)
    sock.binaryType = 'arraybuffer'
    ws.current = sock
    sock.onmessage = (e) => {
      if (e.data instanceof ArrayBuffer) {
        player.play('voice', e.data.slice(1), 24000)
        return
      }
      const msg = JSON.parse(e.data)
      if (msg.type === 'debrief_ready') {
        setFacts(msg.facts)
        setStatus('live')
      } else if (msg.type === 'debrief_agent') setLines((l) => [...l, { who: 'codeloop', text: msg.text }])
      else if (msg.type === 'debrief_user') setLines((l) => [...l, { who: 'team', text: msg.text }])
      else if (msg.type === 'debrief_tool') setLines((l) => [...l, { who: 'tool', text: 'CodeLoop read the facts from the Code Record' }])
      else if (msg.type === 'debrief_note') setLines((l) => [...l, { who: 'note', text: msg.note, kind: msg.kind }])
      else if (msg.type === 'agent_interrupted') player.flush('voice')
      else if (msg.type === 'debrief_done') {
        setSummary(msg.summary)
        setStatus('done')
        window.setTimeout(stop, 8000)
      } else if (msg.type === 'error') {
        setError(msg.message)
        setStatus('error')
        stop()
      }
    }
    sock.onclose = (e) => {
      if (ws.current !== sock) return
      mic.current?.stop()
      mic.current = null
      ws.current = null
      if (e.code === 4404) setError('A spoken debrief is available once the code has ended.')
      else if (e.code === 4401) setError('Enter the access code on the home screen first.')
      setStatus((st) => (st === 'done' ? st : e.code >= 4000 ? 'error' : 'done'))
    }
  }

  const noteLabel: Record<string, string> = { went_well: 'Keep', to_change: 'Change', action_item: 'Action', system_issue: 'System issue' }

  return (
    <div className="record">
      <div className="brand">
        <Logo />
        <span className="name">Spoken debrief</span>
        <a className="btn small" href={`#/record/${codeId}`} style={{ marginLeft: 'auto' }}>
          Code Record
        </a>
      </div>
      <p className="muted" style={{ margin: 0 }}>
        A short, structured team debrief (Gather, Analyze, Summarize), hands-free. CodeLoop asks the questions and quotes facts
        from the Code Record. The lessons are the team's own words, saved to the record. It runs after the code, never during
        it.
      </p>
      {(status === 'idle' || status === 'error') && (
        <button className="btn primary big" onClick={start} style={{ justifySelf: 'start' }}>
          {status === 'error' ? 'Try again' : 'Start spoken debrief'}
        </button>
      )}
      {status === 'connecting' && <div className="muted">Connecting to CodeLoop's voice…</div>}
      {status === 'idle' && <div className="faint">Uses your microphone. Best with headphones, or one speaker in a quiet room.</div>}
      {(status === 'live' || status === 'done') && (
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span className={`pill ${status === 'live' ? 'voice' : 'ok'}`}>{status === 'live' ? 'Listening · speak normally' : 'Debrief complete'}</span>
          {status === 'live' && (
            <button className="btn small" onClick={() => { stop(); setStatus('done') }}>
              End debrief
            </button>
          )}
        </div>
      )}
      {error && <div className="notice bad">{error}</div>}
      <div className="grid2-debrief">
        <section className="panel">
          <h3>Conversation</h3>
          {lines.length === 0 && <div className="empty">CodeLoop will open the debrief.</div>}
          {lines.map((l, i) =>
            l.who === 'codeloop' ? (
              <div key={i} className="cl"><span className="badge">CodeLoop</span><span className="text">{l.text}</span></div>
            ) : l.who === 'team' ? (
              <div key={i} className="utt"><span className="who leader">team</span><span className="text">{l.text}</span></div>
            ) : l.who === 'note' ? (
              <div key={i} className="chip ack" style={{ justifySelf: 'start' }}>Saved · {noteLabel[l.kind ?? ''] ?? l.kind}: {l.text}</div>
            ) : (
              <div key={i} className="faint" style={{ fontSize: 13 }}>{l.text}</div>
            ),
          )}
          {summary && <div className="notice" style={{ background: 'var(--teal-bg)', color: 'var(--teal)' }}><b>Summary.</b> {summary}</div>}
        </section>
        <section className="panel">
          <h3>Facts CodeLoop may quote</h3>
          {facts.length === 0 && <div className="empty">Loaded from the Code Record when the debrief starts.</div>}
          <ul style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 6 }}>
            {facts.map((f, i) => (
              <li key={i} className="muted">{f}</li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
