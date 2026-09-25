# Competitor analysis, batch 2 (submissions.txt lines 41–78, 38 projects)

AssemblyAI Voice Agent Hackathon 2026 (lablab.ai). Collected 2026-09-25.

## Method and caveats

- I downloaded every lablab page with curl and parsed the embedded Next.js JSON. That gave me the description, tech tags, categories, repo, demo, video, slides, likes, and reviews for each project.
- **The pages expose reviews.** Each submission's JSON has a `reviews` array scored on `businessValue / originality / presentation / applicationOfTech`, which looks like the judging rubric. All reviews are marked `approved:false`. So far only two reviewers appear in this batch: `ramachandranalam` ("Senior Data Engineer"), who scores generously, and `amandloi1979`, who scores harder. I have not confirmed they are official judges. The column below shows the average of the four scores for each reviewer.
- **Likes are 0 or 1 for every project, so community votes tell us nothing.**
- Every submission lists a video (MP4 on lablab storage), a repo link, a demo link, and a slides PDF (V/G/D/P below), probably because the form requires them. Where a "demo" is only a GitHub link or localhost, I say so.
- **AssemblyAI tech check.** For 20 repos I cloned the code and grepped for the endpoints actually called:
  - `agents.assemblyai.com/v1/ws` means the Voice Agent API (VAA).
  - `streaming.assemblyai.com/v3/ws` means Universal-Streaming realtime STT (U-S).
  - `api.assemblyai.com/v2/realtime` is the legacy realtime API.
  - Where I did not inspect a repo, the value comes from the page claim only and is marked "(claim)".
- Relay's repo returns 404 (it is private or deleted). I confirmed its tech by grepping the JS bundle of its live demo.
- Ratings are 1–5. D = technical depth, O = originality, P = polish/demo quality, T = threat to win #1.

## 1. All projects

