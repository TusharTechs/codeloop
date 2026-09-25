# Competitor analysis, batch 4 (submissions.txt lines 119–157, plus Recall Radar and ScamTrap from lines 117–118)

AssemblyAI Voice Agent Hackathon 2026 (lablab.ai). Research date: 2026-09-25.

## How this was gathered
- Each lablab page was fetched with curl, and the embedded Next.js RSC payload was parsed for the full description, `repoLink`, `demoUrl`, `videoLink`, `presentationLink`, tech tags, `likes` (community votes) and member count.
- **8 pages returned lablab's 404 fallback**: DataWhisperer, Callout, VoiceDesk, Frontdesk.ai, SignalGuard, Miles, hyperas and SafeCall. For 5 of them the description is still in the payload, but no repo, video or demo links are exposed. These are probably drafts or unpublished submissions and **may go live before the Sept 30 deadline**. Unverified.
- All 32 public GitHub repos were partial-cloned. For each one I measured commit count and date span, source size (code files, excluding node_modules and lockfiles), test-file size, and which AssemblyAI endpoints the code actually calls:
  - `agents.assemblyai.com/v1/ws` = **Voice Agent API (VAA)**
  - `streaming.assemblyai.com/v3` = **Universal-Streaming (US)**
  - `api.assemblyai.com/v2/transcript` or SDK `transcribe` = **async STT**
  - `llm-gateway.assemblyai.com` = **LLM Gateway (LLMG)**
- For the strongest ~10 repos I read the README and the key source. Every live demo URL got an HTTP check. Render-hosted demos (Tally, Probe) timed out on a cold start. DockWitness on Vercel returned 429. I did not interact with any demo in a browser and did not watch any video. Those are unverified.
- Votes: every project in this batch has 0–1 lablab likes. Community voting gives no signal here.

Rating scale is 1–5. "Threat" means the threat to win #1.

## 1. All projects

