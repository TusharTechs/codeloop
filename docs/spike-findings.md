# Day-1 spike findings (25 Sep 2026)

All numbers come from live AssemblyAI sessions on **synthetic** mock-code audio: macOS TTS voices
(Indian English, British, Irish, Hindi) mixed with compressions, a monitor beep, an IEC-style alarm,
room tone and reverb (`eval/synth.py`, "ward" noise profile). Samples are small (one or two
scenarios per configuration). Treat them as engineering signals, not clinical validation. Real
human voices will behave differently. Re-run with `eval/run_eval.py` on new captures.

## 1. Universal-3.5 Pro streaming ("the ears")

| Configuration (same VF-arrest audio, 149 s, 5 speakers) | Critical entities* | Events P / R** | Loop outcomes** | Event latency p50 / p90 |
|---|---|---|---|---|
| Bare: diarization only, tight turn silence | 78% (18/23) | 0.90 / 0.88 | 2 / 3 (misses the dose conflict) | 0.9 s / 4.5 s |
| Full: + `domain=medical-v1`, ACLS keyterms, context prompt, far-field Voice Focus, default silence | — | 0.97 / 0.97 | 3 / 3 | 4.4 s / 7.9 s |
| **Full + tight turn silence (160 / 640 ms)**: chosen default | **96% (22/23)** | **0.97 / 0.91** | **3 / 3** | **1.4 s / 4.1 s** |

\* Drug names, doses, energies and rhythms transcribed correctly on the line that said them (spike metric).
\** Full product pipeline: turn splitting → grammar → resolver → ACLS engine, scored against scenario gold.

Findings:
- **Turns merge speakers.** With `speaker_labels=true`, a turn ends only after about 640–768 ms of
  silence, so fast back-and-forth becomes one turn with one majority label. **Word-level `speaker`
  labels are accurate**, so `aai/turns.py` splits every final turn wherever the word speaker changes.
- **Tight turn silence** (`min_turn_silence=160`, `max_turn_silence=640`) cuts latency by about 3× with
  no loss of loop outcomes.
- **Medical Mode + keyterms + prompt are load-bearing.** Without them, "amio one fifty" is
  misrecognised and the read-back conflict is never caught.
- **Critical-word confidence** on doses and drugs was high (p10 0.89, min 0.73). The 0.6 UNCONFIRMED
  threshold rarely fires on clean speech, which is what we want.
- **Word-level speaker purity is 0.52–0.69** on TTS voices. Loop logic therefore relies on *content*
  (order vs read-back vs completion cues) first, and on speaker identity only to break ties.
- **Hindi-accented English comes back in Devanagari** ("रिदम चेक, एसिस्टली है"). A phonetic
  cross-script layer (`extract/phonetic.py`) maps it back to the English vocabulary. Hinglish loop
  outcomes went from 1/3 to 3/3 and event recall from 0.31 to 0.62. Some Hindi-TTS lines were
  hallucinated outright ("पश्चिमी अफ्रीकी…"), so there was nothing to recover.
- **One mis-heard word ended a code.** A garbled line produced "ROSC". A heard ROSC or termination
  now pauses timers and waits for human confirmation. It never ends the code on its own.

## 2. Voice Agent API ("the voice")

| Test | Result |
|---|---|
| Engine prompt via `reply.create` "Say exactly: …" | Exact wording; **0.76–0.96 s** to first audio |
| Spoken English question | Transcribed correctly; `get_code_state` called; answer grounded in the tool result |
| Spoken Hinglish question (agent's own ASR) | Poor ("Cardioloog, last epi card dia taha"); no tool call |
| Barge-in: human talks over the agent | Reply interrupted mid-sentence; transcript trimmed to what was heard |
| Room chatter not addressed to CodeLoop | Agent generated a reply whose text was literally `<empty>` **and spoke ~1 s of audio** |
| Tool result with code time "00:52" | Read aloud as "twelve fifty-two AM" |

Design decisions:
- **Room audio never goes to the Voice Agent.** The streaming ears transcribe the room. Questions
  addressed to CodeLoop are sent to the agent as text (`conversation.message` + `reply.create`). Room
  audio is forwarded only while the agent is speaking, so its semantic barge-in still works.
- **Only solicited replies are played.** Any reply CodeLoop did not request is muted.
- **Tool results carry pre-rendered spoken strings** ("three minutes ten seconds ago, at code time
  zero fifty-two"), so the model never reformats a time or a dose.

## 3. LLM Gateway

- On this account, `claude-*`, `gemini-*` and `gpt-*` return *"Your account does not have access to
  this LLM Gateway model"*. `qwen3.5-4b-32k-fast` is available but rejects `response_format`.
- The deterministic grammar is therefore the primary extractor, and it runs with no network. LLM
  extraction is an optional second opinion (tool-calling schema), merged with the grammar output.
  When the two disagree on a value, the event is marked UNCONFIRMED.

## 4. Voice Agent API, redesigned path (spike 2b)

Questions were sent as text: `conversation.message(role=user)` then `reply.create`. Room audio was
forwarded to the agent only while it was speaking.

| Test | Result |
|---|---|
| Message + reply sent back-to-back | Agent never saw the question ("I am ready. Please proceed…") |
| Message, 0.5 s gap, reply | `get_code_state` called, but the answer used the **wrong fact** ("The last recorded rhythm is V-fib.") |
| Question carried in `reply.create` instructions | Tool called; the same wrong fact, for English, Hinglish and "what's due" |
| Barge-in with gated audio | Interrupted mid-sentence. The agent then answered the interruption ("Check the screen."), an unsolicited reply the client must mute |
| 20–60 s of silence | Never spoke unprompted |

**Decision: questions are answered deterministically.** The ears transcribe the question, and
`engine/answers.py` classifies it (last drug, what's due, shocks, rhythm, code time, roles) and builds
the sentence from engine state. The Voice Agent speaks it verbatim via `reply.create("Say exactly: …")`.
No generative model ever chooses a number that is spoken during a code. The Voice Agent API supplies
what it is best at: sub-second speech, turn-taking and semantic barge-in. Unrecognised questions get
"Check the screen."
