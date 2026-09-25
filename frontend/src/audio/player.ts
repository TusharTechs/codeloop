// Gapless PCM16 playback on two channels: CodeLoop's voice (24 kHz) and replayed room audio
// (16 kHz). The voice channel can be flushed instantly when a clinician talks over CodeLoop.

type Channel = 'voice' | 'room'

export class PcmPlayer {
  private ctx: AudioContext | null = null
  private gains: Partial<Record<Channel, GainNode>> = {}
  private next: Record<Channel, number> = { voice: 0, room: 0 }
  private live: Record<Channel, Set<AudioBufferSourceNode>> = { voice: new Set(), room: new Set() }
  private volume: Record<Channel, number> = { voice: 1, room: 0.8 }
  onVoiceActivity: ((speaking: boolean) => void) | null = null

  /** Must be called from a user gesture (browsers block audio until then). */
  async resume(): Promise<void> {
    if (!this.ctx) {
      this.ctx = new AudioContext()
      for (const ch of ['voice', 'room'] as Channel[]) {
        const g = this.ctx.createGain()
        g.gain.value = this.volume[ch]
        g.connect(this.ctx.destination)
        this.gains[ch] = g
      }
    }
    if (this.ctx.state === 'suspended') await this.ctx.resume()
  }

  get ready(): boolean {
    return !!this.ctx && this.ctx.state === 'running'
  }

  play(channel: Channel, pcm: ArrayBuffer, rate: number): void {
    const ctx = this.ctx
    const gain = this.gains[channel]
    if (!ctx || !gain || ctx.state !== 'running' || pcm.byteLength < 2) return
    const ints = new Int16Array(pcm)
    const buf = ctx.createBuffer(1, ints.length, rate)
    const data = buf.getChannelData(0)
    for (let i = 0; i < ints.length; i++) data[i] = ints[i] / 0x8000
    const src = ctx.createBufferSource()
    src.buffer = buf
    src.connect(gain)
    const lead = channel === 'room' ? 0.25 : 0.05 // small jitter buffer
    const at = Math.max(ctx.currentTime + lead, this.next[channel])
    src.start(at)
    this.next[channel] = at + buf.duration
    this.live[channel].add(src)
    if (channel === 'voice') this.onVoiceActivity?.(true)
    src.onended = () => {
      this.live[channel].delete(src)
      if (channel === 'voice' && this.live.voice.size === 0) this.onVoiceActivity?.(false)
    }
  }

  flush(channel: Channel): void {
    for (const s of this.live[channel]) {
      try {
        s.stop()
      } catch {
        /* already stopped */
      }
    }
    this.live[channel].clear()
    this.next[channel] = 0
    if (channel === 'voice') this.onVoiceActivity?.(false)
  }

  setVolume(channel: Channel, v: number): void {
    this.volume[channel] = v
    const g = this.gains[channel]
    if (g && this.ctx) g.gain.setTargetAtTime(v, this.ctx.currentTime, 0.02)
  }

  close(): void {
    this.flush('voice')
    this.flush('room')
    void this.ctx?.close()
    this.ctx = null
    this.gains = {}
  }
}
