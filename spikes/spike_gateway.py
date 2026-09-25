"""Spike 3: structured event extraction through AssemblyAI's LLM Gateway.

Sends each gold line of a scenario (as a transcript turn) to several fast models with a strict
json_schema, then measures latency, schema validity, whether every event quotes the
transcript verbatim, and event-level agreement with the gold labels.

    uv run --project backend python spikes/spike_gateway.py
    uv run --project backend python spikes/spike_gateway.py --models claude-haiku-4-5-20251001,gemini-3.5-flash-lite
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx
from _common import REPO, api_key, pct, save_json

URL = "https://llm-gateway.assemblyai.com/v1/chat/completions"
DEFAULT_MODELS = ["claude-haiku-4-5-20251001", "gemini-3.5-flash-lite", "gpt-5-nano",
                  "qwen3.5-4b-32k-fast"]

SYSTEM = """You extract resuscitation events from ONE transcribed utterance spoken during an
in-hospital cardiac arrest. The utterance may mix Hindi and English.
Return every event the utterance states. Rules:
- kind: order (someone tells another to give a drug or deliver a shock), ack (someone repeats
  an order back or says they are doing it), done (a drug is in / a shock was delivered),
  rhythm (a rhythm is named), cpr_start, cpr_pause, cpr_resume, rhythm_check, rosc, cancel,
  role (someone assigns or states a team role), question (someone asks CodeLoop something).
- quote: the exact substring of the utterance that supports the event, copied verbatim.
- Use null for fields that do not apply. Doses in the unit spoken (mg); energy in joules.
- Drugs: use generic names (epi -> epinephrine, amio -> amiodarone).
- Do not infer anything that was not said. If nothing applies, return an empty list."""

EVENT = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "action", "drug", "dose", "unit", "energy_j", "rhythm", "role",
                 "name", "quote"],
    "properties": {
        "kind": {"type": "string", "enum": ["order", "ack", "done", "rhythm", "cpr_start",
                                            "cpr_pause", "cpr_resume", "rhythm_check", "rosc",
                                            "cancel", "role", "question"]},
        "action": {"type": ["string", "null"], "enum": ["drug", "shock", None]},
        "drug": {"type": ["string", "null"]},
        "dose": {"type": ["number", "null"]},
        "unit": {"type": ["string", "null"]},
        "energy_j": {"type": ["number", "null"]},
        "rhythm": {"type": ["string", "null"], "enum": ["VF", "PVT", "PEA", "ASYSTOLE",
                                                        "SINUS", None]},
        "role": {"type": ["string", "null"], "enum": ["leader", "meds", "compressor",
                                                      "airway", "recorder", None]},
        "name": {"type": ["string", "null"]},
        "quote": {"type": "string"},
    },
}
SCHEMA = {
    "name": "code_events",
    "strict": True,
    "schema": {"type": "object", "additionalProperties": False, "required": ["events"],
               "properties": {"events": {"type": "array", "items": EVENT}}},
}


def key_of(ev: dict) -> tuple:
    return (ev.get("kind"), ev.get("drug"), ev.get("dose"), ev.get("energy_j"), ev.get("rhythm"))


async def extract(client: httpx.AsyncClient, model: str, text: str) -> dict:
    body = {"model": model, "temperature": 0, "max_tokens": 600,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": text}],
            "response_format": {"type": "json_schema", "json_schema": SCHEMA}}
    t = time.perf_counter()
    try:
        r = await client.post(URL, json=body, timeout=30)
        ms = (time.perf_counter() - t) * 1000
        if r.status_code != 200:
            return {"ok": False, "ms": ms, "error": f"{r.status_code} {r.text[:200]}"}
        content = r.json()["choices"][0]["message"]["content"]
        return {"ok": True, "ms": ms, "events": json.loads(content)["events"]}
    except Exception as e:
        return {"ok": False, "ms": (time.perf_counter() - t) * 1000, "error": repr(e)}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--gold", type=Path, nargs="*", default=[
        REPO / "eval/audio/vf_arrest_demo.none.gold.json",
        REPO / "eval/audio/asystole_hinglish.none.gold.json"])
    args = ap.parse_args()
    lines = [ln for g in args.gold for ln in json.loads(g.read_text())["lines"]]
    report: dict[str, dict] = {}
    async with httpx.AsyncClient(headers={"Authorization": api_key()}) as client:
        for model in args.models.split(","):
            res = []
            for ln in lines:  # sequential: realistic per-turn latency, no burst throttling
                res.append((ln, await extract(client, model, ln["say"])))
            lat = [r["ms"] for _, r in res if r["ok"]]
            tp = fp = fn = bad_quotes = 0
            for ln, r in res:
                if not r["ok"]:
                    fn += len(ln.get("gold", []))
                    continue
                gold = [key_of(e) for e in ln.get("gold", []) if e["kind"] != "role"]
                got = [key_of(e) for e in r["events"] if e["kind"] != "role"]
                bad_quotes += sum(1 for e in r["events"] if e["quote"] not in ln["say"])
                remaining = list(gold)
                for g in got:
                    if g in remaining:
                        remaining.remove(g)
                        tp += 1
                    else:
                        fp += 1
                fn += len(remaining)
            report[model] = {
                "calls": len(res),
                "failures": sum(1 for _, r in res if not r["ok"]),
                "first_error": next((r["error"] for _, r in res if not r["ok"]), None),
                "latency_ms": {"p50": pct(lat, 0.5), "p90": pct(lat, 0.9)},
                "precision": round(tp / max(1, tp + fp), 3),
                "recall": round(tp / max(1, tp + fn), 3),
                "non_verbatim_quotes": bad_quotes,
                "mistakes": [{"say": ln["say"], "gold": [key_of(e) for e in ln.get("gold", [])],
                              "got": [key_of(e) for e in r.get("events", [])]}
                             for ln, r in res if r["ok"] and sorted(
                                 key_of(e) for e in ln.get("gold", []) if e["kind"] != "role") != sorted(
                                 key_of(e) for e in r["events"] if e["kind"] != "role")][:8],
            }
            print(model, json.dumps({k: v for k, v in report[model].items() if k != "mistakes"}))
    save_json("gateway.report.json", report)


if __name__ == "__main__":
    asyncio.run(main())
