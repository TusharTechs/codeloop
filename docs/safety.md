# CodeLoop safety case

CodeLoop listens to a resuscitation team and speaks during a cardiac arrest. A wrong word in
that room can hurt someone, so the design rests on one rule: **generative models may help
understand speech, but deterministic code decides every state, every timer, and every number
that is shown or spoken.** This document states what CodeLoop may and may not do, and what
happens when each part of the system is wrong.

CodeLoop is built for simulation and training first (see "Deployment stages"). It is not a
medical device and does not recommend treatment.

## What CodeLoop may do

- Transcribe the room and attribute speech to voices (AssemblyAI Universal-3.5 Pro streaming).
- Turn a statement into a structured event (order, read-back, completion, cancellation, rhythm,
  CPR state, role, question), **only with a verbatim quote** of the words it came from.
- Track each order through ordered → read back → given, and flag silence or disagreement.
- Keep the ACLS clock: 2-minute CPR cycles, the epinephrine 3–5 minute window, shock count, the
  amiodarone sequence.
- Speak a short reminder from a fixed list of sentences, and answer "CodeLoop, …" questions
  with sentences composed from its own record.

## What CodeLoop may not do

- Recommend a drug, dose, energy or intervention. Protocol reminders state timing only
  ("Epinephrine window open"), never what to give.
- Speak any number that did not come from the engine. Every spoken number is rendered from
  engine state by `engine/speech.py`. The Voice Agent is instructed to say our sentence word for
  word, and replies CodeLoop did not request are muted.
- End a code on its own. A heard "ROSC" or "call it" only pauses the timers; a human confirms.
- Write to an EHR. The record is for review and sign-off.
- Hear room audio through the Voice Agent. The agent receives silence, except while CodeLoop
  is speaking, when room audio is forwarded so a clinician can talk over it (barge-in).

## Where decisions are made

| Decision | Made by | Why |
|---|---|---|
| What words were said | AssemblyAI streaming (Medical Mode, ACLS keyterms, context prompt) | Best available medical ASR; word-level confidence exposed |
| Who said them | AssemblyAI word-level speaker labels, split per word (`aai/turns.py`) | Turn labels merge speakers in fast exchanges |
| Which event a sentence states | Deterministic grammar (`extract/grammar.py`); an optional LLM only as a second opinion | Auditable, testable, offline |
| Order vs read-back vs restatement | Deterministic resolver using who is speaking and what is open (`extract/resolve.py`) | Depends on state, not on language alone |
| Loop states, timers, flags, prompts | Deterministic engine (`engine/engine.py`), unit-tested, replayable | The safety-critical core |
| Spoken answers | Deterministic composer (`engine/answers.py`) | A managed LLM chose the wrong fact in testing |
| Ending the code, resolving a conflict | A human on screen | Irreversible or clinical judgement |

## Failure modes and responses

| Failure | Detection | Response |
|---|---|---|
| ASR mishears a dose word | Word confidence below 0.6 on value words | Event is kept but **UNCONFIRMED**; the loop shows "confirm value"; the record lists it under *needs review* |
| ASR mishears a read-back ("150" for "300") | Read-back value differs from the order | Loop becomes **CONFLICT**; red card with one-tap Confirm; CodeLoop says "Check dose. Ordered …, read back …" |
| Extractor misses an event | Evaluation recall; clinicians see the loop board | The screen shows only what was heard. A missed read-back leaves the loop amber, which errs toward a nudge rather than silence. Tap-to-log is always available |
| Extractor invents an event | Evaluation precision (≥ 0.93 live, 1.00 on text) | Events need a verbatim quote, a formulary drug and in-bounds values; out-of-bounds values are UNCONFIRMED |
| Two extractors disagree | Grammar and LLM candidates for the same drug differ in value | The event is UNCONFIRMED |
| Speaker labels are wrong | Word-level purity 0.5–0.7 on TTS voices | Loop logic relies on content cues first; speaker identity only breaks ties. Roles can be reassigned on screen |
| A bare "Delivered." could complete two orders | More than one open candidate | The completion is recorded as UNCONFIRMED |
| A garbled word is heard as "ROSC" | Seen in live testing | ROSC only pauses timers; CPR resuming re-activates the code and raises a flag; a human must confirm |
| CodeLoop hears its own voice | Utterance overlaps CodeLoop's speaking window and matches its words | Utterance logged as echo and ignored (tested: its "pause compressions" never pauses CPR) |
| CodeLoop talks over a clinician | Voice Agent semantic barge-in | Speech stops mid-word; the screen shows "Stopped: a clinician spoke over it" |
| A prompt comes too late to matter | Queued longer than its staleness limit | Dropped, not spoken; recorded in the audit log |
| Streaming socket drops | Socket close | Audio buffers up to 30 s; reconnect with backoff; timestamps rebased so the clock stays continuous; screen shows "reconnecting" |
| Voice Agent drops | Socket close | Session resumed within 30 s, otherwise a new one; the screen keeps working without voice |
| Server or network fails | Screen loses its socket | Screen reconnects and resyncs from the server's state; the paper record remains the fallback |
| Someone edits the record | SHA-256 hash chain over every audit entry | Record page shows "Record altered at entry N" |

## Human in the loop

- Prompt policy per team: screen only, timers only, or timers + loop nudges (default).
- Mute for two minutes with one tap.
- Every conflict and low-confidence value must be confirmed on screen before sign-off.
- Roles can be assigned to voices by tapping the speaker chip.
- A human confirms ROSC or termination; nothing ends the code automatically.

## Audit trail

Every utterance, event, loop transition, flag, spoken line, dropped line, answer and screen
control is appended to a hash-chained log (`store.py`). The Code Record is rebuilt from that
log alone (`record.py`), so what the screen showed and what the record says cannot diverge.
The record prints the chain status and head hash.

## Deployment stages

1. **Simulation and training (now).** Mock codes and debriefs: no patient data, no clinical
   reliance. Supported by the replay mode and the Code Record.
2. **Documentation assist.** Live codes, recorder nurse reviews and signs the record; CodeLoop
   is silent or timers-only. Requires hospital IT, consent and privacy review.
3. **Real-time assist.** Spoken loop nudges during live codes. Likely regulated as
   software-as-a-medical-device (FDA / CDSCO); requires clinical validation on real code audio.

## Known limitations

- All evaluation audio so far is synthetic TTS; real voices, accents, overlapping speech and
  real alarms will lower accuracy. The first milestone of a pilot is measuring on recorded mock
  codes in a simulation centre.
- The grammar covers adult ACLS phrasing in English and Hinglish; other phrasing will be
  missed (recall), not invented (precision), until added and tested.
- Diarization on a single far-field microphone is imperfect; a second microphone or
  per-role headsets would improve attribution.
