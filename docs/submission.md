# lablab.ai submission text

## Title (≤ 50 characters)

CodeLoop: the voice recorder for cardiac arrests

## Short description (≤ 255 characters)

A voice agent for resuscitation teams. It hears the whole room, logs every drug, shock and rhythm with the exact words, runs the ACLS clock and speaks up when an order goes unconfirmed or a dose is read back wrong. Built on AssemblyAI.

## Long description (600–2000 characters)

During an in-hospital cardiac arrest the whole team works by voice. Hands are on the chest, the airway and the syringes while orders fly across the room. In filmed resuscitations only 26% of spoken orders were repeated back, and those were completed 3.6 times sooner. Someone has to stop caring for the patient to write, and no tool notices an order nobody confirmed.

CodeLoop is the recorder that never looks away. A tablet on the crash cart streams the room to AssemblyAI Universal-3.5 Pro with speaker labels, Medical Mode, ACLS keyterms and Hindi and English code-switching. A deterministic grammar turns speech into events that quote the exact words they came from. Every order becomes a loop: ordered, read back, given. If nobody confirms, the card turns amber and CodeLoop says so. If a different dose is read back, it turns red and CodeLoop says "Check dose." It keeps the ACLS clock and answers "CodeLoop, last epi?" from its own record. Its voice runs on the AssemblyAI Voice Agent API: it waits for a gap and stops the instant a clinician talks over it.

After the code, the Code Record scores quality against AHA targets, a second listen with async Universal-3.5 Pro re-checks every event, and a hands-free spoken debrief on the Voice Agent API quotes facts through tool calls and saves the team's lessons in their own words.

Models help understand speech; deterministic code decides every state, timer and spoken number, and every entry is hash-chained. On held-out mock codes committed before measuring: precision 0.96, recall 0.88, 16 of 17 loop outcomes. Medical Mode and keyterms raised drug and dose accuracy from 78% to 96%.

First market: simulation centres and mock-code debriefs. Over 290,000 adult in-hospital cardiac arrests happen each year in the US, and a 30-minute code costs about $2.66 of AssemblyAI.

Try it: press "Start here" for the 80-second guided tour, or start a live code and read the six lines on screen.

## Categories and technologies

Categories: Healthcare, Voice Assistant. Technologies: AssemblyAI if the catalogue has it, plus Python, React, FastAPI, Docker and Render where listed.

## Tags

AssemblyAI · Voice Agent · Speech Recognition · Healthcare · Patient Safety · Real-time · FastAPI · React

## Links (fill in before submitting)

- Live demo: https://codeloop-1il8.onrender.com (access code: give it in the submission's judge notes)
- GitHub: https://github.com/TusharTechs/codeloop (make public before submitting)
- Video: (upload URL)
- Slides: `docs/CodeLoop-deck.pdf`

## Before you press submit

- [ ] Repository is public
- [ ] Live demo URL opens for someone outside your network (test on phone data)
- [ ] Demo has an access code, or a sensible `MAX_CONCURRENT_CODES` and credit limit
- [ ] Video ≤ 5 min, MP4 < 300 MB
- [ ] PDF deck and 16:9 cover image uploaded
- [ ] Submit by 18:00 IST on 30 Sep (deadline 20:30 IST)
