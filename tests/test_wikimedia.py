import datetime as dt

import httpx
import pytest

from wir.cache import Cache
from wir.wikimedia import (
    OfflineCacheMiss,
    WikimediaClient,
    WikimediaError,
    encode_title,
)

START, END = dt.date(2026, 1, 1), dt.date(2026, 1, 31)
ITEMS = {
    "items": [{"timestamp": "2026010100", "views": 5}, {"timestamp": "2026010300", "views": 7}]
}


def make_client(tmp_path, handler, **kwargs):
    sleeps = []
    client = WikimediaClient(
        Cache(tmp_path / "c.sqlite"),
        transport=httpx.MockTransport(handler),
        sleep=sleeps.append,
        **kwargs,
    )
    return client, sleeps


@pytest.mark.parametrize(
    ("title", "encoded"),
    [
        ("Albert Einstein", "Albert_Einstein"),
        ("AC/DC", "AC%2FDC"),
        ("Астрономія", "%D0%90%D1%81%D1%82%D1%80%D0%BE%D0%BD%D0%BE%D0%BC%D1%96%D1%8F"),
        ("Přerušovaný půst", "P%C5%99eru%C5%A1ovan%C3%BD_p%C5%AFst"),
    ],
)
def test_titles_are_encoded_for_url_paths(title, encoded):
    assert encode_title(title) == encoded


def test_per_article_request_and_parsing(tmp_path):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=ITEMS)

    client, _ = make_client(tmp_path, handler)
    rows = client.per_article("uk.wikipedia", "AC/DC", START, END)
    assert rows == [(dt.date(2026, 1, 1), 5), (dt.date(2026, 1, 3), 7)]
    assert (
        seen[0]
        .url.raw_path.decode()
        .endswith("/per-article/uk.wikipedia/all-access/user/AC%2FDC/daily/20260101/20260131")
    )
    assert "github.com/mytrichq" in seen[0].headers["User-Agent"]


def test_second_request_is_served_from_cache(tmp_path):
    client, _ = make_client(tmp_path, lambda r: httpx.Response(200, json=ITEMS))
    client.per_article("uk.wikipedia", "X", START, END)
    client.per_article("uk.wikipedia", "X", START, END)
    assert (client.stats.network, client.stats.cached) == (1, 1)


def test_rate_limit_waits_for_retry_after(tmp_path):
    responses = [httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200, json=ITEMS)]
    client, sleeps = make_client(tmp_path, lambda r: responses.pop(0))
    assert len(client.per_article("uk.wikipedia", "X", START, END)) == 2
    assert sleeps == [7.0]
    assert client.stats.retries == 1


def test_persistent_server_errors_give_up_with_a_clear_message(tmp_path):
    client, sleeps = make_client(tmp_path, lambda r: httpx.Response(503), max_retries=2)
    with pytest.raises(WikimediaError, match="HTTP 503"):
        client.per_article("uk.wikipedia", "X", START, END)
    assert sleeps == [1.0, 2.0]


def test_network_failure_suggests_offline_mode(tmp_path):
    def handler(request):
        raise httpx.ConnectError("no route")

    client, _ = make_client(tmp_path, handler, max_retries=1)
    with pytest.raises(WikimediaError, match="WIR_OFFLINE=1"):
        client.per_article("uk.wikipedia", "X", START, END)


def test_404_means_no_data_and_is_cached(tmp_path):
    client, _ = make_client(tmp_path, lambda r: httpx.Response(404, json={"title": "Not Found"}))
    assert client.per_article("uk.wikipedia", "Nope", START, END) == []
    assert client.per_article("uk.wikipedia", "Nope", START, END) == []
    assert client.stats.network == 1


def test_bad_request_reports_api_detail(tmp_path):
    body = {"title": "Bad Request", "detail": "Invalid granularity"}
    client, _ = make_client(tmp_path, lambda r: httpx.Response(400, json=body))
    with pytest.raises(WikimediaError, match="Invalid granularity"):
        client.per_article("uk.wikipedia", "X", START, END, granularity="hourly")


def test_offline_mode_uses_cache_and_explains_misses(tmp_path):
    online, _ = make_client(tmp_path, lambda r: httpx.Response(200, json=ITEMS))
    online.per_article("uk.wikipedia", "X", START, END)

    def fail(request):
        raise AssertionError("offline mode must not use the network")

    offline, _ = make_client(tmp_path, fail, offline=True)
    assert len(offline.per_article("uk.wikipedia", "X", START, END)) == 2
    with pytest.raises(OfflineCacheMiss, match="Unset WIR_OFFLINE"):
        offline.per_article("uk.wikipedia", "Other", START, END)


def test_finished_periods_never_expire_recent_ones_do(tmp_path):
    client, _ = make_client(tmp_path, lambda r: httpx.Response(200, json=ITEMS))
    assert client._pageviews_ttl(dt.date(2026, 8, 31)) is None
    assert client._pageviews_ttl(dt.date(2026, 9, 22)) is not None


def test_action_api_errors_are_raised(tmp_path):
    body = {"error": {"code": "badvalue", "info": "Unrecognized value"}}
    client, _ = make_client(tmp_path, lambda r: httpx.Response(200, json=body))
    with pytest.raises(WikimediaError, match="badvalue"):
        client.action("uk", action="query", list="nonsense")
