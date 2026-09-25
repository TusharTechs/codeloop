# Competitor analysis — batch 3 (submissions.txt lines 79–118, 40 projects)

AssemblyAI Voice Agent Hackathon 2026 (lablab.ai). Collected 2026-09-25.

**Method.** I curl-fetched all 40 lablab pages and parsed the description, tags, date, likes counter and links. I shallow-cloned all 40 GitHub repos. For each repo I counted code lines (py/ts/tsx/js/mjs/html, node_modules excluded) and test files, and grepped for AssemblyAI endpoints to see which API each project actually calls:
- `agents.assemblyai.com/v1/ws` = Voice Agent API (VA)
- `streaming.assemblyai.com/v3/ws` = Universal-Streaming v3 (STREAM)
- `api.assemblyai.com/v2/realtime` = old v2 realtime
- SDK `Transcriber().transcribe` / `v2/transcript` = async STT only
- `llm-gateway.assemblyai.com` = LLM Gateway (GW)

I also HTTP-checked the demo URLs. All returned 200 except Uh-Huh and CrewVoice, which timed out at 25 s. Both are on Render, so this is probably a free-tier cold start; not verified further.

**Limits.** I did not watch the videos or read the slide PDFs. For the 12 strongest projects I read the README, file tree and key code. Where a claim comes only from the lablab description (benchmark numbers, test counts, latency), I mark it "(claimed)". The "Likes" column is the counter shown on each lablab page. Every project in this batch shows 0 or 1, so it tells us nothing about ranking.

**Ratings.** Tech = technical depth, Orig = originality, Polish = polish and demo quality, Threat = threat to win #1. All are scored 1–5.

## 1. All projects

