# Evaluation results

How CodeLoop is measured, and what it scored. All audio is **synthetic**: macOS TTS voices
mixed with compressions, a monitor beep, an alarm, room tone and reverb (`eval/synth.py`,
"ward" profile). Treat these as engineering results on a small set of scripted mock codes,
not clinical validation.

- **Text eval** (`eval/run_text_eval.py`): scripted lines fed as perfect transcripts. This
  measures CodeLoop's own understanding, independent of speech recognition.
- **Live eval** (`eval/capture.py` → `eval/run_eval.py`): the scenario audio is streamed through
  AssemblyAI Universal-3.5 Pro with the exact production settings. The captured session is then
  replayed through the full pipeline (turn splitting → grammar → resolver → ACLS engine) at its
  original timing.

Scores: event precision / recall against each line's gold events, and **loop outcomes**
(did each order end in the right state; was each expected safety flag raised).

## Held-out protocol

The three `heldout_*` scenarios were written and committed (commit "Held-out evaluation
scenarios…") **after the grammar was frozen and before any measurement**. Their first scores are
reported below as the honest generalisation result. The grammar was then improved with *general*
rules (verb and noun pairs for CPR state, contractions, several actions in one sentence, "X, not Y"
corrections, bare completion callouts), not by copying their sentences. The "after" numbers on
these scenarios are therefore **no longer held-out**. A fresh held-out set is needed for the next
honest measurement.

| Held-out, first measurement (frozen grammar) | Precision | Recall | Loop outcomes |
|---|---|---|---|
| Text (perfect transcripts) | 1.00 | 0.80 | 6 / 8 |
| Live AssemblyAI | 0.97 | 0.71 | 5 / 8 |

| After general grammar rules (no longer held-out) | Precision | Recall | Loop outcomes |
|---|---|---|---|
| Text | 1.00 | 1.00 | 8 / 8 |
| Live AssemblyAI | 0.97 | 0.93 | 8 / 8 |

Precision held at 0.93 or above on every live capture. When CodeLoop is unsure, it misses an event
rather than inventing one, which is the right failure mode for a medical record.

## Held-out v2 (written after the v1 fixes, committed before measurement)

UK Resuscitation Council phrasing, lidocaine with a dose-less repeat order and an ignored shock,
and colloquial Hinglish with Hindi verbs and numbers.

| Held-out v2 | Precision | Recall | Loop outcomes |
|---|---|---|---|
| Text, first measurement | 0.81 | 0.71 | 7 / 9 |
| **Live AssemblyAI, first measurement** | **0.82** | **0.56** | **7 / 9** |
| Text, after general fixes (no longer held-out) | 0.98 | 0.98 | 9 / 9 |
| Live, after general fixes (no longer held-out) | 0.94 | 0.83 | 8 / 9 |

What the v2 set caught:
- **A safety bug introduced by the v1 fixes.** "Shock at one hundred and fifty joules" was
  split into two shock orders, 100 J and 50 J. Action splitting now never splits inside a
  number, and a unit alone is not an action. It has a regression test.
- "Going in" was read as "given". Hindi perfective and progressive verbs ("push kar diya",
  "charge ho raha hai") were not recognised. First-person leader statements and "check the
  rhythm" phrasing were also missed.
- **Remaining live misses are recognition errors.** "Two hundred joules" was heard as "100 joules",
  "Shock one fifty do" as "Drop 152", and "teen sau" as "team sorted". The grammar does not guess
  these. In a real code, the read-back loop is what catches a misheard energy.

## Live results, all captures (current grammar)

| Capture | Config | P | R | Outcomes | Event latency p50 / p90 |
|---|---|---|---|---|---|
| VF demo (English, 5 voices) | production (tight silence) | 0.97 | 0.91 | 3/3 | 1.4 s / 4.1 s |
| VF demo | default silence | 0.97 | 0.97 | 3/3 | 4.4 s / 7.9 s |
| VF demo | **bare** (no Medical Mode / keyterms / prompt) | 0.90 | 0.88 | **2/3** | 0.9 s / 4.5 s |
| Hinglish asystole (Hindi TTS voices) | production | 0.85 | 0.69 | 3/3 | 2.3 s / 5.2 s |
| Held-out Hinglish, natural | production | 1.00 | 1.00 | 3/3 | 1.5 s / 2.1 s |
| Held-out PEA | production | 1.00 | 0.92 | 2/2 | 1.3 s / 1.4 s |
| Held-out pulseless VT | production | 0.93 | 0.87 | 3/3 | 1.2 s / 1.5 s |
| Held-out v2 UK phrasing | production | 1.00 | 0.94 | 3/3 | 1.4 s / 3.6 s |
| Held-out v2 lidocaine | production | 0.91 | 0.83 | 2/3 | 1.3 s / 1.4 s |
| Held-out v2 colloquial Hinglish | production | 0.90 | 0.69 | 3/3 | 1.5 s / 2.0 s |

**AssemblyAI A/B:** on identical audio, critical entities (drug names, doses, energies, rhythms)
were transcribed correctly 96% of the time with Medical Mode + ACLS keyterms + context prompt,
versus 78% without them. Without them, the amiodarone read-back conflict is missed entirely.

## Reproduce

```bash
uv run --project backend python eval/synth.py --all --noise ward          # audio + gold (macOS)
uv run --project backend python eval/run_text_eval.py                      # perfect-transcript scores
uv run --project backend python eval/capture.py eval/audio/*.ward.wav      # live AssemblyAI captures
uv run --project backend python eval/run_eval.py spikes/results/streaming.*.product.raw.json
```
