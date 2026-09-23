from __future__ import annotations

import pytest

from tests.cassette import CassetteTransport
from wir.cache import Cache
from wir.wikimedia import WikimediaClient

TODAY = "2026-09-23"


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("WIR_TODAY", TODAY)
    monkeypatch.setenv("WIR_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("WIR_OFFLINE", raising=False)
    monkeypatch.delenv("WIR_CONTACT", raising=False)


@pytest.fixture
def cassette_client(tmp_path):
    clients = []

    def make(name: str) -> WikimediaClient:
        client = WikimediaClient(
            Cache(tmp_path / "cache.sqlite"),
            transport=CassetteTransport(name),
            sleep=lambda _: None,
        )
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.close()