| # | Project | Category | What it does (target user) | AssemblyAI tech actually used | Tools/actions | Safety / verification layer | Deliverables | Likes | Repo size | Tech | Orig | Polish | Threat | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Aalto | personal assistant (browser agent) | Chrome side-panel voice agent that acts on the current page: Q&A, dictation, rewrite in place, multi-field form fill, tab control. For support, ops and sales staff, and people who find typing hard. | VA (the whole loop). A Cloudflare Worker mints single-use tokens. | 18 browser tools plus `get_context` (claimed) | Code-enforced: won't submit a form it hasn't read back; won't guess options | Video, slides, GitHub, live site with in-page sandbox browser | 1 | ~8.8k LOC | 4 | 4 | 4 | 4 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/aalto/aalto-talk-to-your-browser |
| 2 | VoicePulse AI | customer support (QA analytics) | Generic FastAPI "speech QA / sentiment / compliance" platform | STREAM (small) | None real | JWT auth only | Video, slides, GitHub, Vercel | 0 | ~0.6k LOC | 1 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/dropsnipper/voicepulse-ai-real-time-voice-qa-and-speech |
| 3 | Voice Task Assistant | personal assistant | Audio file → transcript → "remind me" intent → saved to JSON. Beginner solo project. | Async STT only | Save reminder | None | Video, slides, GitHub | 0 | 142 LOC | 1 | 1 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/echoagent/voice-task-assistant |
| 4 | **EvidenTurn** | evidence/claims/legal | Turns an out-of-order spoken consumer complaint into a reviewable draft. Every fact links to a final transcript turn; corrections stay visible; exports MD/JSON. | STREAM v3 (universal-3-5-pro) plus a deterministic engine. Explicitly not VA and no LLM. | None (intake only) | Readiness gate: required fields, evidence mention, confirmation, no unresolved conflicts or low-confidence warnings; text hashes. Very candid about its limits. | Video, slides, GitHub, hosted replay demo (no key needed) | 0 | ~4.3k LOC, 8 test files | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/evidenturn/evidenturn |
| 5 | **AegisVoice** | transaction/action safety gate (finance) | "Voice can request, security decides." Spoken transfer intent goes to a VA tool call, then a FastAPI Security Gateway (RBAC, beneficiary whitelist, limits, risk, policy) returns ALLOW, DENY or STEP_UP. For banks and corporate finance. | VA (browser WebSocket with a tools array). Backend mints a v3 streaming token. | Transfer tool → gateway | Deterministic policy and risk engine; audit log; mock executor | Video, slides, GitHub, Vercel | 0 | ~2.3k LOC, no tests | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/marksmanx/aegisvoice |
| 6 | **TRACE** | finance (SMB reconciliation) | Voice-native investigation agent for requests like "revenue is short ₦210k, investigate." Traces orders, invoices, POS and bank settlements; forms and tests hypotheses; separates evidence from inference; answers "prove it." | VA (turn detection, barge-in, tool calling) | ~13 tools, e.g. `search_records`, `trace_transaction`, `compare_records`, `get_evidence`, `flag_transaction`, `create_reconciliation_task`, `draft_customer_follow_up`, `verify_action` | Consequential actions behind a human-approval dialog | Video, slides, GitHub, Vercel | 0 | ~6.8k LOC, client-only Vite app, synthetic Nigerian dataset, 1 commit | 3 | 4 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/trace/trace-voice-native-business-investigation-agent |
| 7 | ARIA | personal assistant | Generic browser voice chat with an animated SVG "living orb" | VA | None | None | Video, slides, GitHub, Vercel | 1 | ~0.6k LOC | 2 | 1 | 3 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/code-warriors/aria-real-time-voice-ai-assistant |
| 8 | **Second Chair** | evidence/claims/legal (financial-advice compliance) | Multi-party room agent. A financial adviser is with a couple. Live diarized transcript; each turn is PII-redacted, then checked against a FINRA/SEC rule pack in <1 ms. Prohibited phrases trigger a private earpiece "whisper" with the regulation and a safe rephrase. The room channel speaks only when addressed by name. An LLM second tier catches omitted disclosures. Append-only audit record. | STREAM v3 with `speaker_labels` (streaming diarization), universal-3-5-pro, `format_turns`. Own orchestration; not VA. LLM via Groq/Claude. | Whisper vs. room output channels; audit writer | Rule pack (finra.yaml), guardrails, redaction, addressivity model, audit trail | Video, slides, GitHub, Next.js site with live console | 1 | ~6.4k LOC, 10 test files | 4 | 5 | 4 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/enigma-pro/second-chair |
| 9 | Playtest Pal | dev tools (game QA) | Game testers describe bugs by voice; the agent asks follow-ups and builds a structured bug report that separates what the tester said from what the agent inferred | VA plus a scripted sample mode | Report-update tools | Said-vs-inferred provenance; editable report | Video, slides, GitHub, live site | 1 | ~8k LOC | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/very-professional/playtest-pal |
| 10 | **sipa-voice-gate** | transaction/action safety gate | Repo: "voice agent that checks itself before it acts." Consequence gate, spoken consequence chain, then explicit yes, then a hash-chained receipt. **The lablab text describes a different thing:** "sipa-trace" TraceCards for AI-infra logs. Page and repo are inconsistent. | Async STT only (Python SDK `TranscriptionConfig` with `redact_pii`). The deck claims Universal-Streaming and LeMUR, but the code does batch transcription. The web demo takes **typed** transcripts. ElevenLabs TTS. | Mock actions (send money, delete, email) | Consequence classifier, confirm-before-act, hashed receipts plus verifier. 21–29 tests (claimed). | Video, slides, GitHub, site | 0 | ~1.9k LOC, 5 test files | 2 | 2 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/sipaos/sipa-voice-gate |
| 11 | MediVoice AI | healthcare (scheduling) | Patient voice booking: find a doctor, check availability, book, reschedule, cancel | VA + Node/Express + MongoDB | Appointment CRUD tools | Confirmation before cancel or reschedule; duplicate-booking checks | Video, slides, GitHub, Render | 0 | ~1.4k LOC | 2 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/medivoice-ai/medivoice-ai |
| 12 | **ClaimVoice** | evidence/claims (insurance FNOL) | "Ivy" takes a car-crash First Notice of Loss on the call: safety check first, then identity verification (policy number plus last 4 digits of phone; 4 misses locks the policy out). Asks about the actual insured car, files the claim, and a risk rule set decides whether to dispatch a tow. For insurers and roadside dispatchers. | VA with HTTP tool webhooks to Django. A `publish_agent` command pushes the prompt and voice to AssemblyAI. The same agent answers a Twilio number over SIP. | `verify_policyholder`, file-claim and tow tools; vendor calls; handoff | Identity verification with lockout and no policy-existence leak; idempotent filings; `not_asked` enum so the model can't invent drivability; redaction module | Video, slides, GitHub, Render live app with dispatcher board, stereo call recordings, insights page, simulator that fails if no claim lands | 0 | ~20k LOC (~11k Django Python), 3,015-line `tests.py` | 5 | 3 | 5 | **5** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/claimvoice/claimvoice-ai-claims-first-responder |
| 13 | AuraCommand | dev tools/SRE | Push-to-talk "voice ops" in Streamlit: cluster health, blue/green deploy, snapshots (simulated) | Async STT only | Simulated ops | None | Video, slides, GitHub | 0 | 160 LOC (single `app.py`) | 1 | 2 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/auracommand/auracommand-autonomous-voice-ops-agent |
| 14 | QuoteReady | receptionist/intake (trades) | Voice intake of 5 quote fields (work, equipment, location, access, timing). Draft with transcript evidence; a correction invalidates the review; caller approves before JSON download. | VA with client-side function tools. Netlify function mints tokens. | Field-fill tools | Evidence per answer; explicit unknown or refusal; re-approval after edits | Video, slides, GitHub, GitHub Pages sample (live app invite-code gated) | 0 | ~1.3k LOC, 6 test files | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/quoteready/quoteready |
| 15 | **Say Less** | dev tools (voice-agent reliability) | Fixes the "sentence reset." When a slot value falls outside the business catalog, it ranks valid candidates by Double Metaphone phonetic similarity and asks the smallest possible clarification ("Tuesday?", then "Tuesday or Thursday?", then "Which day?", then a human). | STREAM v3 plus LLM Gateway (binder) | Booking commit | Catalog-constrained commits: every offered candidate is a real, bookable value | Video, slides, GitHub, Render demo, eval harness | 1 | ~7.7k LOC, 15 test files | 4 | 4 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/aidlc/say-less-intelligent-voice-agent-repair-engine |
| 16 | VoxHire | interview coaching | Adaptive technical interviewer with an end-of-interview report | VA. The repo looks built on the AssemblyAI voice-agent starter (`agents/*.jsonc` templates, AGENTS.md) plus an `interview/` controller. | Interview state and report | None | Video, slides, GitHub, Render | 0 | ~4.5k LOC (mostly .mjs) | 2 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/ai-maxxers/voxhire-adaptive-ai-technical-interviewer |
| 17 | **Voice Order Support Agent** | customer support (e-commerce WISMO) | "Where's my order" voice agent: looks up orders first, puts tracking numbers on screen, starts returns, cancels, changes address | STREAM v3 (Universal-Streaming) + Groq gpt-oss-120b with a manual tool loop + Orpheus TTS. **Deliberately not VA**; builds its own turn-taking. | Order lookup, return, cancel, address change | State-changing tools gated in code (unknown tool, bad arguments, speculative turn, or missing confirmation stops the call); idempotent returns; never claims an unreported success. Memory keeps only the words the user actually heard. | Video, slides, GitHub, Replit live app with a per-turn latency waterfall | 0 | ~10k LOC, 25 test files (288 tests claimed) | 5 | 3 | 4 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voice-order-support-agent/voice-order-support-agent-interrupt-it-any-time |
| 18 | **WalkAround** | field ops / inspection (industrial safety) | Turns any checklist into a voice inspection, e.g. a truck DVIR, restaurant opening or lab procedure. "Oil's good." "Left front steer tire is down to eighty." Each verdict becomes a tool call. Interruptible, jumps between sections, revises earlier items. Final report with exact words, timestamps and work orders. | VA (Universal-3.5 Pro, keyterms, semantic turn detection, JSON-Schema tools, native TTS) plus **LLM Gateway**, which compiles a pasted checklist into a template | Per-item verdict tools; `session.update` swaps tools and prompt each section ("progressive tool reveal") | Checklist state machine: can't skip required items or file before all are resolved; out-of-service explicitly preserved | Video, slides, GitHub, Vercel, scripted no-mic walkthrough, PDF reports | 0 | ~5.1k LOC; engine and live-integration tests (28 claimed) | 4 | 4 | 4 | **4–5** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/sgy/walkaround-voice-inspection-agent |
| 19 | **Earshot** | robotics / physical-agent supervision | Voice supervision layer for autonomous agents and robots. "Stop" is caught on partial transcripts and halts the agent in about 300 ms (claimed). The rest of the sentence becomes a skill. Corrections are logged with 2 s of prior state and distilled by an LLM into versioned policy rules. Demo: a 3D gantry gripper packs 4 objects; run 1 needs 4 corrections, run 2 needs 0. | STREAM v3 (partials, keyterm biasing, turn detection, temp tokens, multilingual) plus an OpenAI-compatible LLM. Not VA. | Skill execution (maps to a ROS action server) | Traceable rule provenance (each rule points back to the sentence) | Video, slides, GitHub (strong README and hero), Vercel live 3D demo with a metrics tab | 1 | ~15.4k LOC, 6 test files | 4 | 5 | 5 | **5** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/degens-unite/earshot |
| 20 | Voxrede | dev tools (voice-agent red-team eval) | Two VA sessions, a test caller and a support fixture, exchange paced audio. Scenarios: impersonation, spoken prompt injection, interruption, degraded channel. Archive of evidence showing false "success" claims. | VA ×2 | Mocked business tools | Separates digit mention from verified identity and tool request from execution; manifests and hashes | Video (older version), slides, GitHub, GitHub Pages walkthrough | 1 | ~6.4k LOC, 9 test files | 3 | 4 | 2 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voxrede/voxrede |
| 21 | **Uh-Huh** | field ops (trades / busy-handed workers) | The customer calls; the AI never talks to the customer. It whispers a short question in the worker's ear ("Sink job, Tue 3pm — good?"). The worker grunts "uh-huh," "nope" or "later," which becomes a booking card, an SMS to the customer in the worker's name, and a "money kept" counter. | STREAM v3 plus LLM Gateway. One-syllable lexicon classifier. | Booking card, SMS | Human always gives the yes; honest limits stated (English only, pre-recorded caller) | Video, slides, GitHub, Render (timed out during my check) | 0 | ~3.4k LOC, 7 test files | 3 | 5 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/gnomon/uh-huh-a-voice-agent-for-busy-handed-workers |
| 22 | SpokeUI | dev tools | Point at a UI element in your running app, hold Space and speak. DOM, style and context plus the transcript go to a local Codex or Claude Code run, which edits the repo. Before/after captures with accept or reject. | STREAM v3 (dictation only) | Coding-agent invocation | Accept/reject diff | Video, slides, GitHub, Vercel landing | 1 | ~3.8k LOC | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/kpsx-studio/spokeui-point-speak-ship-ui-changes |
| 23 | Clinic Scheduling Voice Agent | healthcare (scheduling) | Books a clinic slot by voice with read-back before booking | VA with HTTP tools to FastAPI on Cloud Run | Availability, booking | `BEGIN IMMEDIATE` transactional booking; explicit yes | Video, slides, GitHub, Cloud Run /docs | 0 | 324 LOC | 2 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/call-e-solo/clinic-scheduling-voice-agent |
| 24 | **PackCheck** | field ops / inventory | Voice count-check of a small order: the VA calls a deterministic checklist engine (item IDs, quantity limits, revisions), then undo, review, finalize and a JSON receipt | VA | Count, revise, undo, finalize | Tool-call-ID idempotency; rejected attempts don't overwrite; receipt verifier replays the final state with no AI | Video, slides, GitHub, GitHub Pages replay of real API evidence | 0 | ~0.7k LOC, 1 test file | 2 | 2 | 3 | 1–2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/packcheck/packcheck-every-count-accounted-for |
| 25 | TechSəs | customer support (IT help desk) | Voice IT help desk for Wi-Fi, printer, Windows and account issues, producing escalation ticket drafts | VA | Ticket summary | None notable | Video, slides, GitHub, Vercel | 1 | ~14.7k LOC | 2 | 1 | 3 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/omar-solo-voice-ai/techses-voice-it-help-desk |
| 26 | Meeting Shadow Agent | other (meeting copilot / commitment guard) | Helps non-native engineers on English client calls. Suggests replies that agree only within a pre-written authority memo and defer otherwise. | STREAM v3 (tab audio sent straight from the browser) plus Gemini Flash-Lite | Reply suggestions | Refuses replies that cite an utterance ID nobody spoke; measured eval (20 cases) | Video (simulated call), slides, GitHub, replay demo | 0 | ~3.7k LOC | 3 | 4 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/meeting-shadow-agent/meeting-shadow-agent |
| 27 | OmniDesk | receptionist/front desk | Multi-tenant voice receptionist: pricing Q&A, availability, atomic booking, .ics email invite, embeddable via script tag or npm package | VA with keyterms | `get_today`, `check_availability`, `book_appointment` | Atomic slot lock | Video, slides, GitHub, Vercel | 0 | ~18.9k LOC, no tests | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/dot/omnidesk-real-time-voice-agent |
| 28 | EduVoice / AutoCopilot | field ops (fleet diagnostics) | Hands-free truck fault diagnosis from DTC codes, synthetic CAN telemetry and work orders. Title and content don't match. | Old v2 realtime endpoint; claims LeMUR | Work-order dispatch | Inflated claims (e.g. "ISO 26262-compliant", "100% benchmark") | Video, slides, GitHub, Firebase | 0 | ~45k LOC (looks largely generated) | 2 | 2 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/phantom-grid/eduvoice-copilotautocopilot |
| 29 | NovelOS | other (creative writing) | Dictate scenes, auto-extract a story knowledge graph (characters, plot threads, secrets), plus a continuity "story debugger" | Async STT (dictation) plus OpenAI. Not really a voice agent. | None | Confidence and source per fact | Video, slides, GitHub, live site | 0 | ~21.7k LOC, 40 test files | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/team-kito/novelos |
| 30 | **CrewVoice** | field ops (construction timesheets) | A foreman reports "Jose worked nine hours." `record_hours` creates only a PENDING row; confirmed after read-back and yes. Out-of-crew names come back as candidate questions; accent-folded matching; English and Spanish; end-of-day "who wasn't mentioned." CSV has `heard_as` and `source_utterance`. | VA through a FastAPI bridge | `record_hours`, confirm, export | Rules in tools, not prompt (0–16 h bounds, over-day replacement check); audit columns | Video, slides, GitHub, Render (timed out during my check) | 0 | ~1.5k LOC, no tests | 3 | 3 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/khlab/crewvoice-spoken-timesheets-you-can-audit |
| 31 | NodeFlow | personal assistant / productivity (knowledge) | Tauri/Rust desktop app. Voice commands become graph operations on an Obsidian vault; routing between local and cloud LLMs; HITL proposal validation. | STREAM v3 | Graph operations (create, link, condense) | Server rejects invented IDs; human approval | Video, slides, GitHub, Vercel demo | 1 | ~55k LOC | 4 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voice-co-creator/nodeflow-hybrid-knowledge-orchestrator |
| 32 | HangON | receptionist/intake (ops/service desk) | Configurable voice intake with read-back. Confirmation is HMAC-signed and bound to the exact workspace, summary, route and idempotency key. | VA plus LLM Gateway | Create and route request | Signed confirmation; CSRF | Video, slides, GitHub, Vercel | 0 | ~4.6k LOC, 5 test files | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/openline/hangon-assemblyai-voice-front-desk |
| 33 | Deskpot Cat Nina | other (desktop companion) | Windows desktop pet cat that listens and responds in speech bubbles | Async STT | Commands | None | Video, slides, GitHub, site | 0 | ~6.5k LOC | 2 | 3 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/nina/deskpot-pet-cat-nina |
| 34 | SynapVocal | accessibility (dysarthric speech) | For people with dysarthria, ALS or CP: streams speech, Gemini listens to the audio plus context and proposes 3 interpretations, the user confirms, and Deepgram Aura speaks it. TORGO eval: 426/680 exact vs 324 for raw ASR (claimed). | STREAM v3 plus Gemini (audio) plus Deepgram TTS | Speak confirmed sentence | Confirm-before-speak | Video, slides, GitHub, live site | 0 | ~8.2k LOC, 5 test files | 4 | 4 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/ezi-edutech/synapvocal-realtime-voice-bridge |
| 35 | CatForge Voice Lab | robotics | Mandarin/English voice turns go to an editable command box and a deterministic planner over 5 robot-cat motion primitives, then a gate and explicit Run. Exports a ZIP with a SHA-256 manifest and replay verifier. | STREAM v3 | Motion execution | Typed contracts, motion-limit gate, portable verifier | Video, slides, GitHub, trycloudflare demo (ephemeral) | 0 | ~9.2k LOC, 14 test files | 3 | 3 | 2 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/microcat/catforge-voice-lab |
| 36 | **Benchback** | field ops (auto-repair core-deposit recovery) | A technician holding an old alternator talks to the agent. It matches job, invoice and purchase line, reads the supplier return policy, records evidence and drafts an inspection. Humans confirm the match, approve returns and post credits. Credit ledger reconciles partial credits ($240 deposit, $200 credit, $40 open). | VA with server-validated typed tools; Firebase Auth, Firestore, Cloud Run | Inspection draft, return packet, CSV credit import | Only humans confirm or post money; transactions prevent duplicate credits; reported observations kept separate from verified evidence | Video (plus YouTube), slides, GitHub with CI, live app with guest workspace | 0 | ~16.6k LOC, 5 test files | 4 | 5 | 4 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/benchback/benchback-from-parts-shelf-to-paid-back |
| 37 | **Tell** | healthcare (medication adherence) + verification gate | "Won't take yes for an answer." The agent can't write an adherence fact unless the answer sounded certain. The `record_adherence` tool is gated on acoustic hesitation (latency, filler duration, dead air and more: 8 signals combined noisy-OR against the same patient's baseline in the call). One re-ask, then accept and flag for a clinician. | **VA (24 kHz conversation) plus a parallel STREAM v3 socket (16 kHz)** for per-word timings and confidence. Holds `tool.result` until the measurement arrives, so there's no race. | `record_adherence` (gated) | Paralinguistic certainty gate; explicit "hesitation ≠ deception" framing; evidence doc; RAVDESS and synthetic eval, no clinical claim | Video, slides/deck, GitHub (architecture diagrams, evidence.md), GitHub Pages | 1 | ~3.2k LOC incl. tools, 2 test files (307-line gate test) | 4 | 5 | 4 | **5** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/qiqi/tell-it-wont-take-yes-for-an-answer |
| 38 | Code Talk | interview coaching | Voice-first coding interview simulator (Monaco editor, Claude interviewer, WPM and filler analytics) | STREAM v3 (plus async) | None | None | Video, slides, GitHub, Vercel | 0 | ~5.7k LOC | 3 | 2 | 3 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/team-nexus/code-talk |
| 39 | Recall Radar Voice | other (consumer product safety) | "Is anything I own recalled?" Checks live against CPSC, NHTSA and openFDA; reads back the evidence; walks through the remedy. Also exposes an MCP server (OAuth 2.0 + PKCE). | STREAM v3 plus a deterministic intent router (no LLM in the loop) | Inventory and recall lookup; MCP tools | Never says "recalled" without naming the agency record | Video, slides, GitHub, Vercel | 0 | ~1.5k LOC, 4 test files | 3 | 4 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recall-radar/recall-radar-voice-is-anything-i-own-recalled |
| 40 | ScamTrap AI | fraud/scam safety | Scam-baiting honeypot persona ("confused senior") that stalls scammers and extracts IOCs (mule accounts, URLs) to a dashboard | STREAM v3 plus OpenAI/Gemini TTS pipeline | IOC extraction | None | Video, slides, GitHub, Vercel | 0 | ~1.2k LOC | 2 | 3 | 2 | 1–2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/code-warrior/scamtrap-ai |

