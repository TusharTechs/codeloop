# CodeLoop

Voice agent that acts as the recorder at an in-hospital cardiac arrest: it listens to the
whole resuscitation team, logs drugs/shocks/rhythms with the exact words heard, runs the
ACLS clock deterministically, and flags spoken orders that were never closed-loop.

## Commit rules (mandatory)
- Author every commit as `Tushar Agarwal <tusharaggarwal274@gmail.com>` (repo-local git config is set).
- Never add `Co-Authored-By` trailers, "Generated with Claude Code", or any AI/agent attribution to commits or PRs.
- Commit directly on `main`.

## Layout
- `backend/` — Python 3.13, uv, FastAPI orchestrator (`src/codeloop/`), pytest tests.
- `frontend/` — Vite + React + TypeScript crash-cart UI.
- `eval/` — scenario YAMLs, synthetic mock-code audio generator, evaluation harness.
- `spikes/` — standalone scripts that probe live AssemblyAI behaviour.
- `docs/` — architecture, safety case, research notes.

## Principles
- The LLM only proposes events and must quote the transcript verbatim; deterministic code
  (ACLS engine + loop ledger) owns every timer, state transition and spoken number.
- Low ASR confidence never silently becomes a fact (UNCONFIRMED).
- Be explicit in docs about what is real vs simulated.

## Commands
- Backend tests: `cd backend && uv run pytest`
- Lint: `cd backend && uv run ruff check .`
- Synthesize eval audio: `uv run --project backend python eval/synth.py --all`
