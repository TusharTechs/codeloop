import { useCallback, useEffect, useReducer, useRef } from 'react'
import { socketUrl } from './api'
import { PcmPlayer } from './audio/player'
import { initialView, reduce } from './state'
import type { Control, ServerMsg } from './types'

const ROOM_AUDIO = 1
const AGENT_AUDIO = 2

/** One screen's connection to a running code: state, controls, and audio in/out. */
export function useCodeSocket(codeId: string, player: PcmPlayer) {
  const [view, dispatch] = useReducer(reduce, initialView)
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Each run of this effect owns its socket; a cleanup must never trigger a reconnect.
    let cancelled = false
    let retry = 0
    let timer: number | undefined

    const connect = () => {
      if (cancelled) return
      const sock = new WebSocket(socketUrl(codeId))
      sock.binaryType = 'arraybuffer'
      ws.current = sock
      sock.onopen = () => {
        retry = 0
        dispatch({ type: 'socket', connected: true })
      }
      sock.onmessage = (e) => {
        if (cancelled) return
        if (e.data instanceof ArrayBuffer) {
          const kind = new Uint8Array(e.data, 0, 1)[0]
          const pcm = e.data.slice(1)
          if (kind === AGENT_AUDIO) player.play('voice', pcm, 24000)
          else if (kind === ROOM_AUDIO) player.play('room', pcm, 16000)
          return
        }
        const msg = JSON.parse(e.data) as ServerMsg
        if (msg.type === 'agent_interrupted') player.flush('voice')
        dispatch({ type: 'msg', msg })
      }
      sock.onclose = (e) => {
        if (cancelled) return
        dispatch({ type: 'socket', connected: false })
        if (e.code === 4404 || e.code === 4401) {
          if (e.code === 4404) dispatch({ type: 'msg', msg: { type: 'closed', summary: {} } })
          if (e.code === 4401) dispatch({ type: 'msg', msg: { type: 'error', message: 'Access code required.' } })
          return
        }
        retry += 1
        timer = window.setTimeout(connect, Math.min(8000, 500 * 2 ** retry))
      }
    }
    connect()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
      ws.current?.close()
    }
  }, [codeId, player])

  const send = useCallback((c: Control) => {
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify(c))
  }, [])

  const sendAudio = useCallback((pcm: ArrayBuffer) => {
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(pcm)
  }, [])

  const dismiss = useCallback((id: string) => dispatch({ type: 'dismiss', id }), [])

  return { view, send, sendAudio, dismiss }
}
