# AssemblyAI capabilities for a voice agent hackathon (verified 2026-09-25)

Scope: what AssemblyAI ships **as of late September 2026**, checked against the official docs (the raw `.md` versions of the docs pages, pulled via `https://www.assemblyai.com/docs/<path>.md`), the blog, the pricing page, and the `github.com/AssemblyAI` org. The hackathon is the **AssemblyAI Voice Agent Hackathon on lablab.ai, Sep 1–30 2026, with a $10k pool ($5k cash plus $5k AAI credits)**. The only stated rule is "Every participant builds on AssemblyAI". I could not see a public judging rubric (the lablab page loads it dynamically), so treat everything about judging below as inference.

Legend: **[V]** means verified in official docs or a first-party repo on the date above. **[U]** means unverified, inferred, or the sources conflict (explained inline).

---

## 0. TL;DR: product map (Sept 2026)

| Product | What it is | Endpoint | Price (list) |
|---|---|---|---|
| **Voice Agent API** (launched 2026-04-29) | A hosted speech-to-speech agent: STT, LLM and TTS on one WebSocket, with tools, turn-taking and telephony | `wss://agents.assemblyai.com/v1/ws` plus REST at `https://agents.assemblyai.com/v1/...` | **$4.50/hr ($0.075/min)**, all-inclusive [V] |
| **Universal-3.5 Pro Streaming ("Realtime")** (launched 2026-06-23) | Flagship realtime STT. Promptable, 18 or 19 languages with mid-sentence code-switching, and turn detection that reads the transcript | `wss://streaming.assemblyai.com/v3/ws?speech_model=universal-3-5-pro` | **$0.45/hr** [V] |
| Universal-Streaming English / Multilingual | Older, cheaper streaming models. Confidence-based end-of-turn | same WS, `speech_model=universal-streaming-english` or `universal-streaming-multilingual` | $0.15/hr [V] |
| Universal-3.5 Pro (async) | Pre-recorded STT | `POST https://api.assemblyai.com/v2/transcript` with `speech_models:["universal-3-5-pro"]` | $0.21/hr [V] |
| Universal-2 (async) | 99 languages, cheap | same, `speech_models:["universal-2"]` | $0.15/hr [V] |
| **LLM Gateway** (replaced LeMUR, which was shut off 2026-03-31) | OpenAI-compatible chat completions across Claude, GPT, Gemini, Qwen and others. Supports tools and structured outputs | `https://llm-gateway.assemblyai.com/v1/chat/completions` (EU: `llm-gateway.eu.assemblyai.com`) | per token [V] |
| Sync STT / Dictation API (new) | One HTTP call for short clips. Dictation returns cleaned text plus verbatim, up to 120 s | `dictation.assemblyai.com` | [U: price not checked] |