### AssemblyAI tech split (from code grep, not from descriptions)
| Tech | Count | Projects |
|---|---|---|
| Voice Agent API | 19 | Aalto, ARIA, AegisVoice, TRACE, Playtest Pal, MediVoice, ClaimVoice, QuoteReady, VoxHire, WalkAround, Voxrede, Clinic Scheduling, PackCheck, TechSəs, OmniDesk, CrewVoice, HangON, Benchback, Tell |
| Universal-Streaming v3 only (own orchestration) | 15 | EvidenTurn, Second Chair, Say Less, Voice Order Support, Earshot, Uh-Huh, SpokeUI, Meeting Shadow, NodeFlow, SynapVocal, CatForge, Code Talk, Recall Radar, ScamTrap, VoicePulse |
| Old v2 realtime | 1 | EduVoice/AutoCopilot |
| Async STT only | 5 | Voice Task Assistant, sipa-voice-gate, AuraCommand, NovelOS, Deskpot |
| Also use LLM Gateway | ≥5 | WalkAround, Say Less, Uh-Huh, HangON, Voice Order Support (grep hit; exact use not verified) |
| VA and Streaming together | 1 | **Tell** (the only true dual-socket design in this batch) |

## 2. Top threats in this batch

### Tell — "won't take yes for an answer" (Threat 5)
- **What it does:** A medication-adherence check-in agent. Its write tool is gated on *how* the patient said yes. It runs two AssemblyAI sockets on one mic: the Voice Agent API for the conversation and tools, and Streaming v3 for per-word timings and confidence. The gate withholds `tool.result` until the acoustic measurement arrives. It scores 8 hesitation signals against the patient's own baseline in the call. On a low score it tells the agent to ask a specific follow-up ("which days did you miss?"). After one re-ask it accepts and flags the case for a clinician.
- **Why judges might like it:**
  - It uses two AssemblyAI products together in a way that shows real understanding: turn boundaries come from the agent, not the silence-based STT.
  - The "aha" moment is crisp: "Uh… yeah" is refused at 44%; "I missed Tue/Wed" is recorded at 81%.
  - It sits on a clinically meaningful problem (self-reported adherence overstates reality).
  - The ethics framing is honest.
  - It ships a deck, architecture diagrams and an evidence doc.