| # | Project | Category | What it does (1 line) | AssemblyAI tech actually used (verified in code unless noted) | Tools/actions | Safety / verification layer | Deliverables (V=video, S=slides, G=GitHub, D=live demo) | Votes | Tech | Orig | Polish | THREAT | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Briefkeeper | other (creative-agency client intake / productivity) | Voice conversation fills a 7-field design brief, and each field cites an exact client quote | VAA (token + ws) | JSON tool updates to brief fields | Quote-match provenance; later speech resets approvals; malformed tool updates rejected | V S G D (demo gated by reviewer access code) | 0 | 2 | 2 | 3 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/briefkeeper/briefkeeper-from-conversation-to-clarity) |
| 2 | Wavelink Mobile | customer support | Telecom support portal where the "Maya" voice agent works a ticket live, with memory across calls | VAA | check network status, remote reset, confirm account | Confirms details before changes (prompt-level) | V S G D | 0 | 3 | 2 | 3 | 2 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/lazycat/wavelink-mobile-ai-voice-support-agent) |
| 3 | Heed | accessibility | Hands-free to-do manager for people with paralysis, ALS or Parkinson's | US v3, used in depth: `UpdateConfiguration` to lengthen silence mid-stream, `ForceEndpoint` via a switch, mid-stream keyterms, agent_context. LLM is Nemotron on Nebius | JSON task actions validated server-side | Deletes need a spoken yes; "undo that"; validation against the real list | V S G D (hosted demo is a replay; live mode is local only) | 0 | 4 | 4 | 3 | 3 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/heed/heed-the-voice-to-do-agent-that-waits-for-you) |
| 4 | Lia | personal assistant | Family agenda where spoken tasks become drafts | VAA (per description; the repo holds only zipped source, not inspected) | task drafts, calendar export | Exact-quote check vs. transcript; drafts never auto-save | V S G D | 0 | 2 | 2 | 2 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/lia-agente-da-familia/lia-give-your-mind-some-room) |
| 5 | Voice Market Agent | finance (crypto market copilot) | Telegram voice note in, TA indicators, chart and ElevenLabs voice reply out | async STT (u3.5-pro + keyterms); streaming also referenced | LLM (DeepSeek) function calling: price, RSI, BB, charts (Binance) | none | V S G D (Telegram bot) | 0 | 3 | 2 | 3 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voice-market-agent-vs/voice-market-agent) |
| 6 | Viva oral exam | education/tutoring | Mock viva voce examiner that presses on weak spots and gives a verdict | US v3 + custom browser turn controller; Web Speech TTS | none (LLM branching) | none | V S G D | 1 | 2 | 3 | 3 | 2 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/unstoppable/viva-your-oral-exam-with-a-real-voice-agent) |
| 7 | **VoiceRemitNG** | finance (remittance Q&A, Nigeria) | Voice questions routed to fee-compare, FX, send-now and checklist tools | US v3 (Python SDK) + upload STT | 4 local tools; **all rates and fees are hard-coded "illustrative mocks"** | none | V S G; **"demo" URL is the GitHub repo** (Streamlit, not hosted) | 0 | 2 | 2 | 2 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voiceremitng/voiceremitng) |
| 8 | **MediVoice Evidence-First Intake** | healthcare | Patient speaks symptoms; live transcript becomes structured intake fields and a clinician report | US v3, `universal-3-5-pro`, `domain: medical-v1` (Medical Mode) | none (no agent actions) | Source transcript stays visible; "not a diagnosis" framing. Evidence-first is a label here, not a gate | V S G D | 0 | 2 | 2 | 3 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/medivoice-team/medivoice-evidence-first-patient-intake) |
| 9 | ToneGap | other (voice-agent bias audit / QA) | Runs synthetic voices through a voice agent and reports interruption and outcome disparities | VAA session artifacts (per code docs refs) | harvests agent tool calls/transcripts | Pre-deployment "gate" with evidence packages | V S G D | 0 | 3 | 4 | 3 | 2 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/tonegap/tonegap) |
| 10 | **Rollcall** | healthcare admin (provider directory verification) + action safety gate | Agent calls 40 simulated doctor offices, verifies 5 facts, and writes corrections with an audio clip behind every cell | VAA on **both ends** of each call (agent + simulated receptionist), per-call keyterms + transcription_prompt, `tool.result is_error` as recovery instructions, temp tokens, reply.create | 7 JSON-schema tools; directory writes | **Write gate in code**: a value is written only if the heard words support it; hedges go to a human; no contradictions; 40/40 outcomes, 150/150 fields, 0 false writes vs. hidden truth | V S G D (+ sweep GIF, "answer a call yourself" live mode) | 1 | 5 | 5 | 5 | **5** | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/bug-bunny/rollcall) |
| 11 | AURA offline | personal assistant | "Offline" local agent with RAG and AMD ROCm | **US v3 cloud streaming**, which contradicts the "offline" claim | local file search, drafts | "explicit permission before modifications" (claimed) | V S G D | 0 | 2 | 2 | 2 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/0xkalkistrike/aura-offline-autonomous-voice-agent) |
| 12 | **Recount** | field ops/inventory | Voice stocktake ledger: counts stay drafts until confirmed; closeout separates a confirmed zero from an uncounted item | US v3 (keyterms, prompting); prerecorded neural read-back audio bank | ledger ops, export | Explicit confirmation; mismatched confirmation rejected; full export blocked while items are unresolved | V S G D | 0 | 3 | 3 | 3 | 2 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recount/recount-finish-the-stocktake) |
| 13 | **DockWitness** | field ops/logistics + evidence/claims | Freight receiving: receiver and driver speak, and code computes shortages and damage and records two-party agreement or dispute | US v3 (u3.5-pro, keyterms) **and** VAA (token + ws) | extraction to rules engine; Supabase writes | Deterministic rules engine; "silence is never consent"; photo-evidence gate; append-only trigger-enforced audit ledger; liability always NOT_DETERMINED | V S G D (demo 429 on check; GitHub release with deck/video) | 0 | 4 | 4 | 4 | 4 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/dockwitness/dockwitness-proof-before-the-truck-leaves) |
| 14 | Talkie | dev tools (website voice SDK) | `<talkie-assistant>` web component: visitors talk and the page acts (3D tour moves, map filters, booking form opens) | VAA with client-side tools | page-action tools | none notable | V S G D (3-person team, 49 commits) | 0 | 4 | 3 | 4 | 3 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voiceteam/talkie-websites-that-talk-back-and-take-action) |
| 15 | NeuralVoice | personal assistant | Streamlit voice Q&A with Gemini + pyttsx3 | AssemblyAI SDK (basic STT) + SpeechRecognition | none | none | V S G D | 1 | 1 | 1 | 2 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/neuralvoice/neuralvoice-ai-assistant) |
| 16 | Probe | interview (hiring screens) | One-way interview whose follow-up questions are built from the candidate's own words; delivery signals come from word timings | **VAA + US v3 at the same time** on one mic (US for word-level timings); asymmetric turn detection (2.2 s / 9 s) | question generation | LLM never sees the numbers; frozen verdict model; "a flag is a question, not a rejection"; 178 tests | V S G D (Render, cold) | 0 | 4 | 4 | 4 | 3 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/probe/probe) |
| 17 | CVoxPuzzle | other (career / CV builder) | Voice interview becomes JSON CV "puzzle pieces" | VAA (token + ws) | field edits | none | V S G D (repo has 4 files) | 1 | 2 | 2 | 3 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/techflow-al-momayaz/cvoxpuzzle-fastest-and-most-flexible-cv-builder) |
| 18 | Energy prediction | other (off-topic ML) | LightGBM energy forecast + SHAP | **None found in repo**; repo predates the hackathon (Aug 20) | n/a | n/a | V S G D | 0 | 1 | 1 | 2 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/smart-energy-squad/energy-consumption-prediction-and-recommend-system) |
| 19 | Melo | personal assistant (screen guide) | Description is an author bio. **Same repo and demo as #21 Aura screen** | **None found in repo** | n/a | n/a | V S G D | 1 | 1 | 2 | 1 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/velora/melo-your-screen-your-mission-your-ai-guide) |
| 20 | **ClauseCatcher** | evidence/legal (sales-call contract compliance) | Listens to a sales rep live and speaks the exact contract clause the moment they contradict it | US v3 (contract-seeded keyterms) + VAA (`reply.create` to speak the verbatim clause) + Gemini classifier | clause lookup | LLM returns only a verdict + clause ID, never text; timeout means "unclear", never an accusation; measured 14/14 caught, 0 false alarms; 151+42 tests | V S G D (Render, text-simulate mode, no mic needed) | 0 | 4 | 4 | 4 | 4 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/clausecatcher/clausecatcher) |
| 21 | Aura screen | personal assistant (screen guide) | Screen-share assistant that guides the user step by step | **None found in repo** (Lovable app) | none | user stays in control | V S G D | 0 | 2 | 2 | 2 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/gg/aura-ai-that-understands-your-screen-in-real-time) |
| 22 | Night Desk hotel | receptionist/front desk | After-hours hotel clerk: check availability, quote a rate, book | VAA | 3 tools | Won't state a price or room that inventory didn't return; needs an explicit yes + name to book | V S G D | 1 | 3 | 2 | 3 | 2 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/night-desk/night-desk-tajmahal-hotel) |
| 23 | **Legal-Voice** | evidence/legal (legal form filling) | Conversational multilingual legal form filler that outputs a PDF | **No AssemblyAI in code** (Whisper/OpenAI stack). **Repo dates from Oct–Dec 2025, before the hackathon** | form-field mapping | user reviews extracted fields | V S G D | 0 | 3 | 2 | 3 | 1 (eligibility risk) | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/ai-team/legal-voice-voice-legal-forms) |
| 24 | Runway Voice | finance (SMB cash-flow) | Ask about runway, overdue invoices or hiring scenarios over a 13-week cash model | async STT (SDK `speech_models=["universal"]`) | intent/scenario engine | none | V S G D (Streamlit) | 0 | 2 | 3 | 3 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/runway-voice/runway-voice-ask-your-cash-flow-anything) |
| 25 | **Boomerang** | dev tools | "Voice pager" for coding agents: brief by voice, the agent calls you back, a spoken "ship it" opens a PR | VAA (two orchestrated sessions: brief + agent-initiated callback) | `gh pr create`, retry/cancel | **Consent receipt** (utterance + transcript hash + timestamp) before any side effect; `decide()` is the only path to a PR | V S G D (demo is a replay of a recorded run) | 0 | 3 | 4 | 4 | 3 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/boomerang/boomerang-the-agent-that-calls-you-back) |
| 26 | Spparo | sales (real-estate lead qualification, Dubai) | Voice call qualifies a lead (name, buy/rent, area, AED budget, timeline) and scores it hot or nurture | US v3 + **LLM Gateway** | extraction | Deterministic fallback if the LLM is down | V S G D | 0 | 2 | 2 | 3 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/spparo/spparo-voice-agent) |
| 27 | **RouteProof** | field ops/logistics | Delivery rider reports a failed drop by voice; tool call makes a draft that dispatch approves | VAA (token + ws) | create-draft tool | Quote-in-transcript check; missing-facts gate blocks approval; human approval | V S G D | 0 | 3 | 3 | 3 | 2 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/routeproof/routeproof) |
| 28 | Echos | other (meeting/memo notes) | Record or upload, then transcript + summary + highlights + sentiment | async STT v2 (summarization, highlights, sentiment) | none | none | V S G D (single HTML file) | 0 | 1 | 1 | 2 | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/echos-ai/echos-ai-meeting-and-voice-memo-assistant) |
| 29 | **Tally** | transaction/action safety gate (voice-agent reliability infra) | Sits between a voice agent and its tool calls, checks each call against an independent STT stream, holds and re-asks on conflict, and turns every failure into a regression test | **VAA + an independent US v3 stream** | order tools (burger-ordering reference agent) | Fail-closed gate; scoped re-ask; spoken-drift correction; replayable failure cases; config promotion gated on a regression suite; single write path enforced by DB | V S G D (Render, cold on check) | 0 | 5 | 4 | 3 | 4 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/tally/tally-reliability-layer-for-voice-agents) |
| 30 | **AeroGuard** | industrial safety (airfield / ATC) | Monitors ground-control radio; catches hold-short vs. cross readback deviations; barge-in alarm; FAA Part 139 audit log | US v3 (keyterms) + **LLM Gateway** for audit logs | incursion engine on a 2D airport grid | Readback deviation engine (a rule check) | V S G D (GitHub Pages; built around a "1-click judge simulation") | 0 | 3 | 4 | 3 | 3 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/pilotsaver/aeroguard-autonomous-airfield-voice-interceptor) |
| 31 | **READBACK** | transaction/action safety gate (crypto signing) | Say what you think you're signing; a notary decodes the real calldata, compares with 27 rules, speaks the verdict; an on-chain Safe guard refuses unattested txs | VAA (intent via strict-schema tool call; the agent never sees the tx) | intent tool call; EIP-712 attestation | **On-chain enforcement** (ReadbackGuard.sol verified on Base Sepolia); Bybit-shaped attack reverted on the guarded Safe and succeeded on the control; 15/15 intents; 24/24 Foundry tests on a Base fork | V S G D (+ Remotion-made film, deck) | 0 | 5 | 5 | 5 | **5** | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/readback/readback) |
| 32 | DataWhisperer | unknown | **Page 404; no description available** | unverified | – | – | none visible | – | ? | ? | ? | 1 (unverified) | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/datawhisperer/datawhisperer) |
| 33 | Callout | accessibility / gaming (real-time squad translation) | Players speak their own language; teammates get short tactical callouts in theirs | US v3 u3.5-pro (Hinglish) + Groq Llama (description only) | "Agent, repeat/summary" | none | **Page 404**; no links exposed | – | 3 | 3 | ? | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/dimensions/callout) |
| 34 | VoiceDesk | receptionist/front desk (dental) | Books appointments by voice, syncs to Google Calendar, operator dashboard | VAA (description only) | availability, save details, book | No double booking | **Page 404**; no links exposed | – | 3 | 2 | ? | 2 (if published) | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/tasha404/voicedesk-ai-voice-front-desk) |
| 35 | Frontdesk.ai | receptionist/front desk | Open-source multi-tenant AI receptionist platform | **No AssemblyAI mentioned** (Groq Whisper + LiveKit + Fish Audio) | booking, routing, CRM | RLS multi-tenancy | **Page 404** | – | 3 | 2 | ? | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/closeloop-ai/frontdeskai) |
| 36 | SignalGuard | unknown (customer conversation) | **Page 404; no description** | unverified | – | – | none visible | – | ? | ? | ? | 1 (unverified) | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/siriguard/signalguard-customer-conversation-smart-agent) |
| 37 | Miles | interview coaching (pitch/negotiation sparring) | Adversarial full-duplex sparring partner that interrupts rambling and filler words | US + Rime TTS (description only) | none | none | **Page 404** | – | 3 | 3 | ? | 2 (if published) | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/prx/miles) |
| 38 | hyperas | unknown | **Page 404; team page short description is keyboard-mash ("asdasd…")** | – | – | – | none | – | ? | ? | ? | 1 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/codenova/hyperas) |
| 39 | SafeCall | customer support + privacy | Billing voice agent, then post-call U3.5 Pro PII redaction of **both transcript and audio**; LLM insights see only redacted text | VAA + async STT (PII audio redaction) + LLMG (description only) | account lookup, refund, update contact | PII redaction; original session deleted from AssemblyAI; audit trail | **Page 404** | – | 4 | 3 | ? | 2–3 (if published) | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/endpointing/safecall-privacy-first-ai-voice-agent) |
| X1 | **Recall Radar** (line 117) | other (consumer product-safety assistant) | "Is anything I own recalled?": checks items live against CPSC, NHTSA and openFDA and explains matches with evidence | US v3 (u3.5 Pro, formatted turns) with a **deterministic intent router (no LLM)**; also an MCP server (Streamable HTTP, OAuth 2.0 + PKCE) | recall lookups, remedy walkthrough, Amazon CSV import | Never says "recalled" without naming the agency record, number, date and matched words | V S G D (25 tests) | 0 | 4 | 4 | 4 | 3 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recall-radar/recall-radar-voice-is-anything-i-own-recalled) |
| X2 | **ScamTrap AI** (line 118) | fraud/scam safety | Voice honeypot ("Harold, 78") stalls scammers while an async engine extracts IOCs (mule accounts, URLs, callback numbers) to a dashboard | US v3 + OpenAI GPT-4o-mini + OpenAI TTS | IOC extraction | none (offensive/deception use; no consent/legal framing seen) | V S G D (Vercel; no tests; `__pycache__` committed) | 0 | 2 | 3 | 3 | 2 | [link](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/code-warrior/scamtrap-ai) |

