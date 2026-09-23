from __future__ import annotations

import datetime as dt
import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote

import httpx

from wir import config
from wir.cache import Cache

REST_BASE = "https://wikimedia.org/api/rest_v1/metrics"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
DAY = 24 * 3600
TTL_RECENT = DAY
TTL_METADATA = 7 * DAY
TTL_NOT_FOUND = DAY
FINAL_AFTER_DAYS = 3
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_BACKOFF_SECONDS = 60


class WikimediaError(RuntimeError):
    pass


class OfflineCacheMiss(WikimediaError):
    pass


@dataclass
class RequestStats:
    network: int = 0
    cached: int = 0
    retries: int = 0

    def summary(self) -> str:
        return f"{self.network} network, {self.cached} from cache, {self.retries} retries"


def encode_title(title: str) -> str:
    return quote(title.strip().replace(" ", "_"), safe="")


def ymd(day: dt.date) -> str:
    return day.strftime("%Y%m%d")


class WikimediaClient:
    def __init__(
        self,
        cache: Cache,
        *,
        transport: httpx.BaseTransport | None = None,
        offline: bool | None = None,
        max_retries: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.cache = cache
        self.offline = config.offline() if offline is None else offline
        self.max_retries = max_retries
        self.sleep = sleep
        self.stats = RequestStats()
        self._http = httpx.Client(
            headers={"User-Agent": config.user_agent(), "Accept": "application/json"},
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            transport=transport,
        )

    def get_json(self, url: str, params: dict | None = None, *, ttl: float | None) -> dict | None:
        """Cached GET; returns None on 404."""
        key = str(httpx.URL(url, params=params))
        cached = self.cache.get(key)
        if cached is None and self.offline:
            cached = self.cache.get(key, allow_expired=True)
            if cached is None:
                raise OfflineCacheMiss(
                    f"Offline mode (WIR_OFFLINE) is on and this request is not cached: {key}. "
                    "Unset WIR_OFFLINE to fetch it, or narrow the request to cached data."
                )
        if cached is not None:
            self.stats.cached += 1
            return None if cached.status == 404 else cached.body

        response = self._request(key)
        if response.status_code == 404:
            self.cache.put(key, 404, None, ttl=TTL_NOT_FOUND)
            return None
        body = response.json()
        self.cache.put(key, 200, body, ttl=ttl)
        return body

    def _request(self, url: str) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            self.stats.network += 1
            try:
                response = self._http.get(url)
            except httpx.TransportError as exc:
                if attempt == self.max_retries:
                    raise WikimediaError(
                        f"Network error talking to Wikimedia ({exc.__class__.__name__}: {exc}). "
                        "Check the internet connection; cached data still works with WIR_OFFLINE=1."
                    ) from exc
                self._backoff(attempt, None)
                continue
            if response.status_code in RETRY_STATUSES and attempt < self.max_retries:
                self._backoff(attempt, response.headers.get("Retry-After"))
                continue
            if response.status_code in (200, 404):
                return response
            raise WikimediaError(
                f"Wikimedia API returned HTTP {response.status_code} for {url}: "
                f"{_error_detail(response)}"
            )
        raise AssertionError("unreachable")

    def _backoff(self, attempt: int, retry_after: str | None) -> None:
        self.stats.retries += 1
        try:
            delay = float(retry_after) if retry_after else 2.0**attempt
        except ValueError:
            delay = 2.0**attempt
        self.sleep(min(delay, MAX_BACKOFF_SECONDS))

    def _pageviews_ttl(self, end: dt.date) -> float | None:
        final = end <= config.today() - dt.timedelta(days=FINAL_AFTER_DAYS)
        return None if final else TTL_RECENT

    def _year_chunks(self, start: dt.date, end: dt.date) -> list[tuple[dt.date, dt.date]]:
        """Whole calendar years where possible, so any window reuses the same cached requests."""
        final = config.today() - dt.timedelta(days=FINAL_AFTER_DAYS)
        chunks = []
        for year in range(start.year, end.year + 1):
            year_end = dt.date(year, 12, 31)
            chunks.append((dt.date(year, 1, 1), year_end if year_end <= final else end))
        return chunks

    def _pageviews(self, path: str, start: dt.date, end: dt.date) -> list[tuple[dt.date, int]]:
        rows = []
        for chunk_start, chunk_end in self._year_chunks(start, end):
            url = f"{REST_BASE}/pageviews/{path}/{ymd(chunk_start)}/{ymd(chunk_end)}"
            body = self.get_json(url, ttl=self._pageviews_ttl(chunk_end))
            rows += [row for row in _parse_items(body, "views") if start <= row[0] <= end]
        return rows

    def per_article(
        self,
        project: str,
        title: str,
        start: dt.date,
        end: dt.date,
        *,
        granularity: str = "daily",
        access: str = "all-access",
        agent: str = "user",
    ) -> list[tuple[dt.date, int]]:
        path = f"per-article/{project}/{access}/{agent}/{encode_title(title)}/{granularity}"
        return self._pageviews(path, start, end)

    def aggregate(
        self,
        project: str,
        start: dt.date,
        end: dt.date,
        *,
        granularity: str = "daily",
        access: str = "all-access",
        agent: str = "user",
    ) -> list[tuple[dt.date, int]]:
        return self._pageviews(f"aggregate/{project}/{access}/{agent}/{granularity}", start, end)

    def unique_devices(
        self, project: str, start: dt.date, end: dt.date, *, access_site: str = "all-sites"
    ) -> list[tuple[dt.date, int]]:
        url = f"{REST_BASE}/unique-devices/{project}/{access_site}/monthly/{ymd(start)}/{ymd(end)}"
        return _parse_items(self.get_json(url, ttl=self._pageviews_ttl(end)), "devices")

    def top_by_country(self, project: str, year: int, month: int) -> list[dict]:
        url = f"{REST_BASE}/pageviews/top-by-country/{project}/all-access/{year}/{month:02d}"
        body = self.get_json(url, ttl=None)
        if not body or not body.get("items"):
            return []
        return body["items"][0].get("countries", [])

    def action(self, lang: str, ttl: float | None = TTL_METADATA, **params) -> dict:
        return self._action(f"https://{lang}.wikipedia.org/w/api.php", ttl, params)

    def wikidata(self, ttl: float | None = TTL_METADATA, **params) -> dict:
        return self._action(WIKIDATA_API, ttl, params)

    def _action(self, endpoint: str, ttl: float | None, params: dict) -> dict:
        body = self.get_json(endpoint, {**params, "format": "json", "formatversion": "2"}, ttl=ttl)
        if body is None:
            raise WikimediaError(f"{endpoint} returned 404; check the language code.")
        if "error" in body:
            err = body["error"]
            raise WikimediaError(f"{endpoint} error {err.get('code')}: {err.get('info')}")
        return body

    def ping(self, url: str) -> int:
        response = self._http.get(url)
        response.raise_for_status()
        return response.status_code

    def close(self) -> None:
        self._http.close()


def _parse_items(body: dict | None, field: str) -> list[tuple[dt.date, int]]:
    if not body:
        return []
    rows = []
    for item in body.get("items", []):
        stamp = item["timestamp"]
        rows.append((dt.date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8])), int(item[field])))
    return rows


def _error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:300]
    return str(body.get("detail") or body.get("title") or body)[:300]
