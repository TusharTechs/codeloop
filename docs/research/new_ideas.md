# New idea research: AssemblyAI Voice Agent Hackathon 2026

Prepared 2026-09-25. Deadline 2026-09-30, so there are 5 days left. Judges are AssemblyAI staff. The likely criteria are application of technology, presentation, business value and originality.

## 0. What the competition and the platform tell us

### Competing submissions I checked (from `submissions.txt` and the lablab project pages)

Most draft pages have no description yet, so the list below covers only the pages that do.

- **Saakshi** listens to insurance and credit sales calls in India and flags IRDAI/RBI mis-selling. That takes the "mis-selling detection" idea. ([lablab](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/monster/saakshi-consent-you-can-prove))
- **Second Chair** gives private compliance whispers in multi-party regulated conversations such as financial advice. That takes the generic "compliance copilot on a live call" idea. ([lablab](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/enigma-pro/second-chair))
- **AeroGuard** monitors airport ground-control radio for ICAO clearances. That takes pilot/ATC read-back. ([lablab](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/pilotsaver/aeroguard-autonomous-airfield-voice-interceptor))
- **READBACK** checks the spoken intent behind a crypto transaction. It is part of the action-gate cluster. ([lablab](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/readback/readback))
- **AegisOR** listens to the operating room for time-outs, sponge and needle counts, and medical-lexicon keyterms. It does not cover code blue or resuscitation. ([lablab](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/testteam/aegisor))
- **Kwik 112** is a Hindi call-taker for India's 112 line that uses 43 keyterms and a human dispatcher. It does not do CPR coaching. ([lablab](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/termin8ors/kwik-112-ai-voice-call-taker-for-112))
- **Tell** detects hesitation when patients self-report medication adherence. ([lablab](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/qiqi/tell-it-wont-take-yes-for-an-answer))
- **Guard Line** detects scams on Korean phone calls. **Earshot** lets people correct robot fleets by voice. **ToneGap** audits voice agents for bias. **Officer Parker** simulates visa interviews. **Probe** is an interview tool. **Second Listen** handles investor debriefs.
- These have no content yet and could collide with ideas below: MedBrief, LifeLine Emergency, Voice Triage Agent, Dendrite CHW, VaultVoice "offline compliance interpreter", Awaaz, Callout, SafarSync Fleet Ops.
  - **VaultVoice** is the one to watch for the interpreter idea. Its title suggests it does interpreting, not auditing a human interpreter.

### AssemblyAI features worth showing off

These come from AssemblyAI's own posts ([April 2026 recap](https://www.assemblyai.com/blog/assemblyai-april-2026-recap), [multilingual blog](https://www.assemblyai.com/blog/multilingual-speech-to-text-api)). A strong pitch should use at least three of them visibly.

- **Universal-3 Pro Streaming**
  - Real-time speaker diarization.
  - Dynamic keyterm prompting of up to 1,000 terms, which can be updated mid-conversation.
  - Real-time prompting.
  - Latency under 200 ms.
  - Supports English, Spanish, French, German, Portuguese and Italian.
- **Universal-3.5 Pro Streaming** supports Hindi natively, including Hinglish code-switching.
- **Medical Mode** misses over 20% fewer medical entities, including drug names and doses.
- **Voice Agent API**
  - Speech-aware turn detection.
  - Tool calling with JSON Schema.
  - Configuration can be updated mid-session.
  - Sessions can resume within 30 seconds.
- **Word-level confidence** comes with streaming output. It gives "the ASR itself might be wrong" a principled safety story.

**Skeptic's rule for this field.** There are about 160 submissions, and many already use "LLM + keyterms + a confirmation step". To win, an entry needs three things:
1. A domain where a human-to-human spoken exchange is the actual point of failure, so voice is the problem and not just the interface.
2. A published error rate we can quote.
3. A 30-second demo where the agent catches something a human missed.

---

## 1. Raw brainstorm (26 ideas)

