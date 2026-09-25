"""Append-only, hash-chained audit log of every code (SQLite).

Each entry stores the SHA-256 of (previous hash + canonical JSON of the entry), so any
edit, deletion or reordering of the record is detectable with `verify`. Corrections never
overwrite: they are new entries that reference what they correct.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS codes (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    mode TEXT NOT NULL,
    scenario TEXT,
    status TEXT NOT NULL,
    outcome TEXT,
    ended_at TEXT,
    summary TEXT
);
CREATE TABLE IF NOT EXISTS audit (
    code_id TEXT NOT NULL REFERENCES codes(id),
    seq INTEGER NOT NULL,
    at_wall TEXT NOT NULL,
    at_code_s REAL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    PRIMARY KEY (code_id, seq)
);
CREATE INDEX IF NOT EXISTS audit_kind ON audit(code_id, kind);
"""

GENESIS = "0" * 64


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def entry_hash(
    prev_hash: str, code_id: str, seq: int, at_wall: str, at_code_s: float | None, kind: str, payload: Any
) -> str:
    body = canonical(
        {"code_id": code_id, "seq": seq, "at_wall": at_wall, "at_code_s": at_code_s, "kind": kind, "payload": payload}
    )
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


@dataclass(frozen=True)
class Entry:
    code_id: str
    seq: int
    at_wall: str
    at_code_s: float | None
    kind: str
    payload: Any
    prev_hash: str
    hash: str


class Store:
    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(SCHEMA)
        self._lock = threading.Lock()
        self._heads: dict[str, tuple[int, str]] = {}

    # --------------------------------------------------------------- codes

    def create_code(self, code_id: str, mode: str, scenario: str | None) -> None:
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO codes(id, created_at, mode, scenario, status) VALUES (?,?,?,?,?)",
                (code_id, _now(), mode, scenario, "active"),
            )
        self._heads[code_id] = (0, GENESIS)

    def finish_code(self, code_id: str, status: str, outcome: str | None, summary: dict) -> None:
        with self._lock, self._db:
            self._db.execute(
                "UPDATE codes SET status=?, outcome=?, ended_at=?, summary=? WHERE id=?",
                (status, outcome, _now(), canonical(summary), code_id),
            )

    def get_code(self, code_id: str) -> dict | None:
        row = self._db.execute(
            "SELECT id, created_at, mode, scenario, status, outcome, ended_at, summary FROM codes WHERE id=?",
            (code_id,),
        ).fetchone()
        return self._code_row(row) if row else None

    def list_codes(self, limit: int = 50) -> list[dict]:
        rows = self._db.execute(
            "SELECT id, created_at, mode, scenario, status, outcome, ended_at, summary "
            "FROM codes ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._code_row(r) for r in rows]

    @staticmethod
    def _code_row(r: tuple) -> dict:
        return {
            "id": r[0],
            "created_at": r[1],
            "mode": r[2],
            "scenario": r[3],
            "status": r[4],
            "outcome": r[5],
            "ended_at": r[6],
            "summary": json.loads(r[7]) if r[7] else None,
        }

    # --------------------------------------------------------------- audit log

    def append(self, code_id: str, kind: str, payload: Any, at_code_s: float | None = None) -> Entry:
        with self._lock:
            seq, prev = self._head(code_id)
            seq += 1
            at_wall = _now()
            payload = json.loads(canonical(payload))
            h = entry_hash(prev, code_id, seq, at_wall, at_code_s, kind, payload)
            with self._db:
                self._db.execute(
                    "INSERT INTO audit(code_id, seq, at_wall, at_code_s, kind, payload, prev_hash, hash) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (code_id, seq, at_wall, at_code_s, kind, canonical(payload), prev, h),
                )
            self._heads[code_id] = (seq, h)
            return Entry(code_id, seq, at_wall, at_code_s, kind, payload, prev, h)

    async def append_async(self, code_id: str, kind: str, payload: Any, at_code_s: float | None = None) -> Entry:
        return await asyncio.to_thread(self.append, code_id, kind, payload, at_code_s)

    def entries(self, code_id: str, kinds: set[str] | None = None) -> list[Entry]:
        rows = self._db.execute(
            "SELECT code_id, seq, at_wall, at_code_s, kind, payload, prev_hash, hash FROM audit "
            "WHERE code_id=? ORDER BY seq",
            (code_id,),
        ).fetchall()
        out = [Entry(r[0], r[1], r[2], r[3], r[4], json.loads(r[5]), r[6], r[7]) for r in rows]
        return [e for e in out if kinds is None or e.kind in kinds]

    def verify(self, code_id: str) -> tuple[bool, int | None]:
        """Recompute the chain. Returns (ok, first bad seq)."""
        prev = GENESIS
        for e in self.entries(code_id):
            if (
                e.prev_hash != prev
                or entry_hash(prev, e.code_id, e.seq, e.at_wall, e.at_code_s, e.kind, e.payload) != e.hash
            ):
                return False, e.seq
            prev = e.hash
        return True, None

    def head_hash(self, code_id: str) -> str:
        return self._head(code_id)[1]

    def _head(self, code_id: str) -> tuple[int, str]:
        if code_id not in self._heads:
            row = self._db.execute(
                "SELECT seq, hash FROM audit WHERE code_id=? ORDER BY seq DESC LIMIT 1", (code_id,)
            ).fetchone()
            self._heads[code_id] = (row[0], row[1]) if row else (0, GENESIS)
        return self._heads[code_id]

    def close(self) -> None:
        self._db.close()