- **Weaknesses:**
  - Small codebase (~3k LOC), few tests.
  - No clinical validation; the evaluation uses RAVDESS actors and synthetic speech.
  - Static GitHub Pages demo, so a live mic demo probably needs your own key.
  - A single use case.
  - Paralinguistic "certainty" is contestable.
- **How to differentiate:** Generalize "the gate reads the audio, not just the words" into a reusable layer across many tools and domains, validate on real speech, and show a live, keyless end-to-end demo. Don't do a hesitation gate for healthcare; that angle is taken.

### Earshot — voice supervision for robots and autonomous agents (Threat 5)
- **What it does:** An operator watches a simulated 3D gantry gripper and talks to it. "Stop" is detected on streaming partials and halts the robot in about 300 ms. The rest of the utterance becomes a skill, and corrections are distilled into versioned policy rules traceable to the sentence that produced them. Run 1 needs 4 corrections; run 2 needs 0.
- **Why judges might like it:**
  - A visually striking live 3D demo with a clear before/after metric.
  - Big-market framing (Waymo remote assistants, warehouse robots).
  - Creative use of partial transcripts and keyterms.
  - Excellent README and hero imagery; 15k LOC.
- **Weaknesses:**
  - Doesn't use the Voice Agent API; it's STT plus its own LLM.
  - Fully simulated, no real robot.
  - "Learning" is LLM rule distillation on a toy task with 4 hidden quirks.