| # | Idea | Quick verdict |
|---|---|---|
| 1 | **CodeLoop**: live code-blue (cardiac arrest) recorder, ACLS timers and closed-loop order tracker | Keep |
| 2 | **Verbal Order Guard**: monitors phone and verbal medication orders and critical-lab calls; resolves sound-alike drug names and numbers; enforces read-back | Keep |
| 3 | **Faithful**: real-time fidelity auditor for human interpreters in police, court and hospital settings (omissions, additions, distortions) | Keep |
| 4 | **Vasooli Kavach**: borrower-side shield on loan-recovery calls (RBI Fair Practices Code violations, Ombudsman complaint pack) | Keep |
| 5 | **ThreePart**: monitors three-part communication for power-grid operating instructions (NERC COM-002-4) and rail safety-critical comms | Keep (a pivot of our Guardian idea) |
| 6 | Fireground radio monitor: Mayday, LUNAR and personnel accountability (PAR) tracking | Keep |
| 7 | I-PASS bedside nurse handover that checks the receiver's synthesis | Keep |
| 8 | Ambulance-to-ED handover (ATMIST/IMIST-AMBO) and ED pre-alert | Keep |
| 9 | Informed-consent teach-back in regional languages, with the audio-video record CDSCO requires | Keep |
| 10 | Two-person bedside voice check for blood transfusion | Keep |
| 11 | Telephone CPR coach for bystanders in Hindi | Keep |
| 12 | Conversational vigilance check for long-haul truck driver fatigue | Keep (weak) |
| 13 | Crane signalperson radio monitor (ASME B30.5 voice signals) | Drop: overlaps HazVox and our Guardian |
| 14 | Maritime VHF / IMO SMCP (Standard Marine Communication Phrases) monitor and pilot-master exchange | Drop: AeroGuard is the same pattern; no maritime audio data |
| 15 | Indian Railways line-block and track-worker protection comms | Folded into #5 |
| 16 | Witness for controlled-drug wastage (opioid diversion) | Drop: niche; a badge tap works |
| 17 | Banking-correspondent (AePS) cash read-back for illiterate customers | Drop: sits in the scam/action-gate cluster |
| 18 | Hindi voice FIR / Zero-FIR filing | Drop: SAUTI and Legal-Voice cover it |
| 19 | Checker that rights were read at arrest | Folded into #3 |
| 20 | Anaesthesia handover in the OR | Drop: AegisOR |
| 21 | Surgical count | Drop: AegisOR does it |
| 22 | Aircraft-maintenance torque and RII read-outs | Drop: inspection cluster (WalkAround and others) |
| 23 | Kitchen HACCP temperature log | Drop: low stakes |
| 24 | Wage-theft log for labour contractors | Drop: CrewVoice and VoiceCase |
| 25 | Disaster needs assessment | Drop: SAUTI |
| 26 | Medication voice-pillbox for illiterate elder-care caregivers | Drop: Tell and EverCall are adjacent |

---

## 2. Top 12: research and classification

Classes: **A** = crowded, **B** = exists but we would be meaningfully different, **C** = limited direct competition, **D** = novel.

### 1. CodeLoop: resuscitation recorder and closed-loop order tracker (Class B/C)

**Concept.** A phone or tablet in the room listens to the code team, with diarization. It does four things:
- Timestamps events such as "epi 1 mg in", "shock 200 J" and "rhythm check: VF".
- Runs deterministic ACLS timers: 2-minute CPR cycles and epinephrine every 3–5 minutes. It announces them by voice, and people can interrupt it.
- Flags spoken orders that nobody acknowledged, for example "give amiodarone 300" with no "amiodarone 300 in".
- Produces the GWTG-Resuscitation record and a debrief timeline.

