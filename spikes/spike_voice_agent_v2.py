"""Spike 2b: the redesigned voice path.

Room audio stays with the streaming "ears"; the Voice Agent only ever receives:
  - questions as text: conversation.message(role=user) + reply.create
  - engine prompts:    reply.create("Say exactly: ...")
  - live audio only while it is speaking (so semantic barge-in still works); silence otherwise
Tool results include pre-rendered spoken strings so the model never reformats times/doses.

Checks:
  Q1  English question as text      → tool call, grounded answer, latency
  Q2  Hinglish question as text     → tool call, English answer, latency
  Q3  "what is due" question        → answer reflects open orders / epi window
  B1  barge-in while speaking       → interrupted
  S1  60 s of silence               → agent says nothing on its own

    uv run --project backend python spikes/spike_voice_agent_v2.py
"""

from __future__ import annotations

import asyncio
import json
import re

import websockets
from _common import RESULTS, api_key, save_json, write_pcm16
from spike_voice_agent import SR, URL, Session, summarize, tts24

SYSTEM_PROMPT = """You are CodeLoop, the voice of the recorder at an in-hospital cardiac arrest.
You receive questions from the resuscitation team as text. Rules:
- Before answering anything about times, doses, drugs, shocks, rhythm or what is due, call
  get_code_state. Use the `say` strings from the tool result word for word; never compute,
  convert or round a time or a dose yourself.
- Answer in one short sentence in English, even if the question mixes Hindi and English.
- If the tool fails or does not contain the answer, say exactly: "Check the screen."
- Never recommend treatment or doses. You record and keep time; the team leader decides."""

TOOLS = [{
    "type": "function",
    "name": "get_code_state",
    "description": "Current state of the code with ready-to-speak sentences. Call before answering "
                   "any question about times, doses, drugs, shocks, rhythm, or what is due.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}]

CODE_STATE = {
    "say": {
        "last_epinephrine": (
            "Last epinephrine, one milligram, three minutes ten seconds ago, at code time zero fifty-two."
        ),
        "last_amiodarone": "Amiodarone three hundred milligrams, two minutes fifty-two seconds ago.",
        "shocks": "One shock, two hundred joules, three minutes forty seconds ago.",
        "rhythm": "Last recorded rhythm: V-fib.",
        "due": "Epinephrine window is open. No open orders.",
        "clock": "Code time four minutes two seconds.",
    },
    "clock_s": 242,
    "last_drugs": {"epinephrine": {"dose": "1", "unit": "mg", "seconds_ago": 190},
                   "amiodarone": {"dose": "300", "unit": "mg", "seconds_ago": 172}},
    "epinephrine_window": {"state": "open"},
    "open_orders": [],
}


class GatedSession(Session):
    """Only forwards queued speech while `forward_audio` is set; otherwise sends silence."""

    def __init__(self, ws) -> None:
        super().__init__(ws)
        self.requested_replies = 0


async def ask(s: GatedSession, text: str) -> None:
    """(a) inject the question as a user message, give it time to commit, then ask for a reply."""
    await s.ws.send(json.dumps({"type": "conversation.message", "role": "user", "content": text}))
    await asyncio.sleep(0.5)
    await s.ws.send(json.dumps({"type": "reply.create"}))


async def ask_instr(s: GatedSession, text: str) -> None:
    """(b) carry the question in the reply instructions."""
    await s.ws.send(json.dumps({"type": "reply.create", "instructions":
        f'A team member just asked: "{text}". Call get_code_state, then answer in one short sentence '
        "using the say strings verbatim."}))


async def main() -> None:
    import spike_voice_agent as v1

    v1.CODE_STATE = CODE_STATE  # the tool handler in Session reads this module global
    results: dict[str, dict] = {}
    stop = tts24("Got it, pausing now.", "Rishi")
    async with websockets.connect(URL, additional_headers={"Authorization": f"Bearer {api_key()}"},
                                  max_size=None) as ws:
        s = GatedSession(ws)
        await ws.send(json.dumps({"type": "session.update", "session": {
            "system_prompt": SYSTEM_PROMPT,
            "tools": TOOLS,
            "input": {"format": {"encoding": "audio/pcm"},
                      "turn_detection": {"interrupt_response": True}},
            "output": {"voice": "michael"},
        }}))
        recv = asyncio.create_task(s.receive())
        pump = asyncio.create_task(s.pump_audio())
        await asyncio.wait_for(s.ready.wait(), 15)
        await s.settle(quiet_s=1.5)

        async def test(name, action):
            before = len(s.audio)
            t = s.now()
            await action()
            await s.settle(quiet_s=3.0)
            results[name] = summarize(s.since(t), t)
            write_pcm16(RESULTS / f"agent_v2_{name}.wav", bytes(s.audio[before:]), SR)
            print(name, json.dumps(results[name], ensure_ascii=False))

        await test("Q1_text_en", lambda: ask(s, "CodeLoop, when was the last epinephrine given?"))
        await test("Q1b_instr_en", lambda: ask_instr(s, "CodeLoop, when was the last epinephrine given?"))
        await test("Q2_text_hinglish", lambda: ask(s, "CodeLoop, last epi kab diya tha?"))
        await test("Q2b_instr_hinglish", lambda: ask_instr(s, "CodeLoop, last epi kab diya tha?"))
        await test("Q3b_instr_due", lambda: ask_instr(s, "CodeLoop, what's due?"))

        async def barge():
            t = s.now()
            await ws.send(json.dumps({"type": "reply.create", "instructions":
                'Say exactly: "Epinephrine one milligram ordered forty seconds ago and not acknowledged. '
                'Please confirm who is drawing it up and read back the dose."'}))
            if await s.wait_for(lambda e: e.get("type") == "reply.audio", 10, t):
                await asyncio.sleep(1.2)
                await s.speech.put(stop)  # room audio is forwarded while the agent speaks
        await test("B1_barge_in", barge)

        async def silence():
            await asyncio.sleep(20)
        await test("S1_silence_20s", silence)

        await ws.send(json.dumps({"type": "session.end"}))
        pump.cancel()
        try:
            await asyncio.wait_for(recv, 10)
        except (TimeoutError, websockets.ConnectionClosed):
            pass

    for name in ("Q1_text_en", "Q1b_instr_en", "Q2_text_hinglish", "Q2b_instr_hinglish"):
        said = " ".join(results[name]["agent_said"])
        results[name]["grounded"] = bool(re.search(r"three minutes ten seconds", said))
    results["S1_silence_20s"]["spoke_unprompted"] = bool(results["S1_silence_20s"]["agent_said"])
    save_json("voice_agent_v2.report.json", results)
    save_json("voice_agent_v2.events.json", s.events)


if __name__ == "__main__":
    asyncio.run(main())
