"""Hands-free spoken debrief after a mock code, run on the AssemblyAI Voice Agent API.

After the code (never during it), the team leader talks with CodeLoop, which facilitates a
short structured debrief in the AHA Gather-Analyze-Summarize style. This is the one place
CodeLoop holds a genuine two-way conversation:

  - the agent hears the leader directly (a 1:1 conversation, not the room)
  - it calls tools: get_code_facts returns ready-to-speak sentences built deterministically
    from the Code Record (the model quotes, never computes); save_debrief_note records the
    team's own words; end_debrief closes with a summary
  - semantic turn-taking and barge-in let the leader interrupt at any time

Nothing here can change the clinical record: the debrief notes are appended to the audit
log as the team's statements, next to the facts they were drawn from.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

import websockets

from .aai.voice import AGENT_RATE, FRAME_BYTES, FRAME_MS, resample_16k_to_24k
from .config import Settings
from .engine.speech import say_duration, say_number
from .record import build_record
from .store import Store

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CodeLoop's debrief facilitator for a resuscitation team, speaking with
the team leader right after a mock code. Run a short structured debrief using the AHA
Gather-Analyze-Summarize model, in under five minutes.

Rules:
- Call get_code_facts once, at the start. Any fact about times, doses, counts or outcomes must
  be one of its "say" sentences, spoken word for word. Never invent, compute or round a fact.
- Ask one short question at a time, then wait. Keep every turn under two sentences.
- Gather: ask how the team felt the code went.
- Analyze: raise at most two points from the facts, most important first (a dose conflict, an
  order left unacknowledged, a missed time target), and ask what happened and what would help.
- Summarize: ask for one thing to keep doing and one thing to change.
- Whenever the leader states a lesson, an action item or a system problem, call
  save_debrief_note with their own words.
- Never give medical advice and never blame individuals; focus on team communication.
- When the summary is done, call end_debrief with a one-sentence summary, then thank the team."""

TOOLS = [
    {
        "type": "function",
        "name": "get_code_facts",
        "description": "Facts about this code as ready-to-speak sentences. Call once at the start of the debrief.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "save_debrief_note",
        "description": "Save a lesson, action item or system issue the team leader just stated, in their words.",
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["went_well", "to_change", "action_item", "system_issue"]},
                "note": {"type": "string", "description": "The leader's words, lightly trimmed."},
            },
            "required": ["kind", "note"],
        },
    },
    {
        "type": "function",
        "name": "end_debrief",
        "description": "Close the debrief once the summary is done.",
        "parameters": {
            "type": "object",
            "properties": {"summary": {"type": "string", "description": "One sentence."}},
            "required": ["summary"],
        },
    },
]

JsonSender = Callable[[dict], Awaitable[None]]
BytesSender = Callable[[bytes], Awaitable[None]]


def debrief_facts(record: dict) -> dict:
    """Deterministic, ready-to-speak facts for the debrief (spoken numbers rendered as words)."""
    say: list[str] = []
    s = record.get("summary") or {}
    if record.get("duration_s") is not None:
        outcome = {"rosc": "with return of circulation", "terminated": "with the resuscitation stopped"}.get(
            record["code"].get("outcome") or "", ""
        )
        say.append(f"The code lasted {say_duration(record['duration_s'])} {outcome}".strip() + ".")
    q = {m["key"]: m for m in record.get("quality") or []}
    if "time_to_first_shock" in q and q["time_to_first_shock"]["value"] is not None:
        m = q["time_to_first_shock"]
        verdict = "within" if m["status"] == "met" else "outside"
        say.append(f"The first shock came {say_duration(m['value'])} after the start, {verdict} the two-minute target.")
    if "time_to_first_epinephrine" in q and q["time_to_first_epinephrine"]["value"] is not None:
        say.append(f"The first epinephrine was given {say_duration(q['time_to_first_epinephrine']['value'])} in.")
    if "closed_loop_rate" in q:
        read_back, total = q["closed_loop_rate"]["display"].split(" of ")
        say.append(f"{say_number(int(read_back)).capitalize()} of {say_number(int(total))} orders were read back.")
    unack = [lp for lp in record.get("loops", []) if any(h["state"] == "UNACKNOWLEDGED" for h in lp["history"])]
    for lp in unack:
        say.append(f"The order for {_loop_words(lp)} went unacknowledged for more than ten seconds.")
    for lp in record.get("loops", []):
        conflict = next((h for h in lp["history"] if h["state"] == "CONFLICT"), None)
        if conflict:
            m = re.search(r"read back ([\d.]+) ≠ ordered ([\d.]+)", conflict.get("note", ""))
            detail = (
                f": ordered {say_number(float(m.group(2)))}, read back {say_number(float(m.group(1)))}" if m else ""
            )
            say.append(f"A read-back conflict was caught on {_loop_words(lp)}{detail}.")
    if "cpr_fraction" in q and q["cpr_fraction"]["value"] is not None:
        say.append(
            f"Compressions were running about {say_number(round(q['cpr_fraction']['value'] * 100))} percent "
            "of the time, estimated from spoken calls."
        )
    sl = record.get("second_listen") or {}
    if sl.get("status") == "done":
        c = sl["counts"]
        say.append(
            f"The second listen confirmed {say_number(c['confirmed'])} of {say_number(sl['live_events'])} "
            "events in the record."
        )
    if s.get("prompts_spoken"):
        say.append(f"CodeLoop spoke {say_number(int(s['prompts_spoken']))} times during the code.")
    return {"say": say}


