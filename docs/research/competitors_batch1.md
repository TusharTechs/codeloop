# Competitor analysis, batch 1 (submissions.txt lines 3-40, 38 projects)

Checked on 2026-09-25. For each project I parsed the lablab page's embedded Next.js data (description, tech tags, repo, demo, video, slides, likes, peer reviews). I shallow-cloned all 37 public repos (one returned 404) and grepped the code for the AssemblyAI endpoints it calls: `agents.assemblyai.com` (Voice Agent API), `streaming.assemblyai.com` or the SDK streaming classes (Universal-Streaming), `v2/transcript` or `aai.Transcriber` (async STT), and `llm-gateway` or LeMUR. I also sent an HTTP request to every demo URL. I read the code of the strongest repos in more detail.

**How this was checked**
- **Deliverables:** every project in this batch has a video, slides, a repo link and a demo link on lablab. Those fields seem to be required, so they do not set projects apart. Two things do: whether the demo actually works, and whether the repo is real.
- **Peer reviews:** lablab pages show reviews scored 1-5 on four criteria: **Business Value, Originality, Presentation, Application of Technology**. None of them is marked `approved` yet, and `showWinners` is false. The rubric is most likely the same one the final judges will use.
- **"Likes"** are the community votes lablab shows.
- **Ratings** (1-5) are my own judgment. The AAI column shows what the code actually calls, which is not always what the description claims.

## 1. All projects