### Repo evidence for the deeply inspected projects
| Project | Commits (dates) | Code size / test code | Notes from reading the code |
|---|---|---|---|
| READBACK | 11 (Sep 24, likely squashed) | ~200 KB / 33 KB, plus Solidity + Foundry | Monorepo: `packages/core` (decoder, 27 rules, EIP-712), `packages/provider` (EIP-1193 wrapper), `contracts/ReadbackGuard.sol`, live eval scripts, Remotion video source. Real Base Sepolia tx links in README. Measured design decisions: MultiSend false-positive fix using 81 real Base txs. Most complete and credible project in the batch |
| Tally | 19 (Sep 22–23) | ~1.06 MB / 479 KB | Very large codebase with PRD/ARCHITECTURE/DECISIONS/SECURITY docs, recorded AAI event fixtures, adversarial harness, DB triggers enforcing a single write path. Candidly lists limitations (first real-speech run had a 24.6% false-hold rate, then fixed). Burger-ordering demo is unglamorous |
| Rollcall | 23 (Sep 21–22) | ~300 KB / 21 KB | `lib/agent/gate.ts` and `voice-gate.ts` implement the write gate, with tests. 40 recorded simulated calls with mp3 clips per cell. Very judge-oriented README mapping each AAI feature to a file |
| ClauseCatcher | 20 (Sep 14–20) | ~855 KB / 251 KB | FastAPI + frontend; spike folders; honest notes ("keyterms gain never measured"; tool-calling path dropped as unreliable, so the voice agent is used only to speak) |
| DockWitness | **3** (Sep 23–25, bulk commits) | ~1.1 MB / 492 KB | Next.js + Supabase RLS + Playwright. Tagged GitHub release with video and deck. Tech tags suggest built with Antigravity; volume implies heavy AI generation |
| Boomerang | 12 (Sep 22) | ~56 KB / 0 | **Worker is "scripted-but-real"**: real git clone/branch/push and `gh pr create`, but the fix narrative is a fixed timeline, not an LLM coding agent (comment in `server/worker.ts`). The consent-receipt gate is real |
| Probe | 25 (Sep 16–18) | ~256 KB / 70 KB | Dual VAA + streaming connections confirmed in code (`speech_model=universal-3-5-pro`) |
| AeroGuard | 6 (all Sep 24) | ~275 KB incl. 1,740-line HTML | Python FastAPI; `runway_engine.py` (465 lines) with hard-coded ORD/HND scenarios; README's judge path is a simulation button. Readback deviation is a simple rule check |
| Recall Radar | 8 (Sep 14–15) | ~77 KB / 19 KB | Clean small Node server: `recalls.js`, `match.js`, `intent.js`, `mcp.js`, `auth.js` with fixtures from real agency APIs |
| Recount | 95 (Sep 18–22) | ~320 KB / 152 KB | Many diagnostics/maintenance patch scripts and a prerecorded read-back mp3 bank. Same distinctive writing style as Briefkeeper and Lia ("No customer outcomes are claimed", zipped source releases, reviewer access codes), so possibly the same AI-agent workflow or author |
| Heed | 3 (Sep 16) | ~115 KB / 12 KB | Confirmed US v3 token + ws; advanced streaming control messages |
| Talkie | 49 (Sep 19–24) | ~1.05 MB / 385 KB | 3-person team; web-component SDK + persona console + playground |