def _loop_words(lp: dict) -> str:
    v = lp.get("ordered_value")
    if lp["action"] == "shock":
        return f"a {say_number(v)} joule shock" if v is not None else "a shock"
    unit = {"mg": "milligrams", "g": "grams", "mEq": "milliequivalents"}.get(lp.get("unit") or "", lp.get("unit") or "")
    if v == 1 and unit.endswith("s"):
        unit = unit[:-1]
    return (
        f"{(lp.get('drug') or 'a drug').replace('_', ' ')} {say_number(v)} {unit}".strip()
        if v is not None
        else (lp.get("drug") or "a drug")
    )


class DebriefSession:
    def __init__(
        self,
        code_id: str,
        settings: Settings,
        store: Store,
        send_json: JsonSender,
        send_bytes: BytesSender,
        connect: Callable[..., Any] = websockets.connect,
    ) -> None:
        self.code_id = code_id
        self.settings = settings
        self.store = store
        self.send_json = send_json
        self.send_bytes = send_bytes
        self._connect = connect
        self._ws: Any = None
        self._mic = bytearray()
        self._pending: dict[str, str] = {}
        self._tasks: list[asyncio.Task] = []
        self.ready = asyncio.Event()
        self.ended = asyncio.Event()
        self.facts: dict = {}

    async def start(self) -> None:
        record = await asyncio.to_thread(build_record, self.store, self.code_id)
        self.facts = debrief_facts(record)
        await asyncio.to_thread(self.store.append, self.code_id, "debrief_started", {"facts": self.facts["say"]})
        headers = {"Authorization": f"Bearer {self.settings.assemblyai_api_key.get_secret_value()}"}
        self._ws = await self._connect(
            self.settings.agent_url, additional_headers=headers, max_size=None, open_timeout=10
        )
        await self._ws.send(
            json.dumps(
                {
                    "type": "session.update",
                    "session": {
                        "system_prompt": SYSTEM_PROMPT,
                        "greeting": "Let's debrief that code. I'll keep it to a few minutes. How do you feel it went?",
                        "tools": TOOLS,
                        "input": {"format": {"encoding": "audio/pcm"}, "turn_detection": {"interrupt_response": True}},
                        "output": {"voice": self.settings.agent_voice},
                    },
                }
            )
        )
        self._tasks = [
            asyncio.create_task(self._receive(), name="debrief-receive"),
            asyncio.create_task(self._pump(), name="debrief-pump"),
        ]

    def feed_audio(self, pcm16k: bytes) -> None:
        self._mic += resample_16k_to_24k(pcm16k)
        if len(self._mic) > AGENT_RATE * 2 * 3:  # never queue more than 3 s
            del self._mic[: len(self._mic) - AGENT_RATE * 2 * 3]

    async def close(self) -> None:
        with contextlib.suppress(Exception):
            await self._ws.send(json.dumps({"type": "session.end"}))
        for t in self._tasks:
            t.cancel()
        with contextlib.suppress(Exception):
            await self._ws.close()

    async def _pump(self) -> None:
        await self.ready.wait()
        start = time.perf_counter()
        n = 0
        silence = b"\x00" * FRAME_BYTES
        while True:
            if len(self._mic) >= FRAME_BYTES:
                frame = bytes(self._mic[:FRAME_BYTES])
                del self._mic[:FRAME_BYTES]
            else:
                frame = silence
            await self._ws.send(json.dumps({"type": "input.audio", "audio": base64.b64encode(frame).decode()}))
            n += 1
            await asyncio.sleep(max(0.0, start + n * FRAME_MS / 1000 - time.perf_counter()))

    async def _receive(self) -> None:
        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                t = msg.get("type")
                if t == "session.ready":
                    self.ready.set()
                    await self.send_json({"type": "debrief_ready", "facts": self.facts["say"]})
                elif t == "reply.audio":
                    await self.send_bytes(b"\x02" + base64.b64decode(msg["data"]))
                elif t == "transcript.user":
                    await self.send_json({"type": "debrief_user", "text": msg.get("text", "")})
                elif t == "transcript.agent":
                    await self.send_json(
                        {
                            "type": "debrief_agent",
                            "text": msg.get("text", ""),
                            "interrupted": bool(msg.get("interrupted")),
                        }
                    )
                elif t == "reply.done" and msg.get("status") == "interrupted":
                    self._pending.clear()
                    await self.send_json({"type": "agent_interrupted", "line_id": "debrief"})
                elif t == "tool.call":
                    self._pending[msg["call_id"]] = json.dumps(
                        await self._tool(msg["name"], msg.get("arguments") or {})
                    )
                if t == "reply.done":
                    for call_id, result in list(self._pending.items()):
                        await self._ws.send(json.dumps({"type": "tool.result", "call_id": call_id, "result": result}))
                        del self._pending[call_id]
                elif t == "session.error":
                    await self.send_json({"type": "error", "message": f"Debrief voice: {msg.get('message')}"})
        except websockets.ConnectionClosed:
            pass
        finally:
            self.ended.set()

    async def _tool(self, name: str, args: dict) -> dict:
        if name == "get_code_facts":
            await self.send_json({"type": "debrief_tool", "name": name})
            return self.facts
        if name == "save_debrief_note":
            note = {"kind": str(args.get("kind", "to_change")), "note": str(args.get("note", ""))[:500]}
            await asyncio.to_thread(self.store.append, self.code_id, "debrief_note", note)
            await self.send_json({"type": "debrief_note", **note})
            return {"saved": True}
        if name == "end_debrief":
            summary = str(args.get("summary", ""))[:500]
            await asyncio.to_thread(self.store.append, self.code_id, "debrief_summary", {"summary": summary})
            await self.send_json({"type": "debrief_done", "summary": summary})
            return {"ok": True}
        return {"error": f"unknown tool {name}"}