- **How to differentiate:** Hard to beat on spectacle. Compete on real-world grounding (real users and data), a deeper use of the Voice Agent API, and a measurable safety or business outcome.

### ClaimVoice — insurance FNOL first responder (Threat 5)
- **What it does:** A complete insurer product built on the Voice Agent API with HTTP tool webhooks into Django:
  - identity verification with lockout
  - idempotent claim filing
  - a `not_asked` enum that stops invented facts
  - a tow-dispatch rule set
  - a dispatcher board, stereo recordings and an insights page
  - an agent-publishing command
  - Twilio SIP telephony
  - a conversation simulator that fails CI if no claim lands
- **Why judges might like it:**
  - The most "production-shaped" entry in the batch: roughly 11k lines of Python and about 3k lines of tests.
  - Uses the sponsor's newest features (Voice Agent API, HTTP tools, phone number).
  - Clear buyer.
  - Strong safety details.
- **Weaknesses:**
  - The domain (insurance claims intake) is a well-known voice-AI use case, so originality is only moderate.
  - It's a single Django monolith.
  - Not yet visible on votes.
- **How to differentiate:** Pick a less-obvious workflow, or match its production depth (telephony, simulator-backed tests, operator dashboard) while adding a novel verification mechanism.

### WalkAround — voice inspection checklists (Threat 4–5)
- **What it does:** Turns any written checklist into a voice-walked inspection (truck DVIR by default). The checklist is a state machine. Tools and prompts are swapped per section through `session.update` ("progressive tool reveal"), so the agent can't skip items or file early. The LLM Gateway compiles any pasted checklist into a template. Reports contain the inspector's exact words, timestamps and work orders.
- **Why judges might like it:**
  - Uses three AssemblyAI pieces (Voice Agent API, keyterms and semantic turn detection, LLM Gateway).
  - Its architecture idea (progressive tool reveal) is novel and easy to explain.
  - Generalizes across domains.
  - Has a scripted no-mic mode, PDF reports, and a live end-to-end test.