## 2. Top threats in this batch

### 1. READBACK (threat 5/5): voice read-back before crypto signing, enforced on-chain
- **What it does:** Before signing, the user says aloud what they think the transaction does. The AssemblyAI Voice Agent API turns that into a strict-schema intent and is deliberately never shown the transaction. A deterministic "notary" decodes the real calldata (including unpacked Safe MultiSend batches), checks addresses on Base, applies 27 named rules, and has the agent speak the verdict word for word. On a match it issues an EIP-712 attestation. `ReadbackGuard.sol`, a Safe guard contract, reverts any Safe transaction that lacks one.
- **Why judges will like it:**
  - It is tied to the $1.46B Bybit hack, a real event everyone remembers.
  - The proof is on a public chain: the same Bybit-shaped DELEGATECALL reverted on the guarded Safe and took over the unguarded control Safe.
  - It has hard numbers: 15/15 intents, 24/24 fork tests, 1.9–3.4 s latency, about $0.02 per readback.
  - The design is principled: the model only listens and code decides.
  - The deliverables are polished: live dApp, deck, and a Remotion-produced film.
- **Weaknesses:**
  - Crypto/Web3 is a niche audience, and some judges discount crypto.
  - Only about 38.7% of active Safes are fully decodable.
  - Voice use is thin: one utterance, then an intent. It uses VAA mostly as STT + extraction, not as a conversational agent.
  - Solo builder; 0 votes.