**Why the problem is real**
- About 290,000 adult in-hospital cardiac arrests happen each year in the US, with roughly 25% survival ([PMC review](https://pmc.ncbi.nlm.nih.gov/articles/PMC13134658/)).
- Delays to epinephrine hurt survival, and delay rates vary by hospital from 0% to 53.8% ([Circulation](https://www.ahajournals.org/doi/10.1161/CIRCULATIONAHA.116.025459); [PubMed](https://pubmed.ncbi.nlm.nih.gov/30707123/)).
- Documentation is poor.
  - Agreement between the EHR record and an observer on epinephrine within 5 minutes had kappa 0.27, and for ETCO2 use kappa 0.04 ([PMC10672215](https://pmc.ncbi.nlm.nih.gov/articles/PMC10672215/)).
  - Only 35% of arrests met every documentation benchmark ([Redivus](https://redivus.com/2024/05/31/making-a-case-for-better-code-blue-documentation/)).
  - Paper records often miss times or use several clocks ([PMC5893915](https://pmc.ncbi.nlm.nih.gov/articles/PMC5893915/)).
- Closed-loop communication gets orders completed 3.6× faster ([El-Shafy, J Surg Educ](https://www.sciencedirect.com/science/article/abs/pii/S1931720417300387)). A video review found incomplete closed loops and parallel conversations at every level of case severity ([CJEM](https://pmc.ncbi.nlm.nih.gov/articles/PMC9002216/)).

**How it is solved today, and why that falls short**
- Human recorders scribble on paper.
- Tap-based apps exist: the Redivus Code Blue app claims 66% fewer errors in simulation ([Redivus](https://redivus.com/2019/10/14/code-blue-documentation-in-real-time/)), and UCI's Code Blue NAVI is a one-handed PWA ([GitHub](https://github.com/ALERT-Sapo/Code-Blue-NAVI)).
- Defibrillator data review tools exist (Zoll, Stryker CODE-STAT).
- A GitHub hobby project turns voice into a code report after the event ([GitHub](https://github.com/hulkbuster00134/CodeBlue)).
- Speech-based activity recognition in trauma resuscitation reaches about 87% accuracy from transcripts alone ([PMC7962594](https://pmc.ncbi.nlm.nih.gov/articles/PMC7962594/)). That is academic work, not a product.
- Tap apps still need a free pair of hands, which a code rarely has. Nobody tracks closed loops live.

**Competition in this hackathon.** AegisOR covers OR time-outs and counts, not codes. LifeLine Emergency is unknown. Whitespace is good.

**AssemblyAI fit.** It is a strong fit:
- Multi-speaker diarization in a noisy room.
- Medical Mode.
- Keyterms for drugs, joules and rhythms, updated mid-session with the patient's allergies.
- Turn detection plus interruption for spoken timer prompts.
- Word confidence: an entry with low-confidence dose words becomes "confirm dose?" instead of being logged silently.

**Honest risks**
- Real codes are chaotic, and overlapping speech will defeat diarization at times. Position it first for simulation and debrief training (every hospital runs mock codes), then for live use with a human confirming.
- In the US it would likely be regulated as clinical decision support or SaMD, so the business path goes through simulation centres first.

**30-second demo.** Play a scripted mock-code audio clip, or have three teammates act it out. The timeline fills in live, and CodeLoop speaks: "Two minutes. Rhythm check." Someone says "give epi" and nobody acknowledges it. The card turns red: "Unacknowledged: epinephrine 1 mg (00:14 ago)." At the end, the GWTG form is filled.

### 2. Verbal Order Guard (Class C)

**Concept.** It listens to a doctor-nurse phone call or a verbal order at the bedside. It does four things:
- Extracts a structured order: drug, dose, unit, route and frequency.
- Checks the order against the ISMP list of sound-alike drug pairs and against number traps such as "fifteen" versus "fifty".
- Uses word confidence to demand spell-out or digit-by-digit confirmation when the ASR itself is unsure.
- Blocks sign-off until a read-back that matches the order is heard. It does the same for critical lab values called in by phone.

**Why the problem is real**
- The Joint Commission (NPSG.02.01.01) requires read-back of verbal and phone orders and of critical results. NABH in India also requires read-back and bans verbal orders for high-alert drugs ([ISMP](https://www.ismp.org/sites/default/files/attachments/2018-03/20170518.pdf); [NABH policy example](https://sigmahospital.in/Files/MANAGEMENT_OF_MEDICATION.pdf)).
- ISMP survey: 85% of nurses received phone orders in the past year, and about 12% said more than half of all their orders were verbal ([ISMP](https://www.ismp.org/sites/default/files/attachments/2018-03/NurseAdviseERR201706.pdf)).
- Documented mishearings include Kenalog heard as ketamine and hydromorphone heard as morphine (same ISMP source).
- Sound-alike names are linked to up to 1 in 7 medication errors, and there are about 1,000 ISMP sound-alike pairs ([Prescriber/Wiley](https://wchh.onlinelibrary.wiley.com/doi/full/10.1002/psb.2121); [Simbo summary of ISMP](https://www.simbo.ai/blog/exploring-the-role-of-look-alike-sound-alike-drug-lists-in-reducing-medication-errors-in-clinical-settings-4264608/)).
- NCC MERP explicitly recommends saying "fifty... five zero" versus "fifteen... one five" and spelling drug names aloud ([NCC MERP](https://www.nccmerp.org/recommendations-reduce-medication-errors-associated-verbal-medication-orders-and-prescriptions)).

**How it is solved today, and why that falls short**
- Read-back rests on human discipline.
- Sound-alike checks run at CPOE and dispensing time, for example MedAware ([MedAware](https://www.medaware.com/look-alike-sound-alike-medications-get-an-ai-assist-to-improve-patient-safety/)). They never see the spoken moment where the error starts.
- AI scribes add a new sound-alike risk of their own ([Pharmaceutical Journal](https://pharmaceutical-journal.com/article/feature/are-electronic-prescribing-systems-increasing-the-risk-of-look-alike-sound-alike-medication-errors)).

**Competition in this hackathon.** The "read-back gate" pattern is crowded: Voice Action Gate, READBACK, sipa, Tally. AegisOR mentions pharmacology lexicons. Our difference is that we monitor a human-to-human exchange and have domain-specific sound-alike and number logic. Judges may still see it as another read-back gate.

**AssemblyAI fit.** This is the best showcase of word confidence in the list, plus Medical Mode and keyterms loaded from the patient's current medication list.

**30-second demo.** Doctor on speakerphone: "Hydroxyzine twenty-five IV." Guard shows "Sound-alike pair: hydrOXYzine / hydrALAZINE. Patient has no pruritus indication but BP 190/110. Ask for spell-out." The nurse's read-back says "fifty" instead of "fifteen", and the mismatch turns red.

### 3. Faithful: real-time fidelity auditor for interpreters (Class D)

**Concept.** A three-party exchange (officer or doctor, interpreter, subject) runs in consecutive mode.
- The agent diarizes each turn pair (source utterance and interpretation) and aligns them semantically.
- Using an LLM with quality-estimation prompts, it flags omissions, additions, substitutions and editorializing.
- Protected content (rights, allergies, "I want a lawyer", consent) is always checked. It is never a translator itself: it only audits.
- Flags go privately to the officer, judge or clinician, and the output is a fidelity report for the record.

**Why the problem is real**
- Flores et al. (Pediatrics 2003) found 31 interpreter errors per encounter on average. 63% had potential clinical consequences; 77% did when the interpreter was ad hoc. Omissions made up 52% of errors ([PubMed](https://pubmed.ncbi.nlm.nih.gov/12509547/)). Professional interpreters also err, though less often ([Ann Emerg Med 2012](https://pubmed.ncbi.nlm.nih.gov/22424655/)).
- Legal error rates range from 4% with qualified interpreters to 60% with untrained bilinguals. Mis-rendered Miranda warnings have fed wrongful convictions, as in the Santiago Ventura Morales case ([Legal Reader](https://www.legalreader.com/judicial-mistranslation-changed-the-outcome-of-a-court-case/); [Northwestern JLSP](https://scholarlycommons.law.northwestern.edu/cgi/viewcontent.cgi?article=1179&context=njlsp); [Alaska Courts](https://courts.alaska.gov/language/docs/interpreter-issues.pdf)).
- The US has more than 25 million people with limited English proficiency, and Title VI mandates language access ([Boostlingo](https://boostlingo.com/blog/medical-interpreting-trends-in-2025/)).
- India's multilingual courts and police stations routinely use ad hoc interpreters.

**How it is solved today, and why that falls short**
- Nobody monitors live. Errors are found only on appeal, if a recording exists at all.
- Vendors such as LanguageLine and Boostlingo sell AI interpreting that replaces humans ([LanguageLine](https://www.languageline.com/interpreting-services/ai-interpreting-services); [Boostlingo](https://boostlingo.com/solutions/interpreter-services/on-demand/ai-interpreter/)). They do not audit humans.
- Academic automatic interpreting-quality assessment exists only for training and grading ([Frontiers 2023](https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2023.1047753/full); [arXiv 2406.10091](https://arxiv.org/pdf/2406.10091)).

**Competition in this hackathon.** Tourist translator, VaultVoice ("compliance interpreter", no description yet) and Voice Language Partner all translate. None audits a human interpreter. The idea is novel.

**AssemblyAI fit.**
- Diarization separates the three voices.
- Spanish is fully supported in U3 Pro streaming; Hindi and Hinglish in U3.5 Pro streaming.
- Turn detection gives natural boundaries for consecutive turn pairs.
- Keyterms cover legal phrases in both languages.

**Honest risks**
- The LLM's quality estimation can produce false positives on legitimate paraphrase. Mitigations:
  - Flag only "critical meaning units" drawn from a fixed checklist: numbers, negations, rights, allergies, consent, times.
  - Show both texts side by side, so a human decides.
- Simultaneous interpreting is much harder, so scope the build to consecutive mode.

**30-second demo.** An officer reads the rights in English. The "interpreter" (a teammate) renders them into Hindi or Spanish but drops "you have the right to remain silent". A red flag appears: "OMITTED: right to silence (source 00:12, interpretation 00:18)". Then the subject says "no quiero hablar sin abogado" and the interpreter renders it as "he says he's fine to talk". A second flag appears: "DISTORTION: request for counsel".

### 4. Vasooli Kavach: borrower shield for recovery calls (Class C for the borrower side; lender-side QA is Class A/B)

**Concept.** It works in Hindi and Hinglish, live on a recovery-agent call.
- It detects violations of the RBI Fair Practices Code as they happen: calls outside 08:00–19:00, threats, abuse, contacting relatives or employers, and refusing to give identity or an authorisation letter.
- It whispers the borrower's rights to them in real time.
- It builds a timestamped evidence pack and a pre-filled RBI CMS / Ombudsman complaint.

**Why the problem is real**
- The RBI Ombudsman received 934,355 complaints in FY24, up 32.8% ([TeamLease RegTech](https://www.teamleaseregtech.com/updates/article/38942/rbi-issued-an-annual-report-of-ombudsman-scheme-2023-24/)).
- Several blogs say recovery-agent complaints were 85,281 in FY24, up 42.7%. **This is unverified against the primary RBI report**, so do not quote it on stage without checking ([freed.care](https://freed.care/blog/rbi-guidelines-recovery-agents)).
- The rules are clear and deterministic (8 am to 7 pm, no third-party contact, no abuse) ([Bajaj Finserv summary](https://www.bajajfinserv.in/rbi-guidelines-for-recovery-agents)). RBI has fined lenders for recovery harassment.

**How it is solved today, and why that falls short**
- Lender-side QA already exists: Convin, Credgenics and Gistly monitor all collection calls for compliance ([Convin](https://convin.ai/blog/how-to-simplify-compliance-check-with-ai-phone-monitoring); [Credgenics](https://www.credgenics.com/); [Gistly](https://www.gistly.ai/blog/ai-debt-recovery-collections-2026)). The lender owns that data.
- Borrowers only get blog advice to "record the call" ([Zavo](https://www.thezavo.com/insights/loan-app-harassment-india-how-to-stop)).

**Competition in this hackathon.** Scam detectors (Guard Line, AegisVoice, ScamTrap, SafeCall) and Saakshi, which covers the RBI and IRDAI space from the lender's side. Judges may lump this in with "scam call detection".

**Honest risks**
- Android 10 and later and iOS block third-party apps from recording calls. Workarounds are a Twilio bridge or conference number, or a second device on speakerphone. This is a real production blocker.
- Business model is weak: borrowers won't pay. Possible routes are NGO or legal-aid partners, or selling to regulators.

**30-second demo.** A simulated call at 21:40 with the agent speaking Hinglish: "tumhare office mein bata denge". Banners appear: "VIOLATION: third-party disclosure threat" and "VIOLATION: outside permitted hours". A whisper tells the borrower: "Ask for his ID and authorisation letter." The complaint PDF is generated.

### 5. ThreePart: three-part communication monitor for grid and rail control rooms (Class C; the pattern is adjacent to AeroGuard)

**Concept.** It listens to dispatcher-to-field (or reliability coordinator-to-operator) recorded lines.
- It extracts each Operating Instruction: device ID, action and state.
- It verifies that the receiver repeats it back and the issuer confirms it.
- It flags wrong device IDs by checking them against the switching order and the station's keyterm list.
- It produces NERC COM-002-4 compliance evidence automatically.

This is our Guardian idea, moved to where there is a regulatory buyer.

**Why the problem is real**
- NERC COM-002-4 requires three-part communication in emergencies. Its accepted evidence explicitly includes voice recordings and transcripts. One settlement cost $2.3M ([NERC standard](https://www.nerc.com/globalassets/standards/reliability-standards/com/com-002-4.pdf); [White & Case](https://www.whitecase.com/insight-alert/nerc-case-notes-reliability-standard-com-002-4)).
- Switching errors, such as energizing a grounded line or operating the wrong breaker, often stem from verbal misunderstanding ([Incident Prevention](https://incident-prevention.com/blog/three-way-communication-for-utility-workers/); [SPP human error paper](https://spp.org/documents/18058/human%20error%20in%20electric%20utility%20operation.pdf)).
- In GB rail, safety-critical comms contributed to about 17% of incidents, and up to 90% in some operational contexts ([RSSB](https://www.rssb.co.uk/standards/using-standards/latest-updates-to-standards/spoken-safety-critical-communications)).
- About 1,000 Indian Railways trackmen died per year in 2017–19, and failed line-block repeat-backs are a known cause ([The Caravan](https://caravanmagazine.in/labour/track-maintainer-deaths-indian-railways); [Network Rail](https://safety.networkrail.co.uk/frontline-safety-critical-communications/)).

**How it is solved today.** Recording plus manual sample audits, plus training such as RSSB RED videos. I found no product for automated three-part compliance scoring.

**Competition in this hackathon.** AeroGuard (airfield), the action-gate cluster and HazVox. It is less original to judges, but it has the clearest buyer and the clearest penalty.

**30-second demo.** Dispatcher: "Open breaker 52-14 at Maple substation." Operator repeats: "Open 52-41 at Maple." The line turns red: "Repeat-back mismatch 52-14 ≠ 52-41". The dispatcher then says "correct" anyway, and a second flag appears: "Issuer confirmed an incorrect repeat-back (COM-002-4 R5)".

### 6. Fireground Mayday / accountability radio monitor (Class B)

**Why the problem is real.** NIOSH line-of-duty-death reports repeatedly cite Maydays that nobody heard or acknowledged ([Fire Engineering](https://www.fireengineering.com/firefighting/firefighter-maydays-niosh/); [FirefighterCloseCalls](https://www.firefighterclosecalls.com/report-firefighters-mayday-missed-lodd-lawsuit-radio-traffic-the-secret-list/)).

**Existing products.** Motorola's Dispatch Assist does real-time AI transcription of radio traffic. Versaterm Adashi handles accountability. Radios have man-down accelerometers ([Fire Apparatus](https://www.fireapparatusmagazine.com/equipment/firefighter-radio-communication-best-practices-for-multialarm-incidents/); [Versaterm](https://www.versaterm.com/solution/adashi-cc/)).

**Why it ranks lower.** Radio (P25) audio quality is poor, it needs hardware integration, and missing one Mayday is catastrophic. It is hard to build credibly in 5 days.

### 7. I-PASS bedside handover with receiver-synthesis check (Class B)

**Why the problem is real.** I-PASS cut medical errors by 23% and preventable adverse events by 30% across 10,740 admissions (NEJM 2014) ([NEJM](https://www.nejm.org/doi/full/10.1056/NEJMsa1405556)). The Joint Commission attributes about 80% of serious errors to miscommunication at handoff ([I-PASS Institute](https://www.ipassinstitute.com/evidence)).

**Existing products.** ShiftWhisper, the Handoff AI app, Epic handoff tools, and academic "AI patient report templates" ([ShiftWhisper](https://shiftwhisper.com/); [App Store](https://apps.apple.com/us/app/handoff-ai/id6761528127); [PMC13239256](https://pmc.ncbi.nlm.nih.gov/articles/PMC13239256/)).

**How we would differ.** Check the receiver's spoken synthesis ("S" in I-PASS) against the giver's content live, and catch items that were dropped.

**Competition in this hackathon.** MedBrief, MediScribe and Veritas probably overlap.

### 8. Ambulance-to-ED handover (ATMIST) and pre-alert (Class B)

**Why the problem is real.** Only 72.9% of verbally handed-over key prehospital data was documented by ED staff ([PMC2660073 and related](https://pmc.ncbi.nlm.nih.gov/articles/PMC2660073/)).

**Existing products.** ImageTrend AI Assist dictates the ePCR, and Pulsara provides real-time prehospital-to-hospital links ([ImageTrend](https://www.imagetrend.com/blog/how-imagetrend-ai-enables-smarter-emergency-response/); [Pulsara](https://www.pulsara.com/eso)).

**Competition in this hackathon.** Kwik 112, LifeLine and Voice Triage are adjacent.

### 9. Consent teach-back and audio-video consent record, India (Class B)

**Why the problem is real.** India's New Drugs and Clinical Trials Rules 2019 require an audio-video record of informed consent, including the subject's understanding, for vulnerable subjects in trials of new chemical entities ([CDSCO NDCT Rules](https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2022/new_DC_rules/NEW%20DRUGS%20ANDctrS%20RULE,%202019.pdf); [Science 2014](https://www.science.org/doi/10.1126/science.344.6180.150-b)). Teach-back improves comprehension ([PMC9617437](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9617437/)), and a surgical consent audit in Northeast India found understanding tracks with use of the local language ([PMC13429079](https://pmc.ncbi.nlm.nih.gov/articles/PMC13429079/)).

**Existing products.** eConsent vendors: Medidata, Signant, and Indian CTMS audio-video modules.

**Competition in this hackathon.** Saakshi's tagline "Consent You Can Prove" collides on messaging.

### 10. Two-person bedside voice check for blood transfusion (Class C)

**Why the problem is real.** SHOT 2024 reported 2 deaths where collection and bedside checks were skipped. About 22% of wrong-blood events come from patient-ID errors, and 83.1% of reports are avoidable errors ([SHOT 2024](https://www.shotuk.org/shot-reports/annual-shot-report-2024/); [IBCT chapter](https://www.shotuk.org/wp-content/uploads/2025/07/9.-Incorrect-Blood-Component-Transfused-IBCT-2024.pdf)).

**Existing products.** Barcode bedside systems such as Haemonetics BloodTrack.

**Skeptic view.** Barcodes beat voice on reliability. Voice necessity is only moderate, mainly in hospitals without barcodes (LMICs).

### 11. Hindi telephone-CPR coach for bystanders (Class B)

**Why the problem is real.** Bystander CPR in India runs at 1.3–9.8%. In a 108 T-CPR pilot in Telangana, only 20% of instructed bystanders performed CPR ([IJCM/PubMed](https://pubmed.ncbi.nlm.nih.gov/32905051/); [Indian Heart J](https://www.sciencedirect.com/science/article/pii/S0019483223001402)).

**Assessment.** Voice is structurally necessary (hands on the chest) and the demo would be emotional. It is regulated and liability-heavy, and Kwik 112 and LifeLine are adjacent.

### 12. Conversational fatigue check for truck drivers (Class B)

**Why the problem is real.** India had 172,890 road deaths in 2023 ([MoRTH 2023](https://morth.gov.in/backend/documents/uploaded/Road-Accident-in-India-2023-Publications.pdf)). About half of truck drivers keep driving while sleepy ([SaveLIFE via Autocar](https://www.autocarpro.in/news-national/most-truck-drivers-in-india-are-sleep-deprived-compromise-road-safety-savelifes%C2%A0hardhitting-report-55710)). There is research on LLM conversation for alertness ([arXiv 2510.25421](https://arxiv.org/html/2510.25421v2)).

**Existing products.** Camera driver-monitoring systems (Netradyne, Seeing Machines, Lytx) dominate.

**Assessment.** It is hard to demo, and "detecting fatigue from voice" is a weak basis for a safety claim.

---

## 3. Scoring (1–10)

Column key: Sev = problem severity, Mkt = market size, Freq = frequency, Voice = voice necessity, AAI = AssemblyAI fit, Tech = technical depth, Orig = originality, White = whitespace against the ~160 submissions, Demo = demo impact, Biz = business potential, Soc = social impact, Prod = production potential, Feas = feasibility in 5 days, Safe = safety/reliability story, **Overall** = overall hackathon potential.

| # | Idea | Class | Sev | Mkt | Freq | Voice | AAI | Tech | Orig | White | Demo | Biz | Soc | Prod | Feas | Safe | **Overall** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CodeLoop (resuscitation closed-loop) | B/C | 10 | 6 | 5 | 10 | 9 | 8 | 8 | 8 | 10 | 6 | 8 | 5 | 8 | 8 | **9** |
| 3 | Faithful (interpreter fidelity) | D | 9 | 7 | 8 | 10 | 8 | 9 | 10 | 9 | 9 | 7 | 9 | 5 | 6 | 7 | **9** |
| 2 | Verbal Order Guard | C | 9 | 7 | 8 | 9 | 10 | 8 | 7 | 6 | 8 | 7 | 7 | 6 | 8 | 9 | **8** |
| 5 | ThreePart (NERC/rail read-back) | C | 9 | 5 | 9 | 10 | 9 | 7 | 6 | 5 | 7 | 7 | 6 | 6 | 8 | 8 | **7** |
| 4 | Vasooli Kavach (recovery calls) | C | 8 | 8 | 8 | 9 | 8 | 6 | 7 | 5 | 8 | 4 | 9 | 5 | 8 | 7 | **7** |
| 7 | I-PASS synthesis check | B | 8 | 8 | 10 | 8 | 8 | 6 | 5 | 5 | 6 | 7 | 7 | 7 | 9 | 7 | 6 |
| 9 | Consent teach-back and AV record | B | 7 | 6 | 7 | 8 | 8 | 6 | 6 | 5 | 7 | 6 | 8 | 6 | 8 | 7 | 6 |
| 11 | Hindi telephone-CPR coach | B | 10 | 4 | 3 | 10 | 7 | 6 | 5 | 5 | 9 | 3 | 9 | 4 | 8 | 6 | 6 |
| 10 | Transfusion voice double-check | C | 9 | 5 | 7 | 6 | 7 | 5 | 7 | 8 | 7 | 4 | 7 | 4 | 9 | 8 | 6 |
| 6 | Fireground Mayday monitor | B | 10 | 5 | 4 | 10 | 7 | 7 | 6 | 7 | 8 | 5 | 8 | 4 | 6 | 6 | 6 |
| 8 | Ambulance-to-ED handover | B | 8 | 6 | 8 | 9 | 8 | 6 | 5 | 5 | 7 | 5 | 7 | 5 | 8 | 7 | 5 |
| 12 | Driver fatigue check | B | 9 | 7 | 9 | 7 | 6 | 6 | 5 | 7 | 4 | 6 | 8 | 4 | 7 | 4 | 4 |

### One-line reasons for the major scores

**CodeLoop**
- Demo 10: a live timeline plus a red "unacknowledged order" card is instantly understood.
- Voice 10: nobody's hands are free during a code.
- AAI 9: it uses diarization, Medical Mode, keyterms and interruption together.
- Freq 5: each hospital has many codes, but each clinician sees few.
- Prod 5: the path runs through simulation training before it can be used live and regulated.

**Faithful**
- Orig 10: I found no product or submission that audits human interpreters live.
- Feas 6: aligning meaning across languages is the hard part, so restrict it to consecutive mode and a fixed list of critical meaning units.
- Soc 9: the users are defendants and patients who cannot tell that they were mistranslated.

**Verbal Order Guard**
- AAI 10: it is the most natural showcase of word confidence (the ASR can mishear too).
- White 6: judges have already seen several read-back gates.

**ThreePart**
- Biz 7: the buyer is regulated and the fine is $2.3M.
- Orig/White 5–6: AeroGuard and the action-gate cluster dilute it.
- It reuses the Guardian work.

**Vasooli Kavach**
- Soc 9: the victims are vulnerable borrowers.
- Biz 4: no one on the borrower side pays.
- Prod 5: phone operating systems block call recording.
- White 5: it looks like "scam detection" at first glance.

---

## 4. Recommendation

Pick **CodeLoop** or **Faithful**.

- **CodeLoop** is the safer path to #1: high impact, feasible, and the most AssemblyAI features visible at once.
- **Faithful** has the higher ceiling on originality but more technical risk. Faithful should use Spanish-English for the core demo (U3 Pro streaming, most stable) and add a Hindi-English segment with U3.5 Pro to show the India and code-switching angle.

Things that apply to either:

- **Reliability story.** The LLM never decides. Deterministic state machines own the timers and the closed-loop or protected-content checklists. The LLM only extracts and aligns. Words with low confidence escalate to a human.
- **Presentation.** Open with the published statistic (kappa 0.27 on epinephrine timing, or 31 interpreter errors per visit). Then do a live catch within 30 seconds. Close on the evidence export.
- **Existing ideas.** VoiceCase collides with "Voice Case - The Glasshouse", VerbaTrace, EvidenTurn and ClaimVoice. Guardian collides with HazVox, Voice Action Gate and Earshot. If the team wants to reuse Guardian code, reposition it as ThreePart (NERC COM-002-4), which has a buyer and a penalty.