- **Weaknesses:**
  - "Voice checklist / hands-busy inspection" is crowded. In this batch alone: PackCheck, CrewVoice, Benchback, AutoCopilot. Other batches likely have more.
  - Modest codebase (~5k LOC) and 1 commit.
  - No field validation.
- **How to differentiate:** Avoid generic "voice forms" and checklists. If you go into field ops, add something WalkAround lacks, such as verification against external truth (photos or sensor readings), multi-party handoff, or real user data.

### Second Chair — multi-party compliance whisperer (Threat 4)
- **What it does:** Live diarized streaming in a three-plus-person room (a financial adviser with clients). A FINRA/SEC rule pack flags prohibited statements in under a millisecond and whispers a compliant rephrase to the adviser's earpiece only. A room channel speaks only when addressed by name (2 of 20 turns). An LLM second tier catches omissions. Audit records are free of personal identifiers.
- **Why judges might like it:**
  - Challenges a real assumption: voice agents assume two parties.
  - Makes strong use of streaming diarization.
  - Has a clear regulated-industry buyer and a polished Next.js site with a live console.
  - 10 test files.
- **Weaknesses:**
  - Doesn't use the Voice Agent API.
  - The rule pack is regex-like pattern matching.
  - Odd tags (Education, Dev Tools).
  - Real-time diarization in a noisy room is unproven.