- **How to differentiate:** Make voice the core of the product rather than a front door. Use multi-turn, real-time conversation (barge-in, repair, confirmation) in a domain with a broader audience (payments, healthcare, field ops). Show a live, unscripted interaction, not just on-chain artifacts.

### 2. Rollcall (threat 5/5): an agent that phones provider offices and writes only what it heard
- **What it does:** Health-plan provider-directory verification, which US law requires every 90 days. One click dials 40 simulated offices on 6 parallel lines. Each call is VAA on both sides. Answers become JSON-schema tool calls, and a code-level write gate refuses unsupported values (for example, unheard digits or "I think so?"). Refusals go back to the agent as `is_error` tool results that tell it what to re-ask. Every cell plays the receptionist's own clip.
- **Why judges will like it:**
  - Real regulatory pain with a cited Senate "ghost network" study.
  - A visually striking sweep (GIF, register filling in).
  - Measured against hidden truth sheets: 40/40 outcomes, 150/150 fields, 0 false writes, about $0.08 per listing.
  - Uses many AAI features, each explicitly mapped to a file: keyterms + transcription_prompt per row, tool errors, temp tokens, reply.create.
  - The interactive "answer a call yourself" mode lets judges test it live.
- **Weaknesses:**
  - All offices are simulated, so agent talks to agent. Real IVRs, hold music and voicemail are untested.
  - Outbound telephony (Twilio) is not shown.
  - Narrow B2B buyer.
