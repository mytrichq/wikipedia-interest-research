"""Recorded API responses. Re-record with: WIR_RECORD=1 uv run pytest tests/test_resolve.py"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

from wir import config

CASSETTES = Path(__file__).parent / "fixtures" / "cassettes"


class CassetteTransport(httpx.BaseTransport):
    def __init__(self, name: str):
        self.path = CASSETTES / f"{name}.jsonl"
        self.record = os.environ.get("WIR_RECORD") == "1"
        self.entries: dict[str, dict] = {}
        if self.path.exists() and not self.record:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                entry = json.loads(line)
                self.entries[entry["url"]] = entry
        self._live = httpx.HTTPTransport() if self.record else None
        self._recorded: list[dict] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if self._live:
            request.headers["User-Agent"] = config.user_agent()
            response = self._live.handle_request(request)
            response.read()
            body = response.json() if response.status_code in (200, 404) else None
            self._recorded.append({"url": url, "status": response.status_code, "body": body})
            self._save()
            return httpx.Response(response.status_code, json=body)
        if url not in self.entries:
            raise AssertionError(f"URL not in cassette {self.path.name}: {url}")
        entry = self.entries[url]
        return httpx.Response(entry["status"], json=entry["body"])

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(e, ensure_ascii=False) for e in self._recorded]
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
