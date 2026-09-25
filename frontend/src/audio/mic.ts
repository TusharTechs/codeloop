// Microphone → PCM16 mono 16 kHz in 100 ms frames, via an AudioWorklet.
// Echo cancellation stays on so CodeLoop's own voice (played by this page) is removed from
// the room mic; the server additionally drops anything that matches what CodeLoop just said.

const WORKLET = `
class Pcm16Capture extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / 16000;
    this.buf = new Int16Array(1600);
    this.n = 0;
    this.acc = 0;
    this.accN = 0;
    this.pos = 0;
    this.sumSq = 0;
    this.peakN = 0;
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      // Box-filter downsample to 16 kHz (the context usually already runs at 16 kHz).
      this.acc += ch[i]; this.accN++; this.pos += 1;
      if (this.pos >= this.ratio) {
        this.pos -= this.ratio;
        const v = Math.max(-1, Math.min(1, this.acc / this.accN));
        this.acc = 0; this.accN = 0;
        this.buf[this.n++] = v < 0 ? v * 0x8000 : v * 0x7fff;
        this.sumSq += v * v; this.peakN++;
        if (this.n === 1600) {
          const out = this.buf;
          this.port.postMessage({ pcm: out.buffer, rms: Math.sqrt(this.sumSq / this.peakN) }, [out.buffer]);
          this.buf = new Int16Array(1600); this.n = 0; this.sumSq = 0; this.peakN = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor('pcm16-capture', Pcm16Capture);
`

export type MicChunk = { pcm: ArrayBuffer; rms: number }

export class MicCapture {
  private ctx: AudioContext | null = null
  private stream: MediaStream | null = null
  private node: AudioWorkletNode | null = null

  async start(onChunk: (c: MicChunk) => void): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('This browser cannot capture audio. Use Chrome, Edge, Safari or Firefox over HTTPS.')
    }
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: false, autoGainControl: true },
    })
    try {
      this.ctx = new AudioContext({ sampleRate: 16000 })
    } catch {
      this.ctx = new AudioContext() // the worklet downsamples
    }
    const url = URL.createObjectURL(new Blob([WORKLET], { type: 'application/javascript' }))
    await this.ctx.audioWorklet.addModule(url)
    URL.revokeObjectURL(url)
    const src = this.ctx.createMediaStreamSource(this.stream)
    this.node = new AudioWorkletNode(this.ctx, 'pcm16-capture')
    this.node.port.onmessage = (e: MessageEvent<MicChunk>) => onChunk(e.data)
    src.connect(this.node)
  }

  stop(): void {
    this.node?.disconnect()
    this.stream?.getTracks().forEach((t) => t.stop())
    void this.ctx?.close()
    this.node = null
    this.stream = null
    this.ctx = null
  }
}