- **How to differentiate:** Put real humans and real audio in the loop (a live phone number, PSTN, noisy environments). Show outcomes that go beyond directory data. Address outbound-call compliance (disclosure is already done here, so you need more than that).

### 3. Tally (threat 4/5): a reliability and verification layer for any voice agent's tool calls
- **What it does:**
  - Runs an independent AssemblyAI streaming transcription beside the Voice Agent and validates every order-changing tool call against it.
  - Fails closed: holds on conflict or missing evidence, asks one scoped re-ask about just the disputed item, and corrects spoken drift.
  - Stores every caught failure as a replayable regression case, and config changes can't go live until the suite passes.
- **Why judges will like it:**
  - It is infrastructure that AssemblyAI itself would want, since it makes their Voice Agent trustworthy.
  - It has the deepest engineering in the batch: about 1 MB of code, adversarial harness, DB-enforced single write path.
  - It includes honest real-speech validation: 3 speakers, 36 recordings, bugs found and fixed.
- **Weaknesses:**
  - Burger ordering is a dull demo.
  - Complex to explain in a 3-minute video.
  - Render free tier timed out on the check.
  - First-run metrics were weak (24.6% false holds, then fixed).
  - It looks heavily Claude Code–generated; judges may sense over-documentation.
- **How to differentiate:** If you build a "safety gate", pick a high-stakes, emotionally legible domain and make the verification visible in real time in the UI. Keep the story to one sentence.

