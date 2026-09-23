from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS responses (
    url        TEXT PRIMARY KEY,
    status     INTEGER NOT NULL,
    body       TEXT NOT NULL,
    fetched_at REAL NOT NULL,
    expires_at REAL
)
"""


@dataclass(frozen=True)
class CachedResponse:
    status: int
    body: dict | list | None
    fetched_at: float


class Cache:
    """Raw API responses keyed by URL; ttl=None means the entry never expires."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def get(self, url: str, *, allow_expired: bool = False) -> CachedResponse | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT status, body, fetched_at, expires_at FROM responses WHERE url = ?", (url,)
            ).fetchone()
        if row is None:
            return None
        status, body, fetched_at, expires_at = row
        if not allow_expired and expires_at is not None and expires_at < time.time():
            return None
        return CachedResponse(status=status, body=json.loads(body), fetched_at=fetched_at)

    def put(self, url: str, status: int, body: dict | list | None, ttl: float | None) -> None:
        now = time.time()
        expires_at = None if ttl is None else now + ttl
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO responses (url, status, body, fetched_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (url, status, json.dumps(body, ensure_ascii=False), now, expires_at),
            )
            self._conn.commit()

    def stats(self) -> dict:
        with self._lock:
            count, size = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(LENGTH(body)), 0) FROM responses"
            ).fetchone()
        return {"path": str(self.path), "entries": count, "megabytes": round(size / 1e6, 2)}

    def close(self) -> None:
        with self._lock:
            self._conn.close()