- **How to differentiate:** Multi-party voice agents are a fresh angle that is still mostly open. Combine it with the Voice Agent API or with actions, not just monitoring.

**Honourable mentions (Threat 4):**
- **Benchback:** a very original niche (core-deposit recovery), polished Firebase app with CI and a guest workspace, strict human-only money actions.
- **Voice Order Support Agent:** the deepest engineering on turn-taking. It builds its own barge-in on the first partial word, keeps memory truncated to what the user actually heard, has a latency waterfall and 288 tests (claimed). It skips the Voice Agent API on purpose.
- **Aalto:** a Chrome agent with 18 tools on the Voice Agent API and a sandbox demo.

Next tier (Threat 3): Say Less (phonetic repair with a benchmark), Uh-Huh (the most original framing: the AI never talks to the customer), SynapVocal (accessibility with a TORGO eval), Recall Radar, TRACE, CrewVoice.

### Patterns worth noting for our strategy
1. **"Safety in code, not in the prompt" plus "confirm before act" is now table stakes.** At least 14 of 40 projects here claim it: Aalto, AegisVoice, sipa, EvidenTurn, QuoteReady, PackCheck, CrewVoice, HangON, Benchback, Voice Order Support, ClaimVoice, Tell, WalkAround, CatForge. The lablab sidebar also showed READBACK, Tally, AeroGuard and Guard Line from other batches doing the same. A plain transaction or action gate will not stand out.
2. **Honesty and evidence-heavy write-ups are common** (EvidenTurn, PackCheck, QuoteReady, Voxrede, Meeting Shadow). Several look like the same AI-assisted writing style: heavy caveats, "synthetic audio," "not field-tested." This can come across as unfinished. Real users or real data would stand out.
3. **The strongest entries combine several AssemblyAI products in a way that is essential to the idea:** Tell (VA plus Streaming), WalkAround (VA plus LLM Gateway plus `session.update`), ClaimVoice (VA plus HTTP tools plus phone). About half the batch uses only STT.
4. **Crowded categories:** field ops and hands-busy capture (6), dev tools (5), receptionist and scheduling (3 plus 2 healthcare scheduling), customer support (3).