### 4. ClauseCatcher (threat 4/5): live contract-contradiction alerts on sales calls
- **What it does:** A contract PDF is split into verbatim clauses. The rep's speech streams through AssemblyAI streaming, seeded with keyterms from the contract. Each sentence is classified by Gemini, which returns only a verdict and a clause ID. On a contradiction, a Voice Agent session speaks the literal clause via `reply.create`.
- **Why judges will like it:**
  - Clear B2B value, with a market-size estimate.
  - Strict anti-hallucination design: the LLM never writes the words that are spoken.
  - Measured results: 14/14 caught, 0 false alarms, 4–6.5 s alerts, 190+ tests.
  - The live demo works without a mic.
- **Weaknesses:**
  - The voice agent is used only as a TTS mouthpiece. The author notes tool calling was unreliable and dropped.
  - 4–6.5 s latency is slow for live calls.
  - No Zoom or Meet integration.
  - Alerts play into the rep's own tab, not the call.
- **How to differentiate:** Use VAA's conversational and tool-calling capabilities in earnest, and get sub-2 s latency.

### 5. DockWitness (threat 4/5): freight receiving evidence before the truck leaves
- **What it does:** The receiver and driver speak at the dock. Streaming STT plus a VAA guide capture counts, damage and each party's position. Deterministic code computes discrepancies, enforces photo evidence and records CONFIRMED_BY_BOTH or DISPUTED. The ledger is append-only (Supabase triggers), and liability is never decided.
- **Why judges will like it:**
  - A concrete, physical operations problem with a crisp "golden demo" (48 expected, 47 counted, one crushed carton).
  - An "AI understands, code decides, humans judge" invariant.
  - Large tested codebase and a release with deck and video.
- **Weaknesses:**
  - 3 bulk commits suggest mass AI generation.
  - The demo URL returned 429 on the check.
  - The golden demo is one scripted scenario.
  - Two-speaker attribution is claimed; whether it uses diarization is unverified.
- **How to differentiate:** Use real noisy-environment audio and genuine multi-speaker handling. Show more than one scripted scenario.

