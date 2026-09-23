import datetime as dt

import pytest

from wir import config, languages, periods, series
from wir.cache import Cache
from wir.resolve import resolve_topic
from wir.wikimedia import REST_BASE, WikimediaClient, encode_title, ymd

pytestmark = pytest.mark.live


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WIR_TODAY", dt.date.today().isoformat())
    live = WikimediaClient(Cache(tmp_path / "live.sqlite"))
    yield live
    live.close()


def test_daily_sums_match_monthly_endpoint(client):
    period = periods.parse("12m", config.today())
    project, title = "uk.wikipedia", "Астрономія"
    ours = series.month_rows(
        series.monthly(
            series.daily(
                client.per_article(project, title, period.start, period.end),
                period.start,
                period.end,
            )
        )
    )
    url = (
        f"{REST_BASE}/pageviews/per-article/{project}/all-access/user/{encode_title(title)}"
        f"/monthly/{ymd(period.start)}/{ymd(period.end)}"
    )
    body = client.get_json(url, ttl=0)
    theirs = [[f"{i['timestamp'][:4]}-{i['timestamp'][4:6]}", i["views"]] for i in body["items"]]
    assert ours == theirs


def test_resolve_live(client):
    result = resolve_topic(client, "astronomy", "en", languages.parse_list("uk,pl"))
    assert result.concept.qid == "Q333"