## 3. Category counts (primary category, 40 projects)

| Category | Count | Projects |
|---|---|---|
| field ops / inventory / logistics / inspection | 6 | WalkAround, Uh-Huh, PackCheck, CrewVoice, Benchback, AutoCopilot |
| dev tools / SRE / voice-agent eval | 5 | Playtest Pal, AuraCommand, Say Less, Voxrede, SpokeUI |
| personal assistant / productivity | 4 | Aalto, Voice Task Assistant, ARIA, NodeFlow |
| other | 4 | Meeting Shadow (meeting copilot), NovelOS (writing), Deskpot (companion), Recall Radar (consumer safety) |
| customer support | 3 | VoicePulse, Voice Order Support, TechSəs |
| receptionist / front desk / intake | 3 | QuoteReady, OmniDesk, HangON |
| healthcare | 3 | MediVoice, Clinic Scheduling, Tell |
| evidence / claims / legal / compliance | 3 | EvidenTurn, ClaimVoice, Second Chair |
| transaction / action safety gate | 2 | AegisVoice, sipa-voice-gate |
| interview coaching | 2 | VoxHire, Code Talk |
| robotics / physical agents | 2 | Earshot, CatForge |
| finance | 1 | TRACE |
| accessibility | 1 | SynapVocal |
| fraud / scam safety | 1 | ScamTrap |
| education / tutoring, sales, agriculture, emergency | 0 | — |

**Unverified items:**
- Test counts, latency and benchmark figures quoted from descriptions.
- Whether Uh-Huh and CrewVoice demos work once the Render instance wakes up.
- Video and slide contents (not watched).
- Exactly how the LLM Gateway is used in grep-hit repos.
- The mismatch between sipa-voice-gate's lablab text and its repo.
