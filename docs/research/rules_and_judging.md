# AssemblyAI Voice Agent Hackathon (lablab.ai), rules and judging

Researched 2026-09-25. Main source: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon (abbreviated **[EVT]** below). The page is Next.js/Builder.io and its content lives in the RSC payload (`self.__next_f`), which is where the data below came from. The subpages `/rules`, `/faq`, `/guide`, `/resources`, `/prizes`, `/judges` and `/schedule` all return the generic lablab shell, so they have no content of their own.

Legend: **VERIFIED** means it was read directly from a source. **INFERRED** means it is my reading of the evidence. **UNVERIFIED** means it came from a third party or could not be confirmed.

---

## 1. Deadline — VERIFIED
- Event config: `startAt 2026-09-01T15:00:00Z`, `endAt 2026-09-30T15:00:00Z` [EVT embedded event JSON; also `https://lablab.ai/api/v4/assemblyai-voice-agent-hackathon/live-stats` → `event.endAt`].
- The schedule timeline lists "End of Submissions!" at **Wed Sep 30 2026 19:00 GMT+0400** [EVT].
- **Deadline = 2026-09-30 15:00 UTC = 20:30 IST = 08:00 PDT = 11:00 EDT.**
- Late ("manual") submission is possible for 6 hours after the end, but only with a valid reason and prior approval from organizers or mentors (https://lablab.ai/hackathon-rules). Don't plan around it.
- Registration stays open for the whole window. The deadline is the same for everyone [EVT].
- Live stats at 2026-09-25 09:47Z: 3,773 participants, 1,122 teams, **147 submitted, 78 drafts**, and +19 submissions in the last 24h (live-stats API).

## 2. Eligibility (India remote) — VERIFIED plus INFERRED
- "Fully online hackathon. Join and build from anywhere in the world." [EVT]
- lablab Terms §3A: you must be **18+**. Terms §11: you must not be located in or resident of a US-sanctioned country (examples given: North Korea, Iran, Cuba, Russia) (https://lablab.ai/terms-of-use). **India is not restricted, so remote participation from India is OK** (INFERRED from those terms. No India-specific rule exists).
- Organizers/staff can take part but can't win prizes. Teams that include lablab staff are excluded from judging (https://lablab.ai/hackathon-rules, https://lablab.ai/guide FAQ).
- Company email is encouraged but not required [EVT].
- Prize payout (Terms §17, https://lablab.ai/terms-of-use): prizes go **to individuals**, in USD by SWIFT for non-US winners. Winners need the W-8BEN form, a government photo ID and a bank account in their own name, all within 90 days. **30% US withholding applies to non-US winners unless a treaty applies and a US TIN is provided.** (UNVERIFIED: whether the US–India treaty reduces withholding on prize income. Assume that 30% is withheld.)

## 3. Prizes — VERIFIED (with a discrepancy)
- Hero text: "$10,000 Prize Pool ($5k cash + $5k in AAI credits)" [EVT].
- Prizes section: **"5 winners · $1,000 cash + $1,000 in API credits each"**, repeated as "Five winners will each receive $1,000 in cash and $1,000 in API credits." [EVT, Prizes block]
- **There is no 1st/2nd/3rd prize difference. Winners 01–05 get identical prizes.** Winner 01 gets a highlighted card only. `eventPrizes: []` in the event JSON.
- Fine print: prizes depend on eligibility. Rules and prizes may change. **"Submissions must be original and MIT-compliant."** Payout can take up to 90 days [EVT, and Terms §16: "All submissions … must be original work, open source, and compliant with the MIT License unless specified otherwise"].
- Past lablab results use positions `WINNERS / TOP_2 / TOP_3 / FINALISTS` (live-stats `winners[].position` for past events). A ranking may still be published even though the prize amounts are equal (INFERRED).

## 4. Judging criteria and weights — VERIFIED (no weights published)
The event page "Judging criteria" block [EVT] and the rule book (https://lablab.ai/hackathon-rules) list four criteria:
1. **Application of Technology**: "How effectively the chosen model(s) are integrated into the solution."
2. **Presentation**: "The clarity and effectiveness of the project presentation."
3. **Business Value**: "The impact and practical value, considering how well it fits into business areas."
4. **Originality**: "The uniqueness and creativity of the solution, highlighting approaches and ability to demonstrate behaviors."
- **No weights are published anywhere.** Assume equal weighting (INFERRED).
- The lablab platform has per-criterion numeric scores with min/max ranges. Its i18n strings include "Score for {key} must be between {min} and {max}" and "Unknown criterion key" [EVT bundle]. Judges score each criterion separately (INFERRED).
- Lablab's own guidance on what scores well (https://lablab.ai/guide/how-to-win-an-ai-hackathon):
  - **Application of Technology**: the demo works, the GitHub repo is real with commits spread across the event window, the demo is deployed and accessible, and the AI is meaningfully integrated ("not just a chatbot wrapper").
  - **Presentation**: clarity over production value. Suggested video structure: 0:00–0:30 problem, 0:30–2:30 live demo, 2:30–4:00 business case/TAM/revenue, 4:00–5:00 team and roadmap. Slides should be at most 8–10 pages.
  - **Business Value**: a specific target user, a TAM figure, a revenue model, and "why this couldn't be built without AI".
  - **Originality**: a fresh angle, not "an existing product with a chatbot bolted on".
  - Named mistakes: a local-only demo "scores as if it doesn't work", and an empty repo with one final push "raises red flags".
- The submission guidelines (https://lablab.ai/delivering-your-hackathon-solution) also say to include TAM/SAM, revenue streams, a competitor analysis/USP, and scalability.
- For comparison, the earlier AssemblyAI-run challenges used different criteria:
  - DEV.to 2025 and 2024: "Use of underlying technology, Usability & UX, Accessibility, Creativity" (https://dev.to/challenges/assemblyai-2025-07-16).
  - Vapi x AssemblyAI NYC: "Effective use of Universal Streaming capabilities" and "conversation quality" (https://luma.com/dqrh7rpb).
  - AssemblyAI clearly values visible use of its own features (INFERRED).

## 5. Judges — VERIFIED list, affiliations UNVERIFIED
The event JSON `eventRoles` lists 21 judges and 1 speaker [EVT]. Titles are shown as given. **No company is listed for any of them, and none is identifiable as AssemblyAI staff from the lablab data.**

| Name | Title (as listed) | LinkedIn |
|---|---|---|
| Bhargavi Vepuri | Director | linkedin.com/in/bhargavi-vepuri |
| Vasu Raj Jain | Senior Software Engineer | linkedin.com/in/vasujain00 |
| Dharmendra Singh | Senior Development Manager | linkedin.com/in/dharma-singh |
| Sanem Avcil | — | linkedin.com/in/sanemavcil |
| Shaktesh Pandey | Founder | — |
| Shweta Chauhan | SDE | linkedin.com/in/swec-969022236 |
| Haris Jalal | — | — |
| Vishal Paul | Senior Software Engineer | — |
| Sriharsha Makineni | Sr Business Engineer | linkedin.com/in/sriharshamakineni |
| Amit Singh | AVP | linkedin.com/in/amit-singh-57980030 |
| Anil Mandloi | — | — |
| Suresh Kumar Gunasekaran | Senior Software Engineer | linkedin.com/in/suresh89 |
| Nandita Krishnan | — | — |
| Nalini Garg | Associate Vice President | linkedin.com/in/nalini-garg-427278136 |
| Andrii Stetsenko | Chief Architect | linkedin.com/in/andrii-stetsenko-92243a52 |
| Kumar Shivendu | Core DB Engineer | — |
| Neeraj Kumar Singh Beshane | Staff Security Infra Engineer | linkedin.com/in/neerajkumarsinghb |
| Mallika Rao | Engineering Leader | linkedin.com/in/mallikarao |
| Nicole Hao | Founding Engineer | linkedin.com/in/nicolehao34 |
| Neha Manjunath | Research Scientist | — |
| Vipul Jain | — | linkedin.com/in/vipulj169 |

- Speaker: Andrea Marazzi (lablab profile `uffaaaa`, no role given).
- INFERRED: this is lablab's usual pool of volunteer industry judges, mostly senior engineers and managers, many apparently India-based. With 21 judges and about 225 entries, each project is probably seen by only a few judges, likely in a preliminary round and then a finalist round. Past lablab events show FINALISTS/TOP_3/WINNERS tiers. So the first 30–60 seconds of the video and the cover and short description matter a great deal.
- Several judges have security and infrastructure backgrounds (Staff Security Infra Engineer, Core DB Engineer, Chief Architect). Pieces like "API key never reaches the browser" and "deterministic checks around the LLM" are likely to land well (INFERRED).
- AssemblyAI staff may take part in final selection without being listed. The 2024 AssemblyAI NYC hackathon was judged by its VP Marketing, a Senior ML Developer Advocate and its Head of DevRel (https://www.assemblyai.com/blog/top-speech-ai-projects-and-winners-at-2024-assemblyai-hackathon). (UNVERIFIED for this event.)

## 6. Community votes / likes / "event points" — INFERRED, NOT a stated criterion
- None of the four criteria mentions votes or likes [EVT], [rule book].
- The rule book does say "gaming the voting system" leads to immediate disqualification (https://lablab.ai/hackathon-rules). So likes exist as a community feature and manipulating them is a serious risk.
- "Points toward the lablab.ai community leaderboard" are a recognition perk, not a judging input (https://lablab.ai/guide/ai-hackathons).
- Evidence from past lablab events (live-stats API `winners` for each event slug) shows **likes correlate poorly with winning**:
  - IBM Bob hackathon: TOP_2 "Atlas" had **0 likes**.
  - Bright Data hackathon: "ConsumerIQ" had 52 likes but was only a FINALIST, while two WINNERS had 2–5 likes.
  - ElevenLabs hackathon: the winner had 5 likes, and TOP_3 had 7.
- Conclusion (INFERRED): judges' scores decide. Likes at most break ties or raise visibility. The current like leaders (SAUTI 11, Siberia 9, CyberVoice 9) are not guaranteed anything.

## 7. Required deliverables — VERIFIED
The event page "What to submit" block [EVT], the rule book (https://lablab.ai/hackathon-rules), the submission guidelines (https://lablab.ai/delivering-your-hackathon-solution) and the guidelines article (https://lablab.ai/ai-articles/hackathon-guidelines) together require:
- **Project title** (max 50 characters per the guidelines article). **Short description ≤255 characters.** **Long description ≥100 words.** Technology and category tags. The submission form has "categories", such as "Voice Assistant" seen on LoudEnough. This event has no tracks (`eventTracks: []`, live-stats `tracks: []`).
- **Cover image**: PNG/JPG, 16:9.
- **Video presentation**: **5 minutes maximum**, MP4 (the uploader also accepts MOV), **under 300MB**. It is uploaded to lablab storage. Suggested flow: intro, walk through the slides, then show the product working.
- **Slide presentation: PDF** ("MP4 and PDF formats are mandatory", rule book).
- **Public GitHub repository**: mandatory. A private repo means judges "won't be able to fully review your work, which may lower your overall score".
- **Demo application platform** plus **application URL**: "required for interactive evaluation". Recommended hosts are Streamlit, Replit or Vercel. Other platforms are selectable; LoudEnough uses `demoPlatform: VERCEL`, and other entries use Fly.io and others.
- Code must be original, open-source and **MIT-compatible** [EVT, Terms §16].
- The `breaksRules` flag exists on submissions. Moderators can mark rule violations (seen in the submission JSON).
- The guide FAQ lists "working prototype that others will be able to use online + video + pitch deck" as the minimum (https://lablab.ai/guide).
- Pre-existing code: usually OK, provided "the core AI-powered functionality was built during the event window" (https://lablab.ai/guide/ai-hackathons, the generic FAQ. There is no event-specific rule).

## 8. Required AssemblyAI products — VERIFIED
- "Every participant builds on AssemblyAI." / "Every project is built on AssemblyAI." [EVT]
- Challenge: "Build a voice agent using AssemblyAI's real-time voice AI technology." There are **two allowed paths** [EVT, Challenge block]:
  1. **Voice Agent API**: an end-to-end voice agent over a single connection. It includes STT powered by **Universal-3 Pro**, LLM routing and voice output, turn-taking/VAD, and **JSON-Schema tool calling**.
  2. **Realtime Speech-to-Text API** (Universal-Streaming over WebSocket): sub-second, multilingual, "**Bring your own LLM and text-to-speech**".
- The resources list also links **LLM Gateway** docs (https://www.assemblyai.com/docs/llm-gateway/quickstart). It is optional, not required.
- Free credits come from the sign-up link on the page, which uses the `utm_campaign=lablab_virtual_hackathon` credit grant.
- INFERRED: a project that uses only batch/async transcription is weaker. The brief is explicitly "real-time" and "voice agent". Examples are a WhatsApp voice-note pipeline or offline processing.

## 9. Restrictions on other APIs/LLMs — VERIFIED (none stated)
- No restriction is stated. The Realtime STT path explicitly invites your own LLM and TTS [EVT].
- The most-used tech tags among current submissions (live-stats `techStack`) are AI/ML API 65, Vercel 44, Anthropic Claude 41, Claude Code 38, Assistants API 35, Antigravity 35, Codex 25, Gemini 25, OpenAI 18 and Groq 17.
- Caveat (INFERRED): the "Application of Technology" score is about how well *the chosen models* are integrated. A project where AssemblyAI is a thin STT front end to someone else's stack will likely score lower than one that uses AssemblyAI-specific features. Examples of those features: turn detection, barge-in, keyterms prompting, streaming diarization/speaker revisions, Voice Agent tool calls, LLM Gateway.
- Terms-of-use issue (INFERRED): AssemblyAI is a cloud API. Claims of "fully offline/on-device AssemblyAI" (see VaultVoice in drafts.md) are technically dubious.

## 10. Team size — VERIFIED
- "Teams consist of 1-6 people." [EVT Guidelines block]. The event config has `teamMembersLimit: 6` [EVT JSON]. An HTML comment on the page flagged 1–6 as boilerplate "NOT confirmed", but the config confirms 6.
- At most **3 members can have submission permission** [platform message in EVT bundle].
- Everyone must be on a lablab team, solo entrants included. Discord must be connected before creating or joining a team (https://lablab.ai/guide FAQ, platform messages).

## 11. Sponsor-specific requirements / bonuses — VERIFIED (none)
- There are no bonus prizes, special tracks or sponsor bonus criteria (`sponsors: []`, `eventPrizes: []`, `eventTracks: []` [EVT JSON]).
- The only sponsor-specific rule is "build on AssemblyAI", using the Voice Agent API or Realtime STT.
- There are no discussion-thread rule clarifications. The discussion board (`/api/v4/assemblyai-voice-agent-hackathon/discussion/threads?page=1&limit=50`) has only 4 threads, all participant posts: UrbeVoice, CVoxPuzzle, a pivot note, and "how to create a team".
- The social feed (`/api/v4/.../social-feed`) has only lablab promo posts. The 2026-09-23 LinkedIn post confirms "$10,000, online, Sep 1-30… registration stays open". The 2026-09-22 post covers a lablab tutorial on Voice Agent API **HTTP tools** (a dental receptionist example). That hints at an API pattern the organizers favour (INFERRED).
- A third-party listing (https://internshala.com/competitions/assemblyai-voice-agent-hackathon-2026/) says "registration closes Aug 31". **This conflicts with the official page. Ignore it (UNVERIFIED/incorrect).**

---

## 12. Past AssemblyAI hackathons: winners and what they reveal

| Event | Winners | Pattern |
|---|---|---|
| **DEV.to AssemblyAI Voice Agents Challenge**, Jul 2025 (Universal-Streaming required). Criteria: tech use, UX, accessibility, creativity. https://dev.to/devteam/congrats-to-the-assemblyai-voice-agents-challenge-winners-1ppk, https://www.assemblyai.com/blog/these-7-voice-ai-projects-just-blew-us-away | **Wynnie**: multilingual (50+ languages) voice shopping agent with deal-hunting and checkout, multi-agent, accessibility for elderly users (Business Automation). **Hogwarts Spell Caster**: spoken spells become keystrokes in a game, showing off sub-300ms latency (Real-Time Performance). **AI✧Debate**: real-time debate partner with domain knowledge (Domain Expert). Shortlist: Voice of Voiceless (speech-impaired), CareSetu (health scheduling), Elder Care Companion, academic coach. | AssemblyAI praised projects where **latency visibly mattered**, plus **multilingual/auto language detection**, **accessibility / underserved users**, and **end-to-end task completion**. A debate/pushback agent has already won once. |
| **DEV.to Winter Speech-to-Text Challenge**, Dec 2024. https://www.assemblyai.com/blog/dev-to-x-assemblyai-winter-speech-to-text-challenge-winners | **Insightview**: journalist interview workflow with speaker ID, highlights and article drafts. **SpeechCraft**: real-time speech analytics dashboard. **ReportSOS**: emergency reporting with a dispatcher dashboard (LeMUR). | Structured output from speech, **dispatcher/emergency** themes, and journalist tooling (compare Nonius in the drafts). |
| **AssemblyAI NYC Hackathon 2024** (in person). Judges: AssemblyAI VP Marketing, Sr ML DevRel, Head of DevRel. https://www.assemblyai.com/blog/top-speech-ai-projects-and-winners-at-2024-assemblyai-hackathon | **1st Dealty**: real-estate deal calls transcribed live, with entity extraction **auto-filling application forms in real time**. **2nd Muse**: voice mental-health journaling ("we'd download it immediately"). Special mention: Say What (audio guessing game). | A **concrete B2B workflow** turned into structured data instantly, with live form-fill visible on screen, and a polished consumer app the judges would actually use. |
| **AssemblyAI $50k Winter Hackathon**, Dec 2022, Devpost (judges included Nat Friedman and Daniel Gross). https://www.assemblyai.com/blog/winners-and-honorable-mentions-assemblyai-50k-winter-hackathon | 1st Superpaint (SD inpainting), 2nd Toy Story Creator, **3rd OperatorAI (911 call triage/dispatch)**, Best AssemblyAI: Pupil.ai (video-transcript tutor). | 911/dispatch triage keeps placing. |
| **Vapi x AssemblyAI NYC Voice Agent Hackathon** (Luma). https://luma.com/dqrh7rpb | Winners not published. Criteria: technical implementation, **effective use of Universal Streaming**, UX/conversation quality, business potential. | Conversation quality and use of AssemblyAI features are judged explicitly. |
| **lablab ElevenLabs AI Hackathon** (voice, lablab judges). Live-stats API `eleven-labs-ai-hackathon` | WINNER: EASY DX (game voiceovers, B2B cost-saving). TOP_2: Voxa AI (SaaS customer-service voice bot). TOP_3: Debated-AI. Finalists: Patient Simulator, Audio-Visual Novel. | lablab judges reward a **clear business buyer and cost savings**. Debate and training simulators recur. |

Other lablab winners (live-stats API for `ibm-bob-hackathon`, `brightdata-ai-agents-web-data-hackathon`, `complete-ai-agent-hackathon`):
- Pedigree: cryptographic provenance for AI code.
- Verdict: OFAC due diligence with cited verdicts and audit PDFs.
- OnboardEase.

Together these show that lablab judges favour **B2B, compliance/evidence/auditability, "trust" features, and quantified value**, with little regard to likes.

**Past-winner takeaways (INFERRED):**
1. Show a **concrete workflow in a named business vertical**, where voice becomes structured, actionable output live on screen, and quantify the time or money saved.
2. **Visibly exercise AssemblyAI-specific capabilities**, with latency/turn-taking/barge-in you can see in the demo. Useful features: keyterms, diarization, multilingual/code-switching, and Voice Agent tool calls.
3. **Trust and safety scaffolding** (evidence citations, deterministic guards, human-in-the-loop) fits this year's senior-engineer and security-heavy judge panel.
4. **Accessibility and underserved or multilingual users** is a recurring AssemblyAI favourite.
5. The themes most saturated in this event are emergency/911 triage, front desk/receptionist, interview coach, restaurant ordering and farmer advisory, going by the titles in submissions.txt. Originality points are harder to earn there.
