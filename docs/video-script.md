# Demo video (≤ 5 minutes)

**Goal:** within 30 seconds a judge should see CodeLoop catch something a busy team missed.
Every claim in the video must match what the README and `eval/RESULTS.md` say.

**Setup**
- A laptop running CodeLoop in Chrome (live mode), placed where a crash cart would be.
- Three people: **Leader**, **Meds nurse (Priya)** and **Compressor (Arjun)**. Optionally, a
  CPR manikin or a pillow for compressions. Sound effects are optional: play a monitor-beep
  loop quietly from a phone.
- Record the screen and the room together. OBS with the screen, plus a phone camera on the
  team, works well. Play CodeLoop's voice through the laptop speakers so the room hears it;
  CodeLoop ignores its own voice.
- Speak naturally. Don't slow down for the machine.

## Timeline

| Time | Picture | Audio / what happens | What it proves |
|---|---|---|---|
| 0:00–0:12 | Black, then a text card: "Filmed resuscitations: only 1 in 4 spoken orders was confirmed back." Then: "Confirmed orders were done 3.6× sooner. (El-Shafy 2018)" | Monitor beeps, compressions | The problem, with a real number |
| 0:12–0:20 | CodeLoop home page; click **Start live code** | "CodeLoop is the recorder at a cardiac arrest. It hears the whole team." (voice-over) | What it is |
| 0:20–0:35 | Team, with the screen side by side | **Leader:** "Code blue. Starting CPR now. I'm leading. Priya, you're on meds. Arjun, you're on compressions." The clock starts, the CPR ring counts down and roles appear | Hands-free start, speaker roles |
| 0:35–0:55 | Same | **Leader:** "Pause compressions. Rhythm check. That's V-fib. Charge to two hundred joules." **Arjun:** "Charging to two hundred. Everybody clear. Shock delivered." **Leader:** "Resume compressions." The shock loop goes ordered → read back → delivered, **closed loop** | Real-time structured events with quotes |
| 0:55–1:20 | Zoom on the open-orders board | **Leader:** "Give one milligram of epinephrine." Everyone keeps talking about IV access and nobody confirms. At 10 s the card turns **amber**; at 15 s **CodeLoop:** "Epinephrine one milligram ordered. Not acknowledged." **Priya:** "Sorry, epi one milligram, drawing up now … Epi's in." | **The catch**: something humans missed |
| 1:20–1:45 | Zoom on the card | **Leader:** "Amiodarone three hundred milligrams." **Priya:** "Amio one fifty, pushing." The card turns **red**; **CodeLoop:** "Check dose. Ordered amiodarone three hundred milligrams, read back one hundred fifty milligrams." **Leader** (cutting in): "No. Three hundred." CodeLoop stops mid-word. **Priya:** "Three hundred amio, pushing … amio's in." | Dose conflict caught; barge-in |
| 1:45–1:55 | Transcript panel | **Priya:** "CodeLoop, last epi kab diya tha?" **CodeLoop:** "Last epinephrine, one milligram, … ago." | Hindi–English; answers from the record |
| 1:55–2:10 | Cut to the clock near 1:45 (say "two minutes later" in the edit) | **CodeLoop:** "Fifteen seconds to rhythm check." … "Two minutes. Pause compressions for rhythm and pulse check." | The ACLS clock, out loud |
| 2:10–2:25 | Team, then the banner | **Leader:** "Hold compressions, pulse check. I've got a pulse. We have ROSC." The banner reads *"ROSC called. Timers are paused until someone confirms."*; tap **Confirm** | A human confirms the end |
| 2:25–2:45 | Code Record page | Scroll: closed-loop orders, 1 conflict caught, needs-review list, quoted timeline, "Record intact" with hash | The documentation nobody had to type |
| 2:45–3:20 | Architecture diagram (from `docs/architecture.md`) | "Two AssemblyAI connections. Universal-3.5 Pro streaming hears the room, with speaker labels, Medical Mode and ACLS keyterms. The Voice Agent API is CodeLoop's voice: it waits for a gap and stops when a clinician speaks. Between them, deterministic code decides every state, timer and number that is spoken. The model never picks a dose." | Application of technology |
| 3:20–3:50 | Results slide | "We tested on held-out mock codes committed before measuring. Fresh sets found real bugs, including one that turned 'one hundred and fifty joules' into two shocks. After general fixes: precision 0.96, recall 0.88, 16 of 17 loop outcomes. Medical Mode and keyterms raised drug and dose accuracy from 78 to 96 percent. Latency is about 1.2 seconds." | Honest evidence |
| 3:50–4:30 | Business slide | "The first customers are simulation centres and hospital resuscitation committees: every hospital runs mock codes and must review every real one. It costs about $2.66 in AssemblyAI usage per 30-minute code. Next come nurse-signed documentation and registry export, then real-time assist with clinical validation." | Business value |
| 4:30–5:00 | Team on camera, then the logo | "Codes are loud, fast and hands-full. CodeLoop is the recorder that never looks away. Every order heard. Every loop closed." | The memorable close |

## Fallback: no actors available

Use **Replay a mock code → VF arrest** and screen-record it with system audio. Keep the same
timeline and voice-over, and say on screen that the voices are synthetic: *"Mock code, synthetic
voices, streamed live through AssemblyAI."* This is honest, and the pipeline is fully real.

## Editing notes

- Show captions of what people say. The room audio is noisy by design.
- Keep CodeLoop's spoken lines audible; they are the product's voice.
- Add a small corner label: "Live AssemblyAI · no scripted UI".
- Keep it under 5:00 and export as MP4 (< 300 MB).