| # | Project | Category | What it does / target user | AssemblyAI tech (verified?) | Tools / actions | Safety / verification layer | Deliverables | Reviews (avg) | D | O | P | T | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 41 | TalkOS | personal assistant / productivity | Voice-directed workspace: docs, sheets, planners, canvases, dashboards, Tavily research | VAA (verified; US+EU endpoints, short-lived token) | Many workspace-editing tools | Cancels stale work when interrupted, revision checks, undo/redo receipts | V G D P; 36 commits, ~12.9k LOC, 70 test files | none | 4 | 3 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/talkos/talkos |
| 42 | AI voice agent for booking appointment | receptionist / healthcare | Hospital website with booking and doctor discovery | Unclear; the description never mentions AssemblyAI mechanics | Booking (claim) | none | V G D P | none | 1 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/nightmare/ai-voice-agent-for-booking-the-appointment |
| 43 | Voice-Controlled Robot Arm | other (robotics / OR assistant) | Hands-free surgical instrument fetching; arm simulated in CoppeliaSim | Live STT (claim; repo not inspected) | Arm control via FSM | Closed-loop joint check, fuzzy matching, mid-task correction | V G P; demo link is the GitHub repo | none | 3 | 4 | 2 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/vibes/voice-controlled-robot-arm |
| 44 | **Claim intake agent that refuses to guess** | evidence / claims / legal | Insurance FNOL claim intake by voice | VAA (verified; `record_field` tool, `session.update`) | `record_field` goes to a server validator | Three verdicts (accepted / unconfirmed / rejected); spoken read-back; deliberately removed keyterm biasing after finding it caused false accepts; `/compare` page | V G D P (live 200); 30 commits; 142 tests | none | 4 | 4 | 4 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/vector-forge/the-claim-intake-agent-that-refuses-to-guess |
| 45 | **HazVox AI** | industrial safety | Spoken hazard reports become OSHA logs and a Supabase command dashboard | **Page claims VAA plus tool calling. The code actually uses the browser Web Speech API with regex extraction.** AssemblyAI appears only as a call to the deprecated `v2/realtime/token` | "`report_safety_hazard`" is a regex-built payload, not a real LLM tool call | none | V G D P; 6 commits; no tests | 3.63 (4.5 / 2.75) | 2 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/hazvox-ai-x-voice-safety-agent/hazvox-ai-hands-free-voice-safety-agent |
| 46 | voicebridgeai | accessibility | Voice navigation of a web dashboard for blind and motor-impaired users, with offline fallback | VAA (claim) | Dashboard control | Offline local-parser fallback | V G D P (demo is a raw-IP sslip.io link) | none | 2 | 2 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/uganda-cranes/voicebridgeai |
| 47 | Ohun | other (translation / communication) | Translated voice calls, chats, and voice notes | Realtime STT plus async STT for voice notes (claim) | none | none | V G D P | none | 2 | 2 | 3 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/teevincs/ohun |
| 48 | OpsPilot Voice | dev tools / SRE | Voice incident commander | VAA (verified) | `get_system_status`, `create_incident`, `execute_runbook_step`, `resolve_incident`, … (simulated) | Human approval with single-use confirmation tokens for state-changing tools | V G D P; only 3 commits, ~760 LOC | none | 2 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/silvercrane/opspilot-voice-ai-incident-commander |
| 49 | **SilverLine** | healthcare (elder care) | Phone line for elderly patients: confirms clinic visits, teaches back each medication | VAA (verified) plus Twilio PSTN/SMS/SIP | `check_availability`, `book_visit`, `list_medications`, `confirm_medications`, `issue_receipt` | Slow-safe turn detection (1200/3500 ms); keyterms narrowed per call stage; nothing books without full read-back and an explicit yes; HMAC-signed receipt the family can verify; **"proof" file of a real 8-minute PSTN call** | V G D P; 13 commits; ~2k LOC; no tests | none (submitted Sep 22) | 4 | 4 | 4 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/beyond-vibe/silverline |
| 50 | **Second Listen** | evidence / claims (VC risk) | Voice debrief for investors after founder calls; turns conversation into a risk-signal ledger | VAA (verified; built on AssemblyAI's starter kit) plus Universal-2 async for uploads | Ledger / evidence / follow-up tools | Every signal stored with a verbatim quote and timestamp; final decision stays with a human; deterministic fallback | V (also on YouTube) G D P; 47 commits; CI; telephony folder from the starter | none | 3 | 4 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/blink/second-listen |
| 51 | VoiceNova | personal assistant | Voice control of a desktop PC (open apps, search) | VAA (claim) | Opens apps and URLs | none | V G P; **demo URL is 127.0.0.1** | none | 1 | 1 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voice-nova/voicenova |
| 52 | **Relay: Voice Ops for Field Work** | field ops / inventory / logistics | Field technician speaks one incident; the agent checks asset history and inventory, creates a work order, notifies a supervisor | VAA (verified via live-demo bundle: `agents.assemblyai.com/v1/ws`, `tool.call`, `/api/tools`) | One orchestration tool covering asset, inventory, transfer, work order, and notify | "Relay Recovery": when the local-inventory tool fails it replans (part transfer from Central Stores) and keeps the failure visible | V D P; **repo 404 (private or deleted)** | **4.25** (4.5 / 4.0) | 3 (unverified) | 3 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/relay/relay-voice-operations-for-field-work |
| 53 | echologic | field ops | Hands-free incident logging for field engineers | VAA (verified; starter-kit fork, 47 commits since Aug 14, i.e. before the hackathon) | JSON-schema tools to a DB webhook (claim) | none | V G D P; no tests | none | 2 | 2 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/echologic-ai/echologic-voice-agent |
| 54 | Voice Language Partner | education / tutoring | Language conversation practice, graded by Gemini afterwards | VAA (claim) | none of note | none | V G D P; FastAPI + Postgres | none | 3 | 2 | 3 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/talksolo/voice-language-partner |
| 55 | Aura SEC 10-K | finance | Analysts query audited 10-K figures by voice | Universal-3.5 realtime STT (claim) | EDGAR lookups | Pulls exact line items from filings; sector-aware accounting rules | V G D P | 2.75 | 3 | 3 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/aura-sec-in-ram-voice-intelligence/aura-real-time-sec-10-k-voice-analyst |
| 56 | **Voice Action Gate** | transaction / action safety gate | Irreversible actions (e.g. bank transfers) execute only if every argument is grounded in words from the word-level transcript | **U-S v3 (verified)**: word-level confidence and timings. The README describes the VAA `tool.call` seam, but the repo does not call VAA; the demo's proposal is built client-side | Execute credential (capability) minted only by the gate | Capability-based gate; the witness set is built from the transcript before the proposal is seen; normalizer is a partial function (returns UNDECODABLE instead of guessing); a mutation test arm; daily token cap in a Durable Object | V G D P (live 200); 179 tests; ~3.8k LOC Python/JS; very rigorous docs | **4.63** (4.5 / **4.75**), highest in batch | 4 | 5 | 4 | **5** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voice-action-gate/voice-action-gate |
| 57 | **RECEBE** | field ops / inventory / logistics | Warehouse staff speak what arrived in a delivery (Portuguese/English); the app reconciles it against the order | U-S (verified) plus AssemblyAI LLM Gateway. The VAA endpoint is also referenced (verified). Gemini TTS for fixed prompts | LLM Gateway proposes structure; deterministic catalog and arithmetic rules | Targeted question when quantities are ambiguous ("are the 2 damaged included in the 4?"); corrections across turns; **version-bound confirmation, so a stale "yes" cannot finalize a changed record**; eval suite; Gemini Live used as an autonomous tester | V G D P (live 200, Cloud Run); **88 commits, 74 test files**, last commit Sep 24 | none | 4 | 4 | 4 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/signal-foundry/recebe-voice-delivery-reconciliation |
| 58 | **Patchline** | transaction / action safety gate (reliability) | Reliability supervisor for voice agents: blocks tool calls built on misheard entities, repairs them live, turns each failure into a regression test | U-S v3 (verified); Groq for fallback extraction and Orpheus TTS | `lookup_order`, `request_refund`, `update_shipping_address` | Action Gate plus a scoped repair question; regressions replayed against candidate AssemblyAI configs (keyterms, turn detection) with promote/rollback; found a real `keyterms_prompt` wire-format bug | V G D P (live 200, Railway); 43 commits; 39 test files; PRD, DECISIONS, and TESTING docs | none | 5 | 4 | 3 | **4** | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/patchline/patchline |
| 59 | SmartLink Voice | other (marketing analytics) | Voice queries over ad-campaign ClickHouse analytics, plus bot-fraud detection | STT / VAA (claim) | Read-only SQL | Read-only queries | V G D P (demo is an existing commercial site) | 3.5 (4.25 / 2.75) | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/smart-link/smartlink-voice-autonomous-analytics-voice-agent |
| 60 | VANE-SPACE-SLA | other | Prompt-grounding toolkit; its own description says it calls no real services. **No voice or AssemblyAI content visible** | none visible | none | "Multi-gate telemetry validation" (simulated) | V G D P | none | 1 | 1 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/anticipatedd-vsslaanintelligentmulti-agent/vane-space-sla-v10 |
| 61 | Heat Warning Agent | industrial / worker safety (emergency) | Calls outdoor workers when heat is dangerous and records whether they *understood*, not just whether they answered | VAA (verified); 4 function tools | Writes the outcome record during the call | Never asks yes/no questions; facts start as null ("not established") rather than false; escalates to a human on dizziness etc.; worker's own words stored beside each judgement | V G D P (live 200); 18 commits; 23 unit tests plus e2e (claim); no telephony | none | 3 | 5 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/heat-warning-agent/heat-warning-agent |
| 62 | SahabatSuara | other | Indonesian work companion: SOPs, KPIs, bible verses, job board, referral selling | STT / VAA (claim), Streamlit | none | none | V G D P (demo on HF Space) | 2.5 | 1 | 2 | 1 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/sahabatsuara/voice-work-skill-discipline-spirituality |
| 63 | LineOne | other | Vague "voice-first prototype"; no concrete use case | unclear | unclear | none | V G D P | 3.0 | 1 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/juice-lineone/lineone |
| 64 | Voicemed | healthcare | "Aria" voice triage nurse: ESI 1–5, drug interactions, 911/988 escalation, SOAP notes with ICD-10, English/Spanish | VAA (verified) | Symptom lookup, interaction check, triage, booking, SOAP | Mandatory red-flag questions; **urgency decided by deterministic code, not the LLM**; never diagnoses | V G D P (Render demo timed out on my check); 44 tests; first commit Aug 31 | **4.13** (4.5 / 3.75) | 4 | 2 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/team-rn/voicemed-ai-agent |
| 65 | LinguSim | education / tutoring | Adaptive language roleplays that throw in complications, then personalize the next scenario | VAA (claim) | App-level tools (claim) | none | V G D P | none | 3 | 2 | 3 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/speakquest/lingusim-adaptive-language-simulation-coach |
| 66 | Interview Lab | interview coaching | Mock job interview by voice, with an OpenAI feedback report | VAA (claim) | none | none | V G D P | 3.75 (4.5 / 3.0) | 2 | 1 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/interview-lab/interview-lab |
| 67 | Speech-to-Maya | dev tools (3D) | Voice copilot that writes `maya.cmds` code through a local Ollama Qwen model | U-S WebSocket (claim) | Executes generated Python in Maya | none | V G P; demo link is the GitHub repo (local desktop only) | none | 3 | 4 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voiceagentj/speech-to-maya |
| 68 | Officer Parker | interview coaching | US visa interview simulator that cross-examines you against your own DS-160 form and quotes every contradiction | VAA (verified); LLM Gateway for scoring | none (report at end) | "Honesty" rule: suggested rewrites may not add facts you didn't state; server mints a 300 s single-use token | V G D P (live 200); 11 commits | none | 3 | 4 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/officer-parker/officer-parker |
| 69 | BugSpeak | dev tools | Spoken bug report becomes a structured GitHub issue | VAA (claim) | create-issue client tool | none | V G D P | 3.5 | 2 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voiceforus/bugspeak-speak-a-bug-ship-issue |
| 70 | **Guard Line** | fraud / scam safety | Korean voice-phishing detector that quotes the transcript evidence behind each risk signal | U-S v3 Korean (verified) plus LLM Gateway | none (warns; guardian notification is simulated) | Java layer validates the quoted evidence and confirms high-impact signals with rules; reproducible heuristic score; honest limits stated | V G P; demo on Render timed out on my check; 14 commits; 7 synthetic scenario audio sets; submitted Sep 24 | none | 4 | 3 | 3 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/guard-line/guard-line |
| 71 | **Veritas Clinical AI** | healthcare | Ambient scribe that writes SOAP notes and bills (CMS-1500, 837P EDI), reads ECG images via Gemini, checks drug interactions | U-S v3 in backend (verified). **Deployed frontend is a static export with hardcoded `localhost:8000` backend calls**, so the live voice path very likely does not work | ICD-10 lookup, claims generation | "Medico-legal airlock" for drug interactions (claim) | V G D P; 13 commits all on Sep 4 (polished-looking scaffold, buzzword-heavy) | 3.5 (4.5 / **2.5**) | 2 | 3 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/veritas-clinical-ai/veritas-clinical-ai |
| 72 | Tourist translator | other (translation) | Streamlit app translating English to/from EU languages | STT (claim; Streamlit) | none | none | V G D P | 2.63 | 1 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/firstchoice/tourist-translator-ai |
| 73 | Voice Lab Molecular | education (science) | Voice copilot for molecular point groups, with deterministic computation and a "Research Replay" | VAA (verified) | PubChem lookup, symmetry engine | Deterministic computation checks the LLM; replay of evidence | V G D P (live); ~20k LOC and 20 test files, but only 4 commits on one day (bulk import) | none | 4 | 5 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/voicelab/voice-lab-molecular-symmetry-copilot |
| 74 | **VerbaTrace AI** | evidence / claims / legal (compliance interviews) | Adaptive enterprise interviews (compliance, due diligence) that produce an evidence pack of risks, decisions, and actions | **U-S Universal-3.5 Pro (verified)** plus Cloudflare Workers AI. The page claims VAA tool actions; the repo shows STT plus its own LLM | Own workflow engine (not AssemblyAI tool calls) | Evidence scoring and gap detection; targeted follow-ups | V G D P (live 200); **1 commit; a single 12.9k-line `index.js`; "v4.3.3"**, which suggests a pre-existing product | 3.5 (orig 2) | 3 | 2 | 3 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/blue-river-technology/verbatrace-ai-voice-to-evidence-agent |
| 75 | EchoAgent AI | personal assistant | Generic voice assistant for meeting summaries and tasks | STT (claim) | unclear | none | V G D P | none | 1 | 1 | 2 | 1 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/sara-developer/echoagent-ai |
| 76 | VoiceOps Controller | dev tools / SRE | Voice-commanded Kubernetes pod mitigation with a Groq-written post-mortem | U-S v3 (verified) | Deterministic FSM intent parser (no LLM tool calling) | Two-phase voice confirmation with single-use execution tokens for destructive actions; "307 tests" (claim; 14 test files) | V G P; **demo link is the GitHub repo** | none | 4 | 3 | 2 | 2 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/nemesis-voiceops/voiceops-controller-autonomous-voice-sre-engine |
| 77 | Radio Universe | other (entertainment) | Live AI radio station with hosts, news, 74 original songs, and listener call-ins | VAA (verified) for hosts and callers | none | News facts restricted to RSS content | V G D P (live on CF Pages with Durable Objects); only 5 commits | 3.25 | 4 | 5 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/radio-universe/radio-universe-radio-you-can-talk-to |
| 78 | Flowchart Creator for VI users (Koi Charts) | accessibility | Voice-built flowcharts for blind users, with a tactile pin-display simulator and Braille context | U-S v3 (verified) plus Gemini | Node add/rename/connect/delete | Structural chart checking; spoken confirmations | V G D P (live); **143 commits, 83 test files**, ~12.9k LOC | none | 4 | 4 | 4 | 3 | https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/midnight-ace/flowchart-creator-for-visually-impaired-users |

## 2. Top threats in this batch

### 1. Voice Action Gate (threat 5)

- **What it does.** A voice agent cannot execute an irreversible action, such as a money transfer, unless every argument is backed by a "witness" from AssemblyAI's word-level streaming transcript. The executor only accepts an `Execute` capability, and the gate is the only code that can mint one.
  - "I couldn't tell" can never become "go ahead."
  - The normalizer is a partial function that answers UNDECODABLE instead of guessing.
  - The witness set is built before the LLM's proposal is visible, so an invented number cannot pick its own evidence.
- **Why judges may like it.**
  - It has the highest reviewer scores in the batch (4.63 average). The harder reviewer gave it 4/5/5/5.
  - The framing is sharp: "change what the failure does, not how often it happens."
  - It is backed by 179 tests, a mutation-test arm, and a README that refuses to state unmeasured numbers.
  - It is one of the most intellectually rigorous submissions I have seen.
- **Weaknesses.**
  - It uses Universal-Streaming v3 only. The repo never calls the Voice Agent API, even though the README describes the VAA tool-call seam.
  - The live demo's "proposal" is built client-side (scripted), so there is no real LLM agent in the loop.
  - It is a banking demo on toy data, with no telephony, no end-to-end voice conversation, and a developer-tool feel.
- **How to differentiate.**
  - Run a real VAA conversation where the gate sits on the actual `tool.call` / `tool.result` seam.
  - Cover several action types plus a live spoken repair loop (re-ask, then read back).
  - Use real telephony and a realistic domain.
  - Show measured error rates. VAG explicitly declines to publish any.

### 2. Patchline (threat 4)

- **What it does.**
  - A reliability supervisor sits between Universal-Streaming and business tools such as refunds and address changes.
  - It blocks tool calls built on weak entity evidence and asks one scoped repair question.
  - Every recovered failure becomes a replayable regression test. Candidate AssemblyAI configs (keyterms, turn detection) must pass all regressions before promotion, with rollback.
  - It found and fixed a real `keyterms_prompt` wire-format bug.
- **Why judges may like it.**
  - It is the deepest engineering in the batch: 43 commits, 39 test files, and PRD, DECISIONS, and TESTING docs.
  - It closes the loop from failure to regression to config promotion, which appeals to AssemblyAI as a platform vendor.
  - Its "no LLM in the highest-risk path" stance is strong.
- **Weaknesses.**
  - It is an ops/dev-tool UI, not a compelling end-user story.
  - It uses Universal-Streaming plus Groq TTS instead of the Voice Agent API.
  - Polish of the video is unverified.
  - It has no reviews yet.
- **How to differentiate.** Deliver the same guard-plus-repair idea inside a native VAA agent, with a vivid end-user scenario and measured before/after numbers on real audio.

### 3. Claim intake agent that refuses to guess (threat 4)

- **What it does.** A VAA agent for insurance first-notice-of-loss (FNOL) claims. Every field goes through a `record_field` tool to a server validator that returns accepted, unconfirmed, or rejected. The agent speaks the validator's exact words.
- **Its standout story.** The author measured that keyterm-biasing the recognizer toward valid policy numbers produced false accepts: C411 was transcribed as KD4-1188, a real policy belonging to someone else. So they removed the biasing. A `/compare` page shows side by side what a naive system records versus what this one records, using real call logs.
- **Why judges may like it.**
  - It is honest, empirical, and uses the Voice Agent API natively with tool calling.
  - It has 142 tests, a deck, and a working live demo.
  - The keyterm finding is directly useful feedback for AssemblyAI.
- **Weaknesses.**
  - Single-field validation against a static `policies.json`.
  - No telephony.
  - The UI is plain Python.
- **How to differentiate.** Go beyond per-field validation to action-level gating. Add a replayable audit or evidence timeline, and handle multi-entity conversations.

### 4. RECEBE (threat 4)

- **What it does.**
  - Warehouse or delivery receiving by voice, in Portuguese or English, reconciled against a known order.
  - It asks targeted questions about ambiguous relationships ("are the damaged ones included in the total?") and handles corrections across turns.
  - It computes received, damaged, undamaged, and missing counts with deterministic arithmetic.
  - Confirmation is version-bound, so a stale "yes" cannot finalize a changed record.
- **Why judges may like it.**
  - It is very disciplined engineering: 88 commits through Sep 24, 74 test files, and an eval directory.
  - Gemini Live acts as an autonomous tester.
  - It uses several AssemblyAI products (Streaming plus LLM Gateway, with VAA referenced).
  - It is bilingual and focused on a concrete physical workflow.
- **Weaknesses.**
  - The domain is narrow and unglamorous (fictional order).
  - Spoken output is fixed Gemini TTS prompts rather than a conversational agent voice.
  - It has no reviews yet.
- **How to differentiate.** Broader action coverage, a native VAA voice loop, and a more emotionally compelling, higher-stakes scenario.

### 5. SilverLine (threat 4)

- **What it does.**
  - An elderly patient calls a real phone number (Twilio PSTN; a landline works).
  - A slow-safe VAA agent confirms clinic visits and teaches back each medication. It uses tuned turn detection (1200/3500 ms) and keyterm narrowing per call stage (clinic names, then drug names).
  - Nothing books without a full read-back and an explicit yes.
  - The family gets an HMAC-signed receipt they can verify online.
  - The repo includes proof of a live 8-minute PSTN call that cost about $0.60 of AssemblyAI time.
- **Why judges may like it.**
  - It is emotional and human, with real telephony.
  - It makes deep use of VAA-specific features: turn-detection tuning and live keyterm updates.
  - It has a measurable proof artifact.
  - Judges can toggle fast vs. patient mode in the browser demo.
- **Weaknesses.**
  - It has no tests.
  - It is small (~2k LOC).
  - It was submitted late (Sep 22), so it has no reviews yet.
- **How to differentiate.** A combination of the rigor of VAG/Patchline and the human, telephony-grade demo of SilverLine is the gap nobody in this batch fully covers.

### Honorable mentions

- **Relay.** Highest-rated field-ops entry (4.25). It uses VAA with tool-failure recovery, but its repo is 404, which could hurt it.
- **Heat Warning Agent.** A very original "comprehension, not yes" design with null-vs-false facts.
- **Radio Universe.** High originality and polish.
- **Koi Charts.** Accessibility, 143 commits.
- **Voicemed.** 4.13 reviews; deterministic triage.

### Cross-batch note

The "related apps" sidebar on these pages also surfaces two projects outside this batch that sit in exactly the same niche. Check whether they are in another batch:

- **READBACK**: VAA plus a Safe guard contract that refuses unread-back crypto transactions.
- **Tally**: "validates every voice-agent tool call against an independent speech stream … repairs mishearings … regression test", which is nearly identical to Patchline.

### Hype flags (claims the code does not support)

- **HazVox** claims VAA plus tool calling but runs on the browser Web Speech API and regex.
- **Veritas'** deployed frontend calls `localhost:8000`.
- **VerbaTrace** claims VAA tool actions but uses streaming STT plus Workers AI, in a single-commit, 12.9k-line file.
- **VANE-SPACE-SLA** shows no voice content.
- **VoiceNova's** demo URL is localhost.

## 3. Category counts (38 projects)

| Category | Count | Projects |
|---|---|---|
| transaction / action safety gate | 2 | Voice Action Gate, Patchline |
| evidence / claims / legal | 3 | Claim intake agent, Second Listen, VerbaTrace |
| field ops / inventory / logistics | 3 | Relay, RECEBE, echologic |
| industrial / worker safety | 2 | HazVox, Heat Warning Agent |
| healthcare (incl. receptionist) | 4 | appointment booking, SilverLine, Voicemed, Veritas |
| fraud / scam safety | 1 | Guard Line |
| dev tools / SRE | 4 | OpsPilot, VoiceOps Controller, BugSpeak, Speech-to-Maya |
| interview coaching | 2 | Interview Lab, Officer Parker |
| education / tutoring | 3 | Voice Language Partner, LinguSim, Voice Lab Molecular |
| accessibility | 2 | voicebridgeai, Koi Charts |
| finance | 1 | Aura SEC 10-K |
| personal assistant / productivity | 4 | TalkOS, VoiceNova, EchoAgent, LineOne |
| translation / communication | 2 | Ohun, Tourist translator |
| other | 5 | Robot Arm, SmartLink, VANE-SPACE-SLA, SahabatSuara, Radio Universe |

A broader "verify before act / refuses to guess" theme runs across categories:

- **Explicit safety or confirmation gate (7 in this batch):** Voice Action Gate, Patchline, Claim intake, RECEBE, SilverLine, OpsPilot, VoiceOps.
- **Evidence-quoted outputs (5):** Guard Line, Second Listen, Heat Warning, VerbaTrace, Voice Lab.
- **Outside this batch:** READBACK and Tally.

This niche is crowded, and its best entries are strong. Winning with it requires a clearly superior, measured, end-to-end VAA demo.

**AssemblyAI tech actually used (repos checked):**

| Tech | Repos |
|---|---|
| VAA (`agents.assemblyai.com`) | TalkOS, Claim intake, OpsPilot, SilverLine, Second Listen, Relay (bundle), echologic, Heat Warning, Voicemed, Officer Parker, Voice Lab, Radio Universe, RECEBE (partial) |
| Universal-Streaming v3 only | Voice Action Gate, Patchline, Guard Line, Veritas, VerbaTrace, VoiceOps, Koi Charts |
| Legacy / none | HazVox |