**Honorable mentions (threat 3):**
- **Probe:** dual VAA + streaming with word-timing analytics; strong hiring story.
- **Recall Radar:** grounded agency data, no-LLM intent router, MCP server.
- **Boomerang:** agent-initiated callback plus a consent receipt; the coding worker is scripted.
- **Heed:** the best accessibility entry, with deep streaming-API control.
- **Talkie:** a polished SDK from a 3-person team.
- **AeroGuard:** a dramatic aviation-safety story, but simulation-driven.

### Pattern worth noting
The strongest entries in this batch share one playbook:
1. The LLM or voice agent only hears; deterministic code decides.
2. Every written fact is tied to the exact quote or audio clip that justifies it.
3. Refusal and fail-closed behaviour is used instead of guessing.
4. Measured, hidden-truth evaluation numbers, with honest limitations.

READBACK, Rollcall, Tally, ClauseCatcher, DockWitness, Recall Radar, RouteProof, Briefkeeper, Recount, Lia and Night Desk all use some version of this. **"Evidence-gated action" is now a crowded theme.** A #1 contender needs it as table stakes plus something the others lack:
- real telephony or real-world audio,
- genuinely multi-turn conversational repair,
- broad human stakes,
- a demo judges can run themselves in 30 seconds.

## 3. Category counts (41 projects: 39 in batch + Recall Radar + ScamTrap)

Primary category per project. Where two categories were listed, the first one counts.

| Category | Count | Projects |
|---|---|---|
| transaction/action safety gate | 2 | READBACK, Tally |
| field ops/inventory/logistics | 3 | Recount, DockWitness, RouteProof |
| personal assistant | 5 | Lia, AURA offline, NeuralVoice, Melo, Aura screen |
| receptionist/front desk | 3 | Night Desk, VoiceDesk*, Frontdesk.ai* |
| finance | 3 | Voice Market Agent, VoiceRemitNG, Runway Voice |
| healthcare | 2 | MediVoice, Rollcall (healthcare admin) |
| evidence/claims/legal | 2 | ClauseCatcher, Legal-Voice |
| customer support | 2 | Wavelink Mobile, SafeCall* |
| interview coaching / hiring | 2 | Probe, Miles* |
| education/tutoring | 1 | Viva |
| accessibility | 2 | Heed, Callout* |
| dev tools | 2 | Boomerang, Talkie |
| sales | 1 | Spparo |
| fraud/scam safety | 1 | ScamTrap |
| industrial safety | 1 | AeroGuard |
| other | 6 | Briefkeeper (client intake), ToneGap (bias audit), CVoxPuzzle (CV), Energy prediction (off-topic), Echos (memo notes), Recall Radar (product-recall safety) |
| unknown (404, no description) | 3 | DataWhisperer*, SignalGuard*, hyperas* |

\* = lablab page currently returns 404 (draft or unpublished; unverified).

Total = 2+3+5+3+3+2+2+2+2+1+2+2+1+1+1+6+3 = 41.

### AssemblyAI tech usage in this batch (verified in code where a repo exists)
- **Voice Agent API** (`agents.assemblyai.com/v1/ws`): READBACK, Rollcall, Tally, ClauseCatcher, DockWitness, Boomerang, Probe, RouteProof, Briefkeeper, Wavelink, CVoxPuzzle, Talkie, Night Desk, ToneGap. Claimed only: Lia, VoiceDesk, SafeCall.
- **Universal-Streaming v3 only**: Heed, Recount, MediVoice (medical mode), AeroGuard, Recall Radar, ScamTrap, Spparo, Viva, VoiceRemitNG, AURA offline. Claimed only: Callout, Miles.
- **VAA and Streaming together**: Tally, Probe, ClauseCatcher, DockWitness.
- **Async STT only**: Echos, Runway Voice, Voice Market Agent (mostly), NeuralVoice.
- **LLM Gateway**: AeroGuard, Spparo. Claimed: SafeCall.
- **No AssemblyAI found**: Legal-Voice (repo predates the hackathon), Energy prediction (repo predates the hackathon), Melo and Aura screen (shared repo), Frontdesk.ai (description names Groq Whisper).