Sources: [Voice Agent API docs](https://www.assemblyai.com/docs/voice-agents/voice-agent-api), [Introducing Voice Agent API blog](https://www.assemblyai.com/blog/introducing-our-voice-agent-api), [U3.5 Pro Realtime blog](https://www.assemblyai.com/blog/universal-3-5-pro-realtime), [Pricing](https://www.assemblyai.com/pricing), [Streaming model selection](https://www.assemblyai.com/docs/streaming/select-the-speech-model), [LeMUR→LLM Gateway migration](https://www.assemblyai.com/docs/llm-gateway/migration-from-lemur).

---

## 1. Voice Agent API

### 1.1 Basics [V]
- **Name:** "Voice Agent API". Product page: https://www.assemblyai.com/products/voice-agent-api
- **WebSocket:** `wss://agents.assemblyai.com/v1/ws`
  - Server-side auth: `Authorization: Bearer <API_KEY>` header on the upgrade. The docs examples use `additional_headers={"Authorization": f"Bearer {API_KEY}"}`.
  - Browser auth: `wss://agents.assemblyai.com/v1/ws?token=<temp_token>`.
- **Temp token:** `GET https://agents.assemblyai.com/v1/token?expires_in_seconds=60&max_session_duration_seconds=...` with your API key in `Authorization`, which returns `{ "token": "..." }`.
  - `expires_in_seconds` is 1–600. It is the redemption window.
  - `max_session_duration_seconds` is 60–10800. The default is 10800 (a 3-hour cap).
  - Tokens are **single-use**, so fetch a fresh one for every connect and every resume.
  - The official starter calls `/token?product=voice_agent&expires_in_seconds=60`. The `product` param isn't in the docs page; it comes from the repo. [V: repo]
- **REST base:** `https://agents.assemblyai.com/v1`. The starter's `lib.py` also mentions regional hosts, and the SIP guide uses `https://agents.us.assemblyai.com/v1`.
- **No proprietary SDK is required.** It's plain JSON over a WebSocket. Neither the Python SDK (`assemblyai` 1.6.1) nor the JS SDK (`assemblyai` 4.41.5) has a voice-agent module; they cover streaming, async, LLM gateway, sync and dictation. [V: checked SDK source trees]
- **Architecture:** a cascade (STT, then LLM, then TTS), not an end-to-end speech model. The blog says "Swap the LLM and adjust prompts (cascading orchestration, not end-to-end speech model)". STT is Universal-3.5 Pro Streaming. At launch it was Universal-3 Pro Streaming; the docs now say 3.5.
- **Latency:** "~1 second end-to-end latency" from end of the user's turn to agent audio, and end-of-turn detection around 300 ms ([blog comparison](https://www.assemblyai.com/blog/voice-agent-api-vs-universal-3-pro-streaming)). Session timelines report `time_to_first_audio_ms`; example values in the docs are 1013 and 1457 ms.

### 1.2 Two ways to configure
1. **Stored agent (recommended)** [V]
   - `POST https://agents.assemblyai.com/v1/agents` creates an agent and returns an `id`.
   - `PUT /v1/agents/{id}`, `GET /v1/agents`, `GET /v1/agents/{id}` and `DELETE /v1/agents/{id}` manage it.
   - The client then sends only `{"type":"session.update","session":{"agent_id":"..."}}` as the **first** message. `agent_id` can't be mixed with inline fields; doing so raises `agent_id_not_first`.
   - HTTP tools, custom `llm`, DTMF and `pre_connect_requests` live **only on stored agents**.
2. **Inline config** via `session.update` right after connect, before `session.ready`.

Minimal stored agent ([create-agent](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/create-agent)):
```json
{ "name": "Support Assistant",
  "system_prompt": "You are a friendly support agent. Keep responses under two sentences.",
  "greeting": "Hi, how can I help?",
  "voice": { "voice_id": "alba" } }
```
Stored agents take `voice: {voice_id}`. Inline sessions use `session.output.voice: "alba"`.

### 1.3 Full inline session config [V]
([session-configuration](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/session-configuration), [events-reference](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/events-reference))
```json
{ "type": "session.update",
  "session": {
    "system_prompt": "…",                       // mutable mid-session
    "greeting": "…",                            // IMMUTABLE after first update
    "tools": [ … ],                             // mutable (progressive reveal)
    "input": {
      "format": { "encoding": "audio/pcm" },    // audio/pcm (24 kHz PCM16) | audio/pcmu | audio/pcma (8 kHz)
      "keyterms": ["Sunrise Pharmacy", "hydrochlorothiazide"],  // ≤100, mutable
      "transcription_mode": "balanced",         // min_latency | balanced | max_accuracy, mutable
      "transcription_prompt": "…",              // ≤1750 chars, STT context (NOT behavior), mutable
      "language_codes": ["en","hi"],            // omit = auto; applied on next STT reconnect
      "voice_focus": "near-field",              // near-field (default) | far-field; set at connect
      "voice_focus_threshold": 0.85,            // 0–1, default 0.85
      "turn_detection": {
        "vad_threshold": 0.5,                   // default 0.5
        "min_silence": 1000,                    // ms; unset = adaptive
        "max_silence": 3000,                    // ms; unset = adaptive
        "interrupt_response": true,             // barge-in on/off
        "interruption_delay": 0                 // 0–1000 ms; default per mode
      }
    },
    "output": {
      "voice": "alba",                          // IMMUTABLE
      "format": { "encoding": "audio/pcm" },    // IMMUTABLE
      "volume": 100                             // 0–100, mutable
    }
  } }
```
- **Mutable mid-session:** `system_prompt`, `tools`, `input.turn_detection`, `input.keyterms`, `input.transcription_mode`, `input.transcription_prompt`, `output.volume`.
- **Immutable:** `greeting`, `output.voice`, `output.format`. Changing them raises `immutable_field`.
- **Delayed:** `language_codes` and `voice_focus*` take effect on the next STT reconnect.
- The server answers every update with `session.updated` carrying the full resolved `config`.

### 1.4 Client → server events [V]
| type | fields | notes |
|---|---|---|
| `input.audio` | `audio`: base64 | Mono PCM16 at 24 kHz by default. Send at real-time pace, ~50 ms chunks, and only after `session.ready`. Sending faster than real time triggers `audio_rate_violation`. Binary frames and WAV headers are rejected (`invalid_audio`). |
| `session.update` | `session:{…}` | See 1.3 |
| `session.resume` | `session_id` | Must be the first message on reconnect. The grace window is **30 s** and it is billable. |
| `session.end` | none | Clean end: stops billing immediately. The server emits `session.ended`. |
| `tool.result` | `call_id`, `result` (**JSON string**), `is_error?` | Send it when `reply.done` is the latest event you've received. |
| `reply.create` | `instructions?` | Makes the agent speak now, e.g. a status update during a hold. |
| `conversation.message` | `role`: `user` or `system`, `content` | Injects context without triggering a reply |

### 1.5 Server → client events [V]
| type | key fields |
|---|---|
| `session.ready` | `session_id`, `config`, `expires_at` (epoch s), `resume_token` |
| `session.updated` | `config` |
| `session.ended` | `session_duration_seconds`, `audio_duration_seconds`, `timestamp` |
| `input.speech.started` / `input.speech.stopped` | none. Flush playback on `started` for the snappiest barge-in. |
| `transcript.user.delta` | `item_id`, `text`. The **full text so far**, so replace rather than append. |
| `transcript.user` | `item_id`, `text` (final) |
| `reply.started` | `reply_id` (`fc-<call_id>` for tool replies), `item_id` |
| `reply.audio` | `data`: base64 PCM16 |
| `transcript.agent.delta` | `reply_id`, `item_id`, `delta` (next word), `start_ms`, `end_ms`. Aligned to the audio, so it's good for captions. |
| `transcript.agent` | `text` (trimmed to what the user actually heard if interrupted), `interrupted` |
| `reply.done` | `reply_id`, `status`: `completed` or `interrupted` |
| `tool.call` | `call_id`, `name`, `arguments` (**already a dict**) |
| `session.error` | `code`, `message`, `timestamp`, `param?` |

**The user transcript events carry no word-level confidence or timestamps** on the Voice Agent WebSocket. Per-turn `user_confidence` shows up only after the call, in the session timeline (see 1.10). If you need live word confidence, use Universal-3.5 Pro Streaming directly (section 2). [V]

**Error codes** [V]:
- **Handshake:** `UNAUTHORIZED` or `FORBIDDEN` (close 1008), `INTERNAL_ERROR` (1011).
- **Resume:** `session_not_found`, `session_forbidden`, `session_expired`.
- **Startup:** `agent_init_failed`, `agent_timeout` (10 s).
- **Client messages:** `invalid_format`, `invalid_audio`, `invalid_value`, `immutable_field`, `invalid_config`, `agent_id_not_first`, `agent_not_found`, `audio_rate_violation`.
- **Retryable:** `at_capacity`, `concurrency_exceeded`, `internal_error`.
- **Live:** `session_expired` when the TTL is hit. There is **no warning event** before it, so run your own timer.
- In browsers, pre-handshake failures surface only as close code **1006**.

### 1.6 Canonical message sequence (with a tool) [V]
```
C→ session.update {system_prompt, tools, output.voice}
S→ session.ready {session_id}
C→ input.audio …
S→ input.speech.started → transcript.user.delta* → input.speech.stopped → transcript.user
S→ reply.started → reply.audio ("let me check") → tool.call {call_id, name, arguments} → reply.done
C→ tool.result {call_id, result:"{\"temp_c\":22}"}
S→ reply.started → reply.audio → transcript.agent.delta* → transcript.agent → reply.done
C→ session.end ;  S→ session.ended ; socket closes
```

### 1.7 Tools [V]
([tools overview](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/tools/overview), [client-side](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/tools/client-side-tools), [HTTP](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/tools/http-tools))

**Function (client-side) tool**, declared inline in `session.tools`:
```json
{ "type": "function", "name": "lookup_part",
  "description": "Call when the caller names a part number. Do not call for general questions.",
  "parameters": { "type": "object",
    "properties": { "part_number": { "type": "string",
        "description": "Part number as spoken, e.g. AB-12345",
        "pattern": "[A-Z]{2}-\\d{5}", "examples": ["AB-12345","XK-00917"] } },
    "required": ["part_number"] },
  "execution_mode": "interactive",   // or "hold"
  "timeout_seconds": 120 }           // 1–300, default 120
```
- **Returning results:** gather results as `tool.call` events arrive, then send them all from the `reply.done` handler. On `reply.done` with `status:"interrupted"`, throw away pending results.
- `result` is a **JSON string**. One page of the docs (the tools overview hold example) shows `tool_call_id` and an object `result`. The events reference and starter code use `call_id` plus a string, so go with `call_id` plus a string. [conflict noted]
- **Async and long-running tools:** supported through `execution_mode:"hold"`.
  - The agent stays silent, and user speech is kept in context but gets no reply.
  - `tool.result` automatically fires the next reply, so don't also send `reply.create`.
  - To speak during a hold, send `reply.create` with `instructions`.
  - Use hold for work over 10 s, transfers, payments, or identity checks.
  - Use `interactive` (the default) for calls under ~5 s. The agent says a transition phrase such as "let me check that".
- **Parameter validation is itself a turn-detection signal.**
  - `enum`, `examples`, `pattern` (Python `re`, full match) and `format` (`email`, `date`, `date-time`) are enforced. When a spoken value doesn't fit, the agent re-asks for **just that value**.
  - The agent also **waits for a complete value** before ending the user's turn, for example all ten digits of a phone number.
  - For digit strings, write patterns that tolerate spaces (`" *([0-9] *){13,19}"`) and strip non-digits in your handler.
- **HTTP (server-side) tools**, stored agents only:
  - Add `"http": {"url","http_method":"GET|POST|PUT|PATCH|DELETE","headers":[{"name","value"}]}`.
  - GET and DELETE turn the arguments into a query string; POST, PUT and PATCH send them as a JSON body.
  - Responses are capped at 8 KiB. Only HTTPS and public hosts work, and redirects aren't followed.
  - Header values are write-only and encrypted.
  - The browser still receives `tool.call` for visibility but doesn't answer it.
- **DTMF-collected arguments** (telephony):
  - Configure with `dtmf_collected_arguments:[{parameter_name,min_digits,max_digits,sensitive,terminator:"#",confirm,prompt}]`.
  - With `sensitive:true`, the digits stay out of the transcript, logs and LLM. PCI flows are the showcase. (Source: `agents/dtmf.jsonc` in the [starter repo](https://github.com/AssemblyAI/voice-agent-starter-python).)
- **Guidance:** keep to 10 or fewer tools per phase. Use **progressive tool reveal** (`session.update` with new `tools` plus `system_prompt` after each step succeeds) so the model can't skip prerequisites.
- **Parallel tool calls:** not documented. [U]

### 1.8 LLM: bundled by default, bring-your-own optional [V]
([connect-your-own-llm](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/connect-your-own-llm))
- **Default:** "AssemblyAI's **managed** conversational model". Which model it is isn't disclosed. [U]
- **BYO:** set `"llm":[{"base_url","model","api_key"}]` on a stored agent.
  - The endpoint must be OpenAI-compatible and serve **streamed** `POST {base_url}/chat/completions` over public HTTPS.
  - Only one entry is allowed (no fallbacks yet).
  - `"llm": []` switches back to the managed model.
- **Via LLM Gateway:** `base_url: https://llm-gateway.assemblyai.com/v1`, with `model` set to a Gateway ID and your AssemblyAI key as `api_key`. The starter uses `claude-sonnet-4-6`.
- **Billing when BYO or Gateway:** the docs say the Gateway is "billed on your AssemblyAI account". Whether the $4.50/hr changes isn't stated. [U]
- **Structured outputs:** the Voice Agent API has no `response_format`. Get structure by (a) tool-parameter JSON Schema, which is validated, or (b) a post-call LLM Gateway call with `response_format: {type:"json_schema", json_schema:{name, schema, strict:true}}`. Supported for GPT-4.1+/5.x, Gemini, Claude 4.5+, Qwen and Kimi, but not gpt-oss ([structured outputs](https://www.assemblyai.com/docs/llm-gateway/structured-outputs)). [V]

### 1.9 Turn detection and barge-in [V]
([turn-detection-and-interruptions](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/turn-detection-and-interruptions))
- **On by default:**
  - **Semantic end-of-turn**: it judges from meaning, not silence.
  - **Smart waiting for tool values**: it waits for phone numbers, emails and dates.
  - **Adaptive pacing**: it learns each speaker's pace over the call.
  - **Semantic barge-in**: "uh-huh" doesn't interrupt; "wait, stop" does.
- AssemblyAI's own tuning advice: "The way to make turn-taking better is **good tool descriptions**, not VAD knobs."
- **Switch `transcription_mode` by call stage:** use `max_accuracy` while capturing an order ID or spelled name, then go back to `min_latency` or `balanced`.
- On interruption, the server sends `reply.done{status:"interrupted"}` and `transcript.agent{interrupted:true}`. The client must flush queued audio.

### 1.10 Sessions, recordings, webhooks, telephony [V]
- **Session history:** `GET /v1/sessions?limit=&cursor=&agent_id=&status=`, `GET /v1/sessions/{id}`, `DELETE /v1/sessions/{id}`.
  - Artifacts come as presigned URLs with a short TTL: a **stereo OGG/Opus recording** (user on the left, agent on the right), a **timeline JSON** and metadata.
  - Timeline turns carry `user_transcript`, **`user_confidence`**, `agent_text`, `status`, `trigger`, `time_to_first_audio_ms`, and `tool_calls[]` with `arguments`, `result`, `duration_ms` and `is_error`. This is ready-made **audit and eval data**. ([session-history](https://www.assemblyai.com/docs/voice-agents/voice-agent-api/session-history))
- **Webhooks:** `session.started`, `session.completed`, `call.connected`, `call.ended` (with `recording_url` and `transcript_url`) and `call.failed`.
  - Each delivery has an HMAC-SHA256 `X-AAI-Signature: t=…,v1=…` computed over `"{t}." + raw_body`, with 300 s tolerance.
- **Twilio SIP (no media server):** create a Twilio SIP trunk with origination to `sip:sip.assemblyai.com`, then `POST /phone-numbers/import` and `PUT /phone-numbers/{number}/agent`. The starter's `deployment/telephony/connect.py` automates this.
- **Pre-connect requests** (telephony only):
  - Before answering, the platform calls your HTTPS endpoint (at most 2 entries, 800 ms max each) with `caller_number`.
  - It maps the returned JSON paths into `{{placeholders}}` in the greeting and into the model context. `{"reject":true}` declines the call.
  - Failures fall through: the call is answered as if the lookup never ran.
- **Media-streams alternative:** [voice-agent-api-twilio-example](https://github.com/AssemblyAI/voice-agent-api-twilio-example) relays `audio/pcmu` between Twilio and the agent with no transcoding. **Caveat:** its README references `wss://agents.assemblyai.com/v1/realtime` and voices `ivy`, `claire` and `dawn`, which don't appear in current docs. It looks stale. [U]
- **Bluejay simulation testing:** there's a docs page plus the `bluejay-aai-bridge` repo for automated voice tests.

### 1.11 Voices and languages [V]
- **16 voices in the current docs.**
  - English, US accent: `alba`, `eve`, `george`, `jane`, `jean`, `mary`, `michael`.
  - English, UK accent: `anna`, `charles`, `paul`, `vera`.
  - Native-accent voices, which code-switch with English: `giovanni` (it), `lola` (es), `juergen` (de), `rafael` (pt), `estelle` (fr).
  - The launch-era marketing and blog say "30+" or "34 voices". That doesn't match the current voices page. [conflict; trust docs]
- No cloned or custom voices are documented, and the TTS model isn't named. [U]
- **Input languages:** 18, with native code-switching: en, es, de, fr, pt, it, tr, nl, sv, no, da, fi, **hi**, vi, ar, he, ja, zh.
- **Output languages:** 6 (en, it, es, de, pt, fr). **Hindi output is "coming soon"**, so a Hindi speaker can be *understood*, but the agent answers in an English or other supported voice.

### 1.12 Pricing and limits
- $4.50/hr, billed on **session wall-clock time** including idle time and the 30 s resume grace window. [V]
- The maximum session is 3 hours. [V]
- Concurrency: "Unlimited" according to the blog. The streaming side limits **new** sessions per minute (free: 5/min, PAYG: 100/min, with auto-scale +10% when usage is at least 70%). There is a `concurrency_exceeded` error code. [V/U: the voice-agent-specific rate limit isn't separately documented]
- Free credits: **$50 at signup, no card**. [V]
- "PCI-certified end-to-end" per the product page. [V]

### 1.13 Minimal Python client (composed from the documented events) [V: events; code is mine]
```python
import asyncio, base64, json, os, websockets
URL = "wss://agents.assemblyai.com/v1/ws"
async def main(mic_chunks):   # async iterator of 24kHz PCM16 mono bytes (~50ms each)
    async with websockets.connect(URL, additional_headers={"Authorization": f"Bearer {os.environ['ASSEMBLYAI_API_KEY']}"}) as ws:
        await ws.send(json.dumps({"type": "session.update", "session": {
            "system_prompt": "You are a parts-desk agent. One or two short sentences.",
            "greeting": "Parts desk, what part number are you after?",
            "output": {"voice": "michael"},
            "input": {"keyterms": ["XK-00917", "Bosch", "torque converter"],
                      "transcription_prompt": "Auto-parts ordering call with part numbers and brand names."},
            "tools": [LOOKUP_PART_TOOL]}}))
        pending, ready = [], asyncio.Event()
        async def pump():
            await ready.wait()
            async for chunk in mic_chunks:
                await ws.send(json.dumps({"type": "input.audio", "audio": base64.b64encode(chunk).decode()}))
        asyncio.create_task(pump())
        async for raw in ws:
            ev = json.loads(raw); t = ev["type"]
            if t == "session.ready": ready.set()
            elif t == "reply.audio": play(base64.b64decode(ev["data"]))
            elif t == "input.speech.started": flush_playback()
            elif t == "tool.call": pending.append((ev["call_id"], await run_tool(ev["name"], ev["arguments"])))
            elif t == "reply.done":
                if ev["status"] == "interrupted": flush_playback(); pending.clear()
                for cid, res in pending:
                    await ws.send(json.dumps({"type": "tool.result", "call_id": cid, "result": json.dumps(res)}))
                pending.clear()
            elif t == "session.error": print(ev["code"], ev["message"])
```
**Browser audio:** the docs and starter use two AudioWorklets.
- Capture: Float32 is resampled to 24 kHz Int16, base64-encoded, and sent as `input.audio`.
- Playback: a ring buffer that is emptied when `input.speech.started` or an interrupted `reply.done` arrives.
- Use `getUserMedia({audio:{echoCancellation:true,noiseSuppression:false,autoGainControl:false}})`. Terminal apps have no echo cancellation and the agent will interrupt itself, so use headphones there.
- Code: [starter app.js](https://github.com/AssemblyAI/voice-agent-starter-python/blob/main/deployment/browser/app.js).

---

## 2. Universal-3.5 Pro Streaming (realtime STT)

### 2.1 Models [V]
| `speech_model` | Languages | Turn detection | Notes |
|---|---|---|---|
| `universal-3-5-pro` (**default**) | 18 in the voice-agent docs; the multilingual page lists **19 (adds Catalan `ca`)**: en es fr de it pt tr nl sv no da fi hi vi ar he ja zh (+ca) | Reads the transcript after silence: it checks for terminal punctuation after `min_turn_silence` and forces the end at `max_turn_silence` | Promptable (`prompt`), `agent_context`, conversation memory, `mode`, Voice Focus. Partials are segment-level re-transcriptions. |
| `universal-streaming-english` | en | Confidence-based: `end_of_turn_confidence_threshold` | Word-by-word partials. P50 emission 317 ms. |
| `universal-streaming-multilingual` | en es de fr pt it | Confidence-based | Per-turn language switching |

The older Universal-3 Pro Realtime remains available as a pinned snapshot (per the blog).

### 2.2 Connection [V]
([API spec](https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket))
- **Endpoints:** `wss://streaming.assemblyai.com/v3/ws`, which is latency-routed. For data residency use `streaming.us.assemblyai.com` or `streaming.eu.assemblyai.com`.
- **Auth:** header `Authorization: <API_KEY>` (**no** "Bearer"), or `?token=` from `GET https://streaming.assemblyai.com/v3/token?expires_in_seconds=60[&max_session_duration_seconds=]`.
  - SDK: `RealTimeTranscriber(...).create_temporary_token(expires_in_seconds=60)` in Python, `client.streaming.createTemporaryToken()` in JS. Tokens are single-use.
- **Audio:** binary frames of 50–1000 ms each. Anything outside that range closes with 3007.
  - `encoding`: `pcm_s16le` (default), `pcm_mulaw`, `opus`, `ogg_opus` or `aac`.
  - `sample_rate`: 8000–96000. Use 16 kHz; higher doesn't help.

**Query params (all verified from the spec):**
- **Model and speed:** `speech_model`, `mode` (`min_latency` | `balanced` | `max_accuracy`).
- **Language:** `language_codes` (JSON list), `language_detection`.
- **Turn-taking:** `min_turn_silence`, `max_turn_silence`, `end_of_turn_confidence_threshold` (Universal-Streaming only; default 0.4), `vad_threshold`, `interruption_delay` (0–1000; U3.5 only).
- **Partials and formatting:** `continuous_partials` (default true, roughly every 3 s), `include_partial_turns`, `format_turns` (Universal-Streaming only).
- **Accuracy:** `domain=medical-v1`, `prompt` (≤1750 chars; U3.5), `keyterms_prompt` (JSON list, ≤100 terms, each ≤50 chars), `agent_context` (≤1750; U3.5), `previous_context_n_turns` (0–100, default 5).
- **Diarization:** `speaker_labels`, `max_speakers` (1–10), `speaker_labels_revision_interval_ms`.
- **Noise:** `voice_focus` (`near-field` or `far-field`), `voice_focus_threshold` (default 0.7).
- **Guardrails:** `redact_pii`, `redact_pii_policies`, `redact_pii_sub` (`hash` or `entity_name`), `filter_profanity`.
- **Session:** `session_heartbeat`, `llm_gateway` (JSON), `inactivity_timeout` (5–3600 s).

### 2.3 Messages [V]
**Client → server**
- Binary audio.
- `{"type":"UpdateConfiguration", …}`. Fields that can change mid-stream: `prompt`, `keyterms_prompt`, `agent_context`, `min_turn_silence`, `max_turn_silence`, `vad_threshold`, `interruption_delay`, `mode`, `end_of_turn_confidence_threshold`, `language_codes`, `continuous_partials`, `session_heartbeat`.
- `{"type":"ForceEndpoint"}` finalizes the current turn immediately, for your own VAD or push-to-talk.
- `{"type":"KeepAlive"}`.
- `{"type":"Terminate"}`.

**Server → client**
```json
{"type":"Begin","id":"uuid","expires_at":1760000000,"configuration":{"model":"universal-3-5-pro","mode":"balanced",…}}
{"type":"SpeechStarted","timestamp":1216,"confidence":0.98}      // U3.5 only; emitted only once a real transcript exists → reliable barge-in
{"type":"Turn","turn_order":0,"end_of_turn":false,"turn_is_formatted":false,
 "transcript":"My name is","end_of_turn_confidence":0,"utterance":"",
 "words":[{"start":1216,"end":1627,"text":"My","confidence":0.956,"word_is_final":false}, …]}
{"type":"Turn","turn_order":0,"end_of_turn":true,"turn_is_formatted":true,
 "transcript":"My name is Sonny.","utterance":"My name is Sonny.","end_of_turn_confidence":1,
 "language_code":"en","language_confidence":0.97,           // with language_detection=true
 "speaker_label":"A","speaker_confidence":0.9,               // with speaker_labels=true
 "words":[…,{"start":3016,"end":4155,"text":"Sonny.","confidence":0.316,"word_is_final":true}]}
{"type":"SpeakerRevision","revisions":[{"turn_order":3,"speaker_label":"B","words":[…]}]}
{"type":"LLMGatewayResponse","data":{"choices":[{"message":{"content":"…"}}]}}   // with llm_gateway param
{"type":"Heartbeat","total_audio_received_ms":…,"realtime_factor":…,"max_speech_probability":…}
{"type":"Termination","audio_duration_seconds":…,"session_duration_seconds":…}
```
- **Partials versus immutability:**
  - On U3.5 Pro, **each `Turn` re-transcribes the whole turn**, so replace rather than append. The final (`end_of_turn:true`) is formatted and the most accurate.
  - On Universal-Streaming, `word_is_final` words are immutable, and with `format_turns=true` you get two finals (unformatted, then formatted).
  - The docs call U3.5 finals "immutable transcripts [that] arrive fully formatted".
- **Word-level confidence and ms timestamps are present on every word.** The docs' own example shows a proper noun at **0.316 confidence** ("Sonny"). That's exactly the signal for "please spell that" confirmation logic.
- **Errors** ([common errors](https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures)):
  - 3005: server error.
  - 3006: invalid message, or inactivity.
  - 3007: chunk size or rate violation.
  - 3008: the 3-hour maximum was hit.
  - 3009: too many new sessions.
  - 1008: auth.
  - 410: the v2 endpoint was retired.

### 2.4 Turn detection details [V]
([turn detection](https://www.assemblyai.com/docs/streaming/turn-detection), [optimizing](https://www.assemblyai.com/docs/streaming/getting-started/optimizing-accuracy-and-latency))

**U3.5 Pro mode presets**
| mode | `min_turn_silence` | `max_turn_silence` | `interruption_delay` |
|---|---|---|---|
| min_latency | 128 | 640 | 0 |
| balanced (default) | 128 | 1280 | 500 |
| max_accuracy | 512 | 2560 | 500 |

- With `speaker_labels` on, the defaults change to 640/768 and continuous partials turn off.
- `vad_threshold`: one doc says the default is 0.2, the best-practices page says 0.3. Keep it matched to your local Silero VAD. [conflict]
- **Entity capture:**
  - Send `{"type":"UpdateConfiguration","min_turn_silence":1000}` right after the agent asks for a phone or card number.
  - Afterwards send `{"type":"UpdateConfiguration","mode":"balanced"}` to restore the defaults.
- **Latency tip:** `interruption_delay=0` gives a first partial at roughly 300 ms; the default 500 gives roughly 800 ms.
- **Universal-Streaming (legacy):**
  - The turn ends when `end_of_turn_confidence ≥ end_of_turn_confidence_threshold` (default 0.4) **and** `min_turn_silence` has passed (default 400 ms).
  - The acoustic fallback is `max_turn_silence` (1280 ms). `vad_threshold` defaults to 0.4.
  - Presets: aggressive 0.4/160/400, balanced 0.4/400/1280, conservative 0.7/800/3600.
- **Backchannels:** raw streaming doesn't filter "mhm", "yeah" and similar. The docs give a filter that ignores turns under 2 words or made only of backchannels while the agent is speaking. The Voice Agent API does this semantically for you.

### 2.5 Keyterms, prompting and context: the accuracy levers [V]
([prompting-and-keyterms](https://www.assemblyai.com/docs/streaming/prompting-and-keyterms), [context carryover](https://www.assemblyai.com/docs/streaming/universal-3-5-pro/context-carryover))
- **`keyterms_prompt`:**
  - At most 100 terms, each at most 50 characters. Longer terms are ignored; more than 100 is an error.
  - Use exact spelling and casing, and avoid common words.
  - Aimed at proper names, brands, **drug names, part numbers, alphanumerics**.
  - Works on all three models. It's **free on U3.5 Pro Realtime and Multilingual**, +$0.05/hr on Streaming English.
  - Replace it mid-stream with `UpdateConfiguration`; `[]` clears it.
- **`prompt`:** plain-language context about the audio, not instructions. Measured on 20k voice-agent calls, relative to no prompt:

| | domain | scenario | detailed |
|---|---|---|---|
| WER | −5% | −10% | −21% |
| hallucinated words | −9% | −12% | −19% |
| name EER | −5% | −16% | **−49%** |
| medical-term EER | −2% | −24% | −43% |

  - Pricing shows "General Prompting +$0.05/hr (U3.5 Pro async/realtime beta)".
- **`agent_context`:** after each agent reply, send `{"type":"UpdateConfiguration","agent_context":"Sure, what date would you like?"}` so the STT knows what was just asked. Earlier user turns are carried automatically (`previous_context_n_turns`, default 5).
  - The blog claims −8.9% WER with context and −16.4% with a context prompt, and −30.7% on place-name errors.
  - The docs example turns "user at assemblyai dot com" into a correctly formatted email.
- **Medical Mode:** `domain=medical-v1`, +$0.15/hr, works with every realtime model.
- **Voice Focus:** noise and cross-talk suppression, +$0.10/hr, U3.5 Pro only.

### 2.6 Multilingual, code-switching, Hindi and Hinglish [V + U]
- **Code-switching:**
  - U3.5 Pro code-switches **mid-sentence** with no configuration.
  - `language_codes:["en","hi"]` biases the model toward those languages while keeping code-switching; a one-element list pins a single language.
  - `language_detection=true` adds `language_code` and `language_confidence` to each turn.
- **Hindi:** supported (`hi`).
  - The docs' English↔Hindi sample is written in **Devanagari for Hindi words and Latin for English words**: "मेरा रुकने का तो बहुत मन है, but I have an exam to give tomorrow."
  - Romanized Hinglish output isn't documented. If you need Latin script, transliterate it yourself through the LLM. [U]
  - Voice Agent **output** in Hindi isn't available yet.

### 2.7 Streaming diarization [V]
- Set `speaker_labels=true`. Optionally add `max_speakers` (1–10).
- Each turn gets a `speaker_label` (A, B, …, or `UNKNOWN`) plus per-word `speaker` and `speaker_confidence`. The docs say that confidence is not calibrated.
- `SpeakerRevision` messages correct earlier labels.
- Utterances under 1 s may be labeled `PENDING`. Accuracy improves over the session.
- Costs +$0.12/hr and works on all streaming models. For multichannel audio, open one session per channel.

### 2.8 Latency and accuracy numbers (AssemblyAI's own) [V]
([benchmarks](https://www.assemblyai.com/docs/streaming/benchmarks), [U3.5 blog](https://www.assemblyai.com/blog/universal-3-5-pro-realtime))
- **Time to complete turn** (end of speech to final transcript):
  - U3.5 Pro: P50 568 ms, P90 829 ms.
  - Universal-Streaming English: P50 649 ms, P90 990 ms.
- **Emission latency** (Universal-Streaming): English P50 317 ms; Multilingual P50 303 ms.
- **WER:**
  - English mean: U3.5 Pro 6.3% vs Universal-Streaming 8.6%.
  - Multilingual average: 8.49% vs 11.74%.
- **Blog comparison on Pipecat's open agent-conversation benchmark:** U3.5 Pro **6.99%** WER, vs Deepgram Flux 15.58%, ElevenLabs Scribe v2 9.76%, and Google Chirp3 9.04%.
- **Entity error rates:** names 16.92%, places 6.28%, phone numbers 3.55%.
- These are vendor numbers.

### 2.9 Other streaming features [V]
- **PII redaction in streaming:**
  - Set `redact_pii=true`, optionally with `redact_pii_policies` (e.g. `["person_name","phone_number","email_address","credit_card_number","us_social_security_number","date_of_birth"]`) and `redact_pii_sub` (`hash` → `####`, `entity_name` → `[PERSON_NAME]`).
  - It applies to **final turns only**. When enabled, `include_partial_turns` defaults to false so no unredacted text leaks.
  - Streaming audio can't be redacted.
  - Pricing lists "PII Text Redaction +$0.08/hr". Whether that applies to streaming is [U].
- **Profanity filter:** `filter_profanity=true`, +$0.01/hr.
- **`llm_gateway` param:** runs an LLM prompt on each turn, with `{{turn}}` replaced by the turn text, and returns an `LLMGatewayResponse` on the same socket. Useful for live classification, translation or extraction without a second connection.
- **Streaming webhooks** and **self-hosted streaming** also exist (docs pages present; not examined).

---

## 3. Async / pre-recorded features that still matter [V]
- **Endpoint:** `POST https://api.assemblyai.com/v2/transcript` with `{"audio_url": "...", "speech_models": ["universal-3-5-pro"], ...}`, then poll `GET /v2/transcript/{id}`. Upload files with `POST /v2/upload`.
- **Speaker diarization:** `speaker_labels: true` (+$0.02/hr standard). An experimental option costs +$0.065/hr.
- **Speaker Identification**, which maps diarized speakers to names or roles: `"speech_understanding":{"request":{"speaker_identification":{"speaker_type":"name"|"role","speakers":[…]}}}`. +$0.02/hr.
- **Speech Understanding add-ons:**
  - Entity Detection (`entity_detection:true`, +$0.08/hr; includes medical entity types)
  - Sentiment (+$0.02)
  - Key Phrases (+$0.01)
  - Topic Detection (+$0.15)
  - Translation (+$0.06)
  - Custom Formatting (+$0.03)
  - Summarization, Auto Chapters and Action Items now run on the LLM Gateway.
- **Guardrails:** PII text redaction (+$0.08), **PII audio redaction** (+$0.05, async only), content moderation (+$0.15), profanity filter, speech threshold.
- **Language detection:** automatic on U3.5 Pro (code-switching). Universal-2 covers 99 languages as a fallback.
- **LeMUR is gone:** deprecated 2026-03-31, replaced by the **LLM Gateway**.
  - Models seen in the list include `claude-sonnet-4-6`, `claude-sonnet-5`, `claude-opus-5`, `claude-haiku-4-5-20251001`, `gpt-5.5`, `gpt-5-mini`, `gemini-3.5-flash`, `qwen3-32B` and `qwen3.5-4b-32k-fast`, among others.
  - The Gateway supports tool calling (OpenAI-style `tools` and `tool_choice`, with `finish_reason` passed through from the provider), structured outputs, prompt caching, fallbacks, and EU residency.
- **Use in a voice agent:** after the call, pull the Voice Agent session recording, run async U3.5 Pro with diarization, entities and PII audio redaction, then have the LLM Gateway produce a JSON-schema summary or QA scorecard. This shows breadth across the platform.

---

## 4. Safety and reliability [V unless marked]
| Feature | Where |
|---|---|
| Word-level `confidence` (0–1) plus timestamps | Streaming `Turn.words[]`. Voice Agent gives only per-turn `user_confidence`, and only in the post-call timeline |
| `end_of_turn_confidence`, `language_confidence`, `speaker_confidence`, `SpeechStarted.confidence` | Streaming |
| PII redaction | Streaming (final turns, text only). Async (text and audio). |
| DTMF with `sensitive:true` | Voice Agent: keeps card numbers and PINs out of the transcript, logs and LLM. "PCI-certified end-to-end". |
| Profanity filter | Streaming and async |
| Content moderation | Async |
| Audit trail | Voice Agent session timeline (every tool call with args, result, duration, error), stereo recording, HMAC-signed webhooks |
| Tool argument validation (`pattern`/`enum`/`format`) with automatic re-ask | Voice Agent |
| `is_error` on `tool.result` | Voice Agent: lets the agent recover gracefully |
| Data residency | US and EU endpoints for streaming, Gateway and agents |
| Write-only secrets | Tool header values and LLM API keys are encrypted and never read back |
| Compliance certificates (SOC 2, HIPAA BAA) | Not checked in this pass [U] |

---

## 5. SDKs, integrations, templates [V]
- **Python** `pip install assemblyai` (v1.6.1). Streaming v3 lives in `assemblyai.streaming.v3`.
  - Classes: `RealTimeTranscriber` (the current name in the docs; `StreamingClient` is still exported), `RealTimeParameters`, `RealTimeEvents.Begin/Turn/Termination/Error`, and events `SpeechStartedEvent`, `SpeakerRevisionEvent` and `LLMGatewayResponseEvent`.
  - Helpers: `client.update_configuration(...)`, `client.force_endpoint()`, `client.stream(iter)`, `client.disconnect(terminate=True)`, `create_temporary_token(expires_in_seconds=60)`.
  - Extras: `EnergyVad` and `ChannelStreamer` / `attribute_turn` for dual-channel work. `aai.DictationTranscriber()` handles dictation.
- **JS/TS** `npm i assemblyai` (v4.41.5).
  - `client.streaming.transcriber({sampleRate:16000, speechModel:"universal-3-5-pro", keytermsPrompt:[…]})`, plus `transcriber.updateConfiguration({...})`, `transcriber.forceEndpoint()` and `client.streaming.createTemporaryToken({expires_in_seconds:60})`.
- **Voice Agent API:** no SDK; use raw WebSocket and REST.
- **Starter repos** (updated Aug 2026), zero-dependency Python or Node:
  - [voice-agent-starter-python](https://github.com/AssemblyAI/voice-agent-starter-python) and [voice-agent-starter-js](https://github.com/AssemblyAI/voice-agent-starter-js).
  - Each agent is a `.jsonc` file (`minimal`, `keyterms`, `turn-taking`, `byo-llm`, `http-tools`, `exa-search`, `airtable-crm`, `cal-booking`, `dtmf`).
  - `publish.py` creates or updates the agent. `deployment/browser/server.py` mints tokens and serves the page. `deployment/telephony/connect.py` wires up a Twilio SIP trunk. There's a Render deploy button.
- **Other repos:** `voice-agent-api-twilio-example` (Media Streams bridge; possibly stale, see 1.10), `bluejay-aai-bridge` (voice simulation testing), `assemblyai-skill` (a coding-assistant skill), `cli`, `streaming-self-hosting-stack`, and `blurt` (open-source macOS dictation).
- **LiveKit:**
  - Install `pip install "livekit-agents[assemblyai,silero,codecs]~=1.6"`.
  - `assemblyai.STT(model="universal-3-5-pro", min_turn_silence=100, max_turn_silence=1000, vad_threshold=0.3)` with `turn_handling=TurnHandlingOptions(turn_detection="stt", endpointing={"min_delay":0})`.
  - `agent_context` is forwarded automatically on 1.6.6+.
  - With LiveKit Inference, use the model string `"assemblyai/universal-3-5-pro"`.
  - ([doc](https://www.assemblyai.com/docs/voice-agents/livekit-universal-3-5-pro))
- **Pipecat (≥1.4.0):**
  - Install `pip install "pipecat-ai[assemblyai,...]"`.
  - `AssemblyAISTTService(api_key=…, settings=AssemblyAISTTService.Settings(model="universal-3-5-pro", min_turn_silence=128, max_turn_silence=640), vad_force_turn_endpoint=False)`. With `False`, AssemblyAI decides turns.
  - ([doc](https://www.assemblyai.com/docs/voice-agents/pipecat-universal-3-5-pro))
- **Telephony:** Twilio SIP (native), Twilio Media Streams (`audio/pcmu` passthrough), and streaming `encoding=pcm_mulaw` at 8 kHz.
- **Also available:** OpenRouter (Sync STT), Vapi (the blog shows a ~465 ms tuned pipeline), and "Build with AI coding tools" docs (`llms.txt`, a skill).

---

## 6. What's distinctive, and what to showcase

### 6.1 How AssemblyAI positions itself against competitors (inference from docs, blog and benchmarks; not neutral)
- **Versus OpenAI Realtime** (end-to-end speech-to-speech):
  - AssemblyAI is a **cascade with a best-in-class, promptable STT layer**. You get a **readable, auditable transcript** with per-turn confidence, tool-call logs and recordings, and you can **swap the LLM** (Claude or GPT through the Gateway, or your own endpoint).
  - OpenAI's Realtime has stronger expressive voices and native speech-to-speech prosody. [U: competitor claims not verified]
- **Versus Deepgram** (Nova-3 / Flux):
  - AssemblyAI claims much lower WER on agent conversations (6.99% vs Flux's 15.58% on Pipecat's benchmark).
  - It adds contextual `prompt`, `agent_context` conversation memory, mid-sentence code-switching across 18 or 19 languages, and turn detection that reads the transcript.
  - The docs ship a Deepgram→AssemblyAI migration guide.
- **Versus ElevenLabs Agents:** ElevenLabs is voice-first (TTS quality and cloning). AssemblyAI's pitch is **the ears**: accuracy on entities (names, emails, phone numbers, part numbers, drug names). They cite that "76% of respondents rated speech-to-text accuracy as the single most important non-negotiable".
  - AssemblyAI's TTS catalog is small: 16 voices, 6 output languages, no cloning. **Don't make voice quality the centerpiece.**
- **What AssemblyAI emphasizes itself:**
  1. entity accuracy with keyterms and prompting
  2. turn detection plus semantic barge-in
  3. `agent_context`
  4. code-switching
  5. tool-parameter-aware waiting
  6. an all-in $4.50/hr on one socket
  7. PCI and DTMF
  8. data you can audit

### 6.2 Five features a project should showcase (ranked)
1. **Entity accuracy you can measure: keyterms, `transcription_prompt` or `prompt`, and `agent_context`.**
   - Pick a domain full of hard entities: pharmacy drug names, auto or industrial part numbers like `XK-00917`, SKUs, surnames.
   - Load **per-caller or per-stage keyterms dynamically** with `session.update` or `UpdateConfiguration`, e.g. after a CRM lookup through `pre_connect_requests`.
   - Show a live **before/after A/B**: the same audio with and without keyterms and prompt, and the entity error rate side by side. This mirrors AssemblyAI's own `keyterms.jsonc` demo and their EER benchmarks.
2. **Confidence-aware confirmation loops.**
   - Use streaming word `confidence` (e.g. flag any entity word under 0.6; the docs' example "Sonny" is 0.316) to decide when to read a value back or ask the caller to spell it.
   - Switch `transcription_mode` to `max_accuracy` (Voice Agent) or raise `min_turn_silence` (streaming) during entity capture, then switch back. Visualize the confidence live.
   - Architecture choice: the Voice Agent API doesn't expose live word confidence. Either run a **parallel U3.5 Pro streaming session** for the confidence UI, or build on streaming, LiveKit or Pipecat. Alternatively, use timeline `user_confidence` after the call.
3. **Natural turn-taking as the visible "wow".**
   - Tool schemas with `pattern`, `examples` and `enum` make the agent **wait for the full phone or card number** and re-ask for only the bad field.
   - Semantic barge-in ignores "uh-huh" but stops on "wait". Show a split-screen event log of `input.speech.started`, `reply.done{interrupted}` and `transcript.agent{interrupted:true}`, with trimmed text.
   - Report `time_to_first_audio_ms` from the session timeline.
4. **Real tool use with the right `execution_mode`, plus progressive tool reveal.**
   - Interactive HTTP tools for lookups. A `hold` tool for a slow action (booking, payment or transfer) with `reply.create` status updates.
   - Tools unlocked in tiers so the agent **can't** commit before verifying.
   - Return `is_error` results that name the failing field.
   - Optionally add DTMF `sensitive:true` for a PCI-safe payment moment. That's a strong "production-ready" signal.
5. **Multilingual code-switching and safety or audit layer.** Pick one or both.
   - **(a)** A caller mixing Hindi and English (or Spanish and English) is understood mid-sentence. Show `language_code` per turn; the agent replies in an English voice, since Hindi TTS is "coming soon".
   - **(b)** A post-call pipeline:
     1. Fetch the session recording and timeline.
     2. Run async U3.5 Pro with speaker labels, entity detection and PII text and audio redaction.
     3. Have the LLM Gateway generate a `json_schema` structured QA or incident report.
     4. Deliver it through an HMAC-verified `session.completed` or `call.ended` webhook.

   This shows the whole platform, not just one API.

**Practical demo tips:**
- Ship as a **real phone number** through Twilio SIP (a single `connect.py`) as well as a browser.
- Include an entity-accuracy scoreboard.
- Keep AssemblyAI in the audio path. Don't put a third-party STT in front.
- Use Claude or another model through `llm-gateway.assemblyai.com` so even the LLM bill runs through AssemblyAI.
- The previous (2025) AssemblyAI and DEV challenge winners were judged on "creativity and technical skill", and the winners highlighted latency, domain expertise and business automation.

### 6.3 Gotchas
- **Audio format:**
  - Voice Agent input is **base64 JSON at 24 kHz PCM16**, not binary frames.
  - Streaming STT uses **binary frames** of 50–1000 ms, 16 kHz recommended.
- **Auth header:**
  - Voice Agent uses `Bearer <key>`.
  - Streaming uses the raw key; the docs say "without `Bearer`".
- **Billing:**
  - Always send `session.end` or `Terminate`. Idle time and the 30 s grace window are billed.
  - Sessions auto-close at 3 h and are billed in full.
- **Echo:** terminal demos without echo cancellation make the agent interrupt itself. Use a browser or headphones.
- **Immutable fields:** voice, greeting and output format can't change mid-call.
- **LLM fallbacks:** only one `llm` entry is allowed, so there are no fallbacks.
- **Hold mode:** during a hold, live user transcripts pause and flush afterwards.
- **Keyterms hygiene:** keep the list short and specific. Too many or overly common keyterms cause over-correction and hallucination, per the docs.

---

## 7. Open items / unverified
- The public judging rubric for the Sept 2026 lablab hackathon. The page renders it client-side and I couldn't retrieve it.
- The identity of the managed LLM and the TTS engine. Whether BYO or Gateway LLM changes the $4.50/hr.
- The voice count: docs show 16, older marketing says 30+ or 34.
- U3.5 Pro language count: 18 in most pages, 19 including Catalan on the multilingual page.
- The U3.5 Pro streaming `vad_threshold` default: 0.2 or 0.3.
- Parallel tool calls in the Voice Agent API.
- Whether streaming PII redaction carries the +$0.08/hr charge.
- Whether the `voice-agent-api-twilio-example` README (`/v1/realtime`, voices ivy/claire/dawn) reflects the current API.
