"""AssemblyAI async (pre-recorded) transcription of a finished code's full recording.

Used for the "second listen": after the code, the whole room recording is transcribed again
with Universal-3.5 Pro, which sees the entire audio at once (not a real-time stream), with
Medical Mode, speaker labels and the same ACLS keyterms.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from ..config import Settings
from ..domain.models import Utterance, Word

API = "https://api.assemblyai.com/v2"


class AsyncTranscriptionError(RuntimeError):
    pass


async def transcribe_file(
    settings: Settings,
    wav: Path,
    keyterms: list[str],
    *,
    poll_s: float = 3.0,
    timeout_s: float = 900.0,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """Upload a WAV and return the completed transcript JSON."""
    headers = {"Authorization": settings.assemblyai_api_key.get_secret_value()}
    own = client is None
    client = client or httpx.AsyncClient(timeout=120)
    try:
        up = await client.post(f"{API}/upload", headers=headers, content=await asyncio.to_thread(wav.read_bytes))
        up.raise_for_status()
        body = {
            "audio_url": up.json()["upload_url"],
            "speech_models": ["universal-3-5-pro"],
            "speaker_labels": True,
            "language_detection": True,
            "domain": "medical-v1",
            "keyterms_prompt": keyterms[:100],
        }
        r = await client.post(f"{API}/transcript", headers=headers, json=body)
        if r.status_code >= 400:
            raise AsyncTranscriptionError(f"{r.status_code}: {r.text[:300]}")
        tid = r.json()["id"]
        waited = 0.0
        while waited < timeout_s:
            t = (await client.get(f"{API}/transcript/{tid}", headers=headers)).json()
            if t["status"] == "completed":
                return t
            if t["status"] == "error":
                raise AsyncTranscriptionError(t.get("error", "transcription failed"))
            await asyncio.sleep(poll_s)
            waited += poll_s
        raise AsyncTranscriptionError("timed out waiting for the transcript")
    finally:
        if own:
            await client.aclose()


def utterances_from_transcript(t: dict, id_prefix: str = "s") -> list[Utterance]:
    """AssemblyAI async `utterances` (one per speaker turn) → CodeLoop utterances."""
    out: list[Utterance] = []
    for i, u in enumerate(t.get("utterances") or []):
        words = [
            Word(
                text=w["text"], start_ms=int(w["start"]), end_ms=int(w["end"]), confidence=float(w.get("confidence", 0))
            )
            for w in u.get("words") or []
        ]
        out.append(
            Utterance(
                id=f"{id_prefix}{i}",
                turn_order=i,
                text=u.get("text", ""),
                start_s=u["start"] / 1000,
                end_s=u["end"] / 1000,
                speaker=u.get("speaker"),
                language=t.get("language_code"),
                words=words,
            )
        )
    return out