AAI key: **VA** = Voice Agent API (wss://agents.assemblyai.com), **RT** = Universal-Streaming realtime STT, **Async** = pre-recorded STT, **GW** = LLM Gateway, **LeMUR** = LeMUR. "Demo" gives the HTTP result on 2026-09-25 (000 means no response within 20s, which could be a Render cold start).

| # | Project | Category | What it does / target user | AAI tech (verified in code) | Tools / actions | Safety / verification layer | Repo depth | Demo | Likes / peer reviews (BV/Or/Pr/AT) | Depth | Orig | Polish | THREAT | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | SAUTI AI: Voice-to-Action | Civic / public services | Kenyan residents report problems (e.g. burst pipe) by voice. The agent asks follow-ups and creates a ticket with a reference number on a dashboard | Claims VA. Code has a VA token URL plus an RT v3 test script and a transcribe route, so this may be RT+LLM rather than true VA (unverified) | Create incident, reference number | Incident validation lib | 8 commits over 2 days, ~0.9k LOC | 200 | **11 likes (highest in batch)**; 4/4/5/5, 3/3/3/3 | 2 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/kisii-unversity-code-union/sauti-ai-voice-to-action |
| 4 | Siberia Voice Agent | Receptionist / front desk | Multi-tenant embeddable voice agent for any business: voice RAG over its documents plus lead capture. Multilingual (PT/EN/ES/FR) | VA (agents provisioned via POST /v1/agents, HTTP tools, single-use tokens) | search_knowledge, capture_lead (emails owner) | None beyond server-side key | 1 commit, 13 files (Laravel + JS) | 200 | 9 likes | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/frantal-company/siberia-voice-agent |
| 5 | CyberVoice AI | Fraud / scam safety (phishing reporting) | Users describe a suspicious email by voice. The agent collects the facts and produces a structured incident report | VA | Save incident report | User reviews and confirms before saving | 2 commits, both on 2026-09-25 | 200 | 9 likes | 2 | 2 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/rangers/cybervoice-ai |
| 6 | CampusFlow | Customer support / service desk | Students talk to a campus ops desk: maintenance tickets, status, escalation, facility booking | VA (+GW) | create/get ticket, escalate, check availability, book, clock tool | Backend rejects fabricated or double bookings; audit trail | 19 commits, ~2.8k LOC, regression test | 000 (Render) | 1 like | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/lastminute/campusflow-campus-ops-voice-desk |
| 7 | KiaOra Dispatch | Field ops / property maintenance | Handles NZ tenant emergency calls: triages under tenancy law (P1-P3 SLAs) and dispatches work orders to agencies | VA (+RT ref) | dispatch_work_order | Priority tiers. The "agency webhooks" (Barfoot, Harcourts…) are **in-memory mock endpoints** | 3 commits in 1 day, no tests | 200 | 5 likes; 4/4/5/5, 4/3/4/4 | 2 | 3 | 4 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/shinydatatech/kiaora-dispatch |
| 8 | MockMate | Interview coaching | Browser voice mock interviews: role and persona, résumé-aware questions, live scoring, filler/WPM stats, report card, Hinglish mode | VA (inline config, keyterms, session.resume, reply.create) | plan_interview, log_question, score_answer, end_interview | None (coaching use case) | 7 commits, ~2.3k LOC vanilla JS + Python server | 200 | 5 likes; 4/4/5/5, 4/3/4/4 | 3 | 2 | 4 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/twin-masters/mockmate-ai-voice-interview-coach |
| 9 | AegisVoice OS | Fraud / scam safety | Claims an inline telco fraud guardian that masks spoken OTPs, quarantines calls and escalates to banks within 426 ms | **No streaming or VA endpoint in the code**, only a token route. The UI displays a deprecated v2/realtime URL | mask_sensitive_token, quarantine_call, escalate (appear **simulated**) | "Threat score" is **clamped to 89-99.6**. The benchmark adds Math.random jitter | 12 commits, ~2.5k LOC, mostly UI and simulator | 200 | 4 likes; 5/5/4/4, 4/3/3/3 | 1 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/sahariar-dev/aegisvoice-os-autonomous-voice-fraud-guardian |
| 10 | VoiceWaiter | Ordering / commerce | Restaurant QR menu you order from by voice: recommendations, allergies, cart, staff dashboard | VA | Menu search, cart add/remove, place order | Verified menu data; cart confirmation before submit | 3 commits (Sep 22-23) | 200 | 3 likes | 2 | 2 | 3 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/happygolucky/voicewaiter-ai-voice-restaurant-ordering-system |
| 11 | Hyperion WarRoom | Dev tools / SRE | Incident war-room agent: spins up Google Meet (Meeting BaaS bot), listens, runs infra commands (rollback, restart) on voice command | VA + RT | Infra tools, meeting provisioning, reports | prompt_guard module | 25 commits, ~5k LOC Python, 11 test files | 200 | 3 likes | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/web-walker/hyperion-warroom-ai-agent |
| 12 | BoloRide | Accessibility (ride booking) | Book a cab by phone in English, Hindi or Hinglish. Aimed at elderly and low-digital-literacy users | **RT only, through the LiveKit agents AssemblyAI plugin** (not VA) | Search driver, confirm ride | Correction handling; Langfuse evals | 41 commits, ~31k LOC, 73 test files, CI | 200 | 3 likes | 4 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/boloride/boloride |
| 13 | FarmVoice | Agriculture | Talk to your greenhouse: reads sensors, prioritizes problems, controls equipment | VA | Equipment control function tools | **Impact-tiered confirmation**, with a state check after each action before reporting success | 5 commits, ~2.7k LOC | 200 (GitHub Pages frontend; backend liveness unverified) | 3 likes | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/farmvoice-ai/farmvoice-ai-voice-agent |
| 14 | Playhead | Accessibility / education | Interrupt an audiobook to ask about what you just heard. The listener's position is the query, so answers never spoil what comes next. Jumps across a 54-hour book | VA (HTTP tools, one agent per listener) + Async (indexing) | Recap, lookup within heard text, seek | Won't search past the listener's position; judge access code on credit-spending actions | 28 commits, ~8.7k LOC Python, 15 test files | 200 | 2 likes | 4 | 4 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/playhead/playhead |
| 15 | VoxSales | Sales | Bilingual sales voice agent: books demos, sends Telegram alerts, n8n+Mistral BANT scoring into Airtable | VA (bridge) | schedule_demo, telegram alert, capture lead | None | 2 commits, 8 files | 200 | 1 like | 2 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voxsales-ai-voice-agent/voxsales-ai-voice-agent |
| 16 | **Saakshi** | Evidence / compliance (regulated sales) | AI witness for Indian insurance and loan sales. Hears a mis-selling claim ("guaranteed 12%") and says a correction aloud to the customer ~1.4 s later. Runs teach-back questions and issues a hash-chained certificate anyone can verify | RT (Universal-3.5 Pro, diarized, Hinglish) + VA (spoken corrections) + GW fallback | Scripted correction, teach-back, certificate | Deterministic regulator "protocol packs" (IRDAI, RBI KFS). **LLM can never tick, flag or speak.** Hash chain with a public VALID/TAMPERED page. /metrics page | 12 commits (phase 0-9), ~19k LOC, 97 test files incl. e2e | 200 | 2 likes | 5 | 5 | 4 | **5** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/monster/saakshi-consent-you-can-prove |
| 17 | Brand Studio Agent | Other (creator tools) | Voice "taste coach" for content ideas. Scores a script against a rubric with a quoted sentence for every score and refuses scripts below 9/10. The user argues back by voice | VA (async reply.create pattern) + RT (word timestamps for edit list) + GW (forced JSON verdict) | Render/asset tools, script lock | "No citation, no score"; voice override is logged | **127 commits**, ~47k LOC, 65 test files, still committing on 09-25 | 000 (unreachable at check) | 1 like; **4/5/4/5, 4/4/5/4 (best in batch)** | 4 | 4 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/vibemarketing-studio/brand-studio-agent-build-your-brand-by-voice |
| 18 | RevenueFlow | Receptionist / front desk | WhatsApp voice-note receptionist for LatAm small businesses: transcribes, extracts intent, resolves "el jueves en la tarde" into a date, books in ~7 s | **Async STT (U-3.5 Pro) + GW only, no realtime or VA** | Book, reschedule, escalate | "Model decides intent, system decides what's allowed": catalog IDs only, dates computed in code, template replies, human escalation | 53 commits, ~8.3k LOC, 177 tests claimed; real WhatsApp number in VE/BR | 200 (login wall; demo creds in README) | 2 likes | 4 | 3 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/revenueflow/revenueflow-whatsapp-voice-receptionist |
| 19 | STICK | Other (productivity) | Speak to build a slide deck, exported to editable PPT | **No AssemblyAI reference anywhere in the repo** | Deck generation | Validation step (claimed) | 4 commits, all on 2026-08-12 (before the event) | Demo link = GitHub repo | 2 likes; 5/5/3/5, 4/3/3/3 | 2 | 3 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/ninjas/stick |
| 20 | VoiceDesk AI | Customer support | Helpdesk agent with lip-synced avatar that watches the user's shared screen and unblocks the account itself | **RT through the LiveKit plugin** (Groq Qwen-VL LLM, Deepgram TTS, Beyond Presence avatar). Not VA | unblock_account, email ticket | None | 22 commits, ~8.4k LOC | 200 | 2 likes | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/assembly-voice/voicedesk-ai |
| 21 | Liora | Personal assistant | Voice memory for physical items: "where's my passport", packing, loans ledger | VA (Node proxy) | Move, pack, loan, return | On-screen confirmation card before any write; timeline log | 9 commits in one day, ~2.2k LOC | 000 (Render) | 2 likes | 2 | 3 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/bloodfang-ronin/liora |
| 22 | AegisOR | Healthcare / clinical safety | Operating-room audio compliance: time-out checklist, verbal-order read-backs, sponge counts, post-op report | Async STT through the Python SDK (+ summarization). Not realtime | None (monitoring and report) | Checklist verification (claimed) | 6 commits in 1 day, ~1.8k LOC | 200 (HF Space) | 2 likes | 2 | 4 | 2 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/testteam/aegisor |
| 23 | SpeakToDebug | Dev tools | Describe a bug aloud. Agent calls local tools (list_files, search_code, read_file, run_tests) and speaks the root cause and fix | VA | 4 local workspace tools | Grounded in tool output (claimed) | 12 commits, ~2.3k LOC | Demo = mp4 in repo | 1 like | 3 | 3 | 2 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/speaktodebug/speaktodebug |
| 24 | **Kwik 112** | Emergency | AI call-taker for India's 112 emergency line (Hindi, Hinglish, English). Hands a human dispatcher a severity-graded incident card | VA (43 keyterms) + optional GW | propose_incident_update (JSON-schema) | **Escalate-only severity floor in code**: the agent can raise severity but never lower it. Tested, prompt-injection test included. Human decides at 3 checkpoints; audit trail | 11 commits, ~20k LOC, **284 tests, CI badge**, held-out benchmark (critical recall 9/9) | 200, with a /for-judges page | 1 like | 5 | 4 | 5 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/termin8ors/kwik-112-ai-voice-call-taker-for-112 |
| 25 | Tareeq Al-Huda | Other (religious content) | Islamic platform: chat, Quran, streams, utilities | **No AssemblyAI in repo** (Google AI Studio remix) | None | None | 3 commits | 200 (ai.studio) | 1 like | 1 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/zsc/tareeq-al-huda |
| 26 | Robin Voice Ops | Receptionist / front desk (home services) | Home-services voice ops: book appointments, request service, job status, FAQ | VA (session resume, keyterms, voice focus, word captions) | check_availability, book_appointment, get_job_status, faq_search, escalate_to_human | **Dispatcher approval queue**, SHA-256 hash-chained audit log, PII handling; 6/6 live evals | 6 commits in 1 day, ~3k LOC | 200 | 1 like | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/robin-voice-ops/robin-voice-ops |
| 27 | OpenLine | Receptionist / front desk | Small-business receptionist: hours, services, booking into SQLite, take message | VA (stored agent) | 7 client tools | Deterministic data only | 3 commits, ~0.8k LOC | 000 (trycloudflare tunnel, dead) | 1 like | 2 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/openline-receptionist/openline-ai-voice-receptionist |
| 28 | **MediScribe Live** | Healthcare | ER: bedside voice triage agent plus ambient scribe that writes a source-linked SOAP note, clinician sign-off, FHIR R4 export | VA (triage) + RT (medical domain, diarized) + GW (SOAP) | record_patient_intake, check_drug_interaction, flag_critical_vital | **Each SOAP line cites transcript turns, and the server checks every citation**; unsourced lines flagged "NO SOURCE - VERIFY"; stays DRAFT until signed | 22 commits (PR-based), ~4.9k LOC, no tests | 200 | 2 likes | 4 | 3 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/neuron-burners/mediscribe-live |
| 29 | **Afterward** | Personal assistant (outbound calls for the user) | After a UK death, calls banks, utilities and pensions for the family: presses IVR keys, waits on hold, discloses it is an AI, records a case reference | VA (one session per call; transcription_mode switched to max_accuracy before the reference is read) | press_key (DTMF), flag_needs_family, record_outcome | **Server validator checks every reference against what the clerk actually said and refused its own agent mid-call.** Missing info goes back to the family as an amber card. Stereo recordings; `npm run verify` | 21 commits (built Sep 22-23), polished Next.js, SPEC, DESIGN, UI-SPEC docs, and a "If you're judging this" README section | 200 (no login, auto-replays) | 2 likes | 4 | 5 | 5 | **5** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/drafters/afterward-the-calls-after-a-death-made-for-you |
| 30 | DocuVoice RAG | Other (document Q&A) | Upload a document and ask questions by voice (Streamlit) | Async STT | None | None | 7 commits, ~0.5k LOC | 303 (Streamlit) | 1 like | 1 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/docuvoice-ai/docuvoice-rag |
| 31 | **Orion** | Finance / consumer | Upload a bill and it phones the provider over Twilio: holds, navigates IVR, asks for retention, negotiates, refuses the first offer | VA + RT (alternate backend) + Async (speaker-labelled post-call transcript) + GW, i.e. four AAI products | IVR keys, vault answers, negotiation | **Outcome recorded only if the post-call recording transcript supports it** (no self-grading); rehearsal mode | 44 commits (all Sep 4-5), ~24k LOC, 59 test files, docs site | **503 at check** | 1 like | 4 | 4 | 3 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/devstation-labs/orion-autonomous-bill-negotiation-by-voice |
| 32 | Voice Case | Other (game / entertainment) | AI hosts a printable murder mystery. The solution is kept server-side so the model cannot leak it | RT (no VA) | Deterministic intent (alias table + edit distance) | Answer never sent to the client; 4 tests assert it. Documents measured STT failures | 3 commits, ~0.9k LOC, 25 tests, no dependencies | 200 | 0 likes | 2 | 4 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/ai-q-labs/voice-case-the-glasshouse-0340 |
| 33 | VoxArchitect | Dev tools | Speak an architecture change request; multi-agent repo scouting, ADR drafts, GitHub actions staged behind approval | VA + optional GW | GitHub staging | Human approval gate | 1 commit, ~1.7k LOC | **Demo URL is localhost** | 0 likes | 2 | 3 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/rhemaai-forge/voxarchitect-voice-native-intelligence |
| 34 | KT tutor | Education / tutoring | General voice tutor that explains, quizzes and asks for teach-back | VA | None evident | None | 25 commits, ~3.3k LOC | 200 | 0 likes; 3/2/3/2 | 2 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/primehack-security-team/kt-the-ai-tutor-you-talk-to |
| 35 | Readdy AI | Interview coaching | Junior technical mock interviews: 5 tracks, 4 stages, silence detection, scorecard | VA | Report generation | Prompt-injection guardrails (claimed) | 38 commits, ~3.7k LOC | Link points to the Vercel dashboard (probably not publicly viewable) | 0 likes; 4/4/5/5, 3/3/4/3 | 2 | 2 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/atomix/readdy-ai-junior-technical-interviewer-practice |
| 36 | Swara AI | Other (TTS) | Hindi text-to-speech web app | **No AssemblyAI in repo** | None | None | 3 commits, dated June 2026 | Vercel dashboard link | 0 likes | 1 | 1 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/aa49/swara-ai |
| 37 | EverCall | Healthcare / eldercare | Daily check-in call to an elderly parent; "Radar" dashboard for mood, medication, memory slips | Claims RT + LeMUR. **The analysis route is a stub returning a golden fixture**; demo uses a simulated grandma | Alert family | None | 4 commits, ~0.5k LOC | 200 | 0 likes; 4/4/5/5, 4/3/4/3 | 2 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/cubiczan/evercall-jarvis-for-grandma |
| 38 | ARIA (LodeStar) | Personal assistant | Proactive companion or chief of staff that speaks first, remembers promises and mood, uses Google Calendar and news | VA (8 tools) + GW (memory extraction) | Calendar, memory, news | Circuit breaker; safety net for skipped tool calls | 1 commit, ~6.5k LOC, 51 tests claimed | 000 (Render) | 0 likes | 3 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/lodestar/aria-adaptive-relational-intelligence-agent |
| 39 | Mockrill | Interview coaching | Mock interview coach: word-level evidence ("kind of" ×3 at 07:42), rubric scoring, re-drills the weakest answer | RT (U-3.5 Pro) + GW tool calls + browser TTS ("Path B", no VA) | Rubric scoring tools | Deterministic replay mode | 24 commits, 36 test files | 200 | 0 likes | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/libitum/mockrill-realtime-ai-mock-interview-voice-coach |
| 40 | OpsVoice AI | Dev tools / SRE | Voice commander for Kubernetes SEV-1s: pod health, logs, restart pods, post-mortem | Claims VA (**repo returns 404, unverifiable**) | Restart pod, raise memory limit, post-mortem | None visible | Unverifiable | Demo link = the same 404 repo | 0 likes; 3/3/5/4 | 2? | 2 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/odishaaititans/opsvoice-ai-sre-incident-commander |

**AssemblyAI usage in this batch (from code):**
- About 25 of 38 use the **Voice Agent API**.
- 5 use **realtime STT only**: BoloRide and VoiceDesk through the LiveKit plugin, plus Voice Case, Mockrill and EverCall.
- 3 use **async STT only**: RevenueFlow, DocuVoice, AegisOR.
- 4 have **no real AssemblyAI integration**: STICK, Tareeq, Swara, and AegisVoice (token route only).
- 1 cannot be verified: OpsVoice.
- The strongest projects combine several products: Saakshi (RT+VA+GW), MediScribe (VA+RT+GW), Orion (VA+RT+Async+GW) and Brand Studio (VA+RT+GW).

## 2. Top threats in this batch

### 1. Saakshi: Consent You Can Prove (THREAT 5)
- **What it does:** Sits between an insurance or loan advisor and a customer in India. Diarized Universal-3.5 Pro streaming handles English and Hinglish, and each finalized turn is checked by a deterministic regulator rule pack (IRDAI ULIP, RBI KFS). When the advisor makes a prohibited claim ("guaranteed 12% returns"), Saakshi speaks a correction of under 20 words to the customer through the Voice Agent API, about 1.4 s median after the advisor stops. It then asks 3-5 teach-back questions and issues a hash-chained certificate that a public page verifies as VALID or TAMPERED.
- **Why judges might like it:**
  - It is original: a real-time "referee" rather than yet another assistant.
  - It cites real regulations and a grievance figure (26,667 IRDAI complaints).
  - It keeps the LLM strictly advisory: it can never tick, flag or speak.
  - It reports measured numbers (1 intervention in 36 turns, 0 false ticks in 12) on a /metrics page.
  - About 19k LOC with 97 unit and e2e test files.
  - It uses two AAI products for different jobs.
- **Weaknesses:**
  - Very few community votes (2 likes).
  - Niche to Indian regulated sales, with no customers.
  - A two-party, one-laptop setup can be hard to follow in a demo video.
- **How to differentiate:** Keep its best pattern (a deterministic rule engine owns decisions, the LLM only advises, and the evidence trail can be verified) but apply it where the *agent itself takes actions*. Saakshi only intervenes by speaking. It does not gate tool calls or transactions.

### 2. Afterward: the calls after a death (THREAT 5)
- **What it does:** After one intake conversation with the executor, it runs one live Voice Agent session per institution (12 fictional UK banks, energy suppliers, pension providers and councils, built as a scripted IVR, hold and clerk test bed). It presses DTMF keys, waits on hold, discloses that it is an AI, states only facts from the brief, and records the outcome through a validated tool. A server validator compares each case reference with what the clerk actually said. It refused its own agent once mid-call and the call recovered. Anything missing goes back to the family as an amber "Needs you" card. Every call produces a stereo recording, a timeline and a verified reference in a shareable Estate Ledger.
- **Why judges might like it:**
  - The emotional hook is very strong.
  - Unusual use of the Voice Agent API: outbound calls, DTMF, switching `transcription_mode` to max_accuracy just before the reference is read.
  - Hard numbers: 12/12 verified, 0 unverified writes, `npm run verify` runs offline.
  - Top-tier design polish, a logged-out demo that replays itself, and a README with an "If you're judging this" section mapped to the four criteria.
  - Clearly labels what is simulated and what is real.
- **Weaknesses:**
  - The institutions are simulated.
  - Built in 2 days, with only about 1.3k LOC of logic.
  - UK-only market story; 2 likes.
- **How to differentiate:** A demo against real counterparties or real systems, rather than a scripted world, would beat its "simulated but honest" position. So would a verification layer that generalizes beyond one domain.

### 3. Kwik 112: AI call-taker for India's 112 (THREAT 4)
- **What it does:** A Voice Agent intake for emergency calls in Hindi, Hinglish and English, with 43 keyterms (medical words, Delhi localities). A mid-call JSON-schema tool proposes severity. A deterministic rules engine sets a floor that the model can raise but never lower. The signature demo moment: the agent proposes LOW and the banner shows it held at CRITICAL. A human dispatcher decides at 3 checkpoints, with an audit trail.
- **Why judges might like it:**
  - Clear "safety guarantee in code, not in the prompt" story.
  - 284 tests in CI, a held-out benchmark (100% critical recall, 16.7% over-escalation), a prompt-injection test, and a /for-judges page.
  - Strong polish.
- **Weaknesses:**
  - Emergency-dispatch AI is a common hackathon theme, and it is not connected to real telephony.
  - Only 1 like.
  - The benchmark is synthetic and small (9 critical calls).
- **How to differentiate:** Its "escalate-only floor" is one narrow invariant. A broader policy or verification engine across many action types, with real integrations, would read as a bigger idea.

### 4. Orion: autonomous bill negotiation by voice (THREAT 4)
- **What it does:** Reads a bill (photo or PDF), phones the provider over Twilio through the Voice Agent API, navigates IVR, asks for retention, answers security questions from an encrypted vault and negotiates. After the call it transcribes its own recording with speaker labels and records only the outcome the recording supports. Includes a rehearsal mode.
- **Why judges might like it:**
  - Uses four AAI products (VA, RT, Async, GW) and takes both paths the challenge offers.
  - The "no marking its own homework" verification idea.
  - Consumer value is obvious.
  - About 24k LOC, 59 test files, a docs site.
- **Weaknesses:**
  - The demo returned **503** on 2026-09-25.
  - All commits fall on Sep 4-5, which suggests a burst, possibly AI-generated.
  - Real negotiation calls raise legal and ethical questions.
  - 1 like.
- **How to differentiate:** A working live demo and stronger reliability evidence. Its post-hoc verification checks an outcome after the call, whereas a pre-action gate stops a bad action before it happens. That difference is an opening.

### 5. MediScribe Live (THREAT 3), with Playhead and Brand Studio Agent close behind (THREAT 3)
- **MediScribe Live** combines a Voice Agent for bedside triage, medical-domain diarized streaming STT, and a GW-generated SOAP note. The server checks every citation, unsourced lines are flagged, and the note stays a draft until a clinician signs it. It exports FHIR R4.
  - Strength: strong use of three AAI products and a clean verification idea.
  - Weaknesses: AI scribes are crowded, and there are no tests.
- **Playhead** is the most original consumer idea in the batch: position-aware audiobook Q&A that cannot spoil the book, with accessibility framing and one agent per listener. It is solid engineering.
- **Brand Studio Agent** has the highest peer-review average in the batch (17.5/20) and 127 commits, but its demo was unreachable and the creator-tools niche is less compelling.

**Community vote leaders (not quality leaders):**
- SAUTI AI (11 likes) is a thin civic reporting app.
- Siberia and CyberVoice (9 each) are basic.
- Likes do not track depth in this batch.

**Out-of-batch sighting (from lablab "latest apps" sidebar, not verified):**
- **"Tally"** describes itself as a reliability layer between a voice agent and its actions. It runs an independent speech stream, validates each tool call against that evidence, holds the call on conflict, re-asks only about the disputed item, and turns caught failures into regression cases. It claims validation against the real managed Voice Agent (3 speakers, 36 recordings).
- This is **directly a "transaction/action safety gate"** competitor. Whoever covers that batch should examine it closely.
- Also seen: "Guard Line" (Korean phone-scam warning), "AeroGuard" (airport ground-radio clearance interceptor) and "READBACK".

## 3. Category counts (batch 1, n=38)

| Category | Count | Projects |
|---|---|---|
| Receptionist / front desk | 4 | Siberia, RevenueFlow, Robin Voice Ops, OpenLine |
| Dev tools / SRE | 4 | Hyperion WarRoom, SpeakToDebug, VoxArchitect, OpsVoice |
| Interview coaching | 3 | MockMate, Readdy AI, Mockrill |
| Healthcare / eldercare | 3 | MediScribe Live, AegisOR, EverCall |
| Personal assistant (incl. acting on the user's behalf) | 3 | Liora, ARIA, Afterward |
| Fraud / scam / security safety | 2 | AegisVoice OS, CyberVoice |
| Customer support / service desk | 2 | CampusFlow, VoiceDesk |
| Accessibility | 2 | Playhead, BoloRide |
| Evidence / compliance / legal | 1 | Saakshi |
| Emergency | 1 | Kwik 112 |
| Finance / consumer | 1 | Orion |
| Field ops / property maintenance | 1 | KiaOra Dispatch |
| Agriculture | 1 | FarmVoice |
| Sales | 1 | VoxSales |
| Ordering / commerce | 1 | VoiceWaiter |
| Education / tutoring | 1 | KT tutor |
| Civic / public services | 1 | SAUTI AI |
| Other (slides, creator tools, game, doc Q&A, religious, TTS) | 6 | STICK, Brand Studio, Voice Case, DocuVoice, Tareeq Al-Huda, Swara |

**Patterns worth noting:**
- A "deterministic guardrail + verifiable evidence" story is now **the standard move among the top entries**: Saakshi (rule packs, hash chain), Kwik 112 (severity floor), Afterward (reference validator), Orion (post-call transcript check), MediScribe (citation check), Robin (approval queue, hash-chained log), RevenueFlow ("model decides intent, system decides what's allowed").
- A safety or verification layer alone will not stand out. Winning needs one of these, or more:
  - a genuinely new domain;
  - real, not simulated, counterparties or integrations;
  - quantified reliability evidence against live AssemblyAI;
  - a working, logged-out demo;
  - use of several AAI products where each does a distinct job.
