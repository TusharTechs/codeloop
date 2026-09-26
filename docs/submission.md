# lablab.ai submission text

## Title (≤ 50 characters)

CodeLoop: the voice recorder for cardiac arrests

## Short description (≤ 255 characters)

A voice agent for resuscitation teams. It hears the whole room, logs every drug, shock and rhythm with the exact words, runs the ACLS clock and speaks up when an order was never confirmed back. Built on AssemblyAI.

## Long description

During an in-hospital cardiac arrest the whole team works by voice. Hands are on the chest,
the airway and the syringes while orders fly across the room. In filmed resuscitations only 26%
of spoken orders were repeated back, and those were completed 3.6 times sooner. Hospital records
agree with trained observers on epinephrine timing at only κ 0.27. Someone must stop caring for
the patient to write things down, and no tool notices an order that nobody confirmed.

CodeLoop is the recorder that never looks away. A tablet on the crash cart streams the room to
AssemblyAI Universal-3.5 Pro, with speaker labels, Medical Mode, ACLS keyterms and Hindi–English
code-switching. A deterministic grammar turns speech into events, and each event quotes the exact
words it came from. Every order becomes a loop: ordered, read back, given. If nobody confirms an
order, the card turns amber and CodeLoop says so. If a different dose is read back, the card turns
red and CodeLoop says "Check dose. Ordered amiodarone three hundred milligrams, read back one hundred
fifty milligrams." It keeps the ACLS clock (two-minute cycles, the epinephrine window, shocks, a
shockable-rhythm check) and answers "CodeLoop, last epi?" from its own record. Its voice runs on
the AssemblyAI Voice Agent API: it waits for a gap in the room and stops the instant a clinician
talks over it.

Safety is the design. Models help understand speech, but deterministic code decides every state,
timer and spoken number. Low-confidence doses are marked for confirmation, and a misheard "ROSC"
cannot end a code. Every entry goes into a SHA-256 hash-chained audit log, and the Code Record is
rebuilt from that log.

After the code, CodeLoop closes the learning loop. The Code Record shows quality against AHA
targets (time to first shock and epinephrine, read-back rate and time, estimated CPR fraction). A
"second listen" transcribes the whole recording again with AssemblyAI async Universal-3.5 Pro and
confirms each live event or flags it for review. Then the team leader can hold a hands-free spoken
debrief: a Voice Agent conversation with tool calls that quotes facts from the record, never
computing them, and saves the team's lessons in their own words.

We measured it honestly on synthetic mock codes. On two held-out sets, committed before they
were measured, the first live scores were precision 0.97 / recall 0.71 and 0.82 / 0.56. After
general fixes: 0.96 / 0.88, with 16 of 17 loop outcomes correct. Medical Mode plus keyterms raised
critical-entity accuracy from 78% to 96%. Event latency is about 1.2 s.
An AssemblyAI bill of about $2.66 covers a 30-minute code. First market: simulation centres and
mock-code debriefs. Over 290,000 adult in-hospital cardiac arrests happen each year in the US across
6,100 hospitals; at an assumed $500 per hospital per month that is about $37M a year in the US alone.

Try it: open the live demo, enter the access code and press "Start here · 80-second guided tour". With
a microphone, "Start live code" shows six lines to say and ticks each one off as CodeLoop reacts.

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
